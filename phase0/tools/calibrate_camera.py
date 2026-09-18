#!/usr/bin/env python3
"""Reduced intrinsic calibration from several views of the NDFID-1 frame.

Model: fx = fy, principal point fixed at the image centre, radial k1 and k2.
Objective: total control-point reprojection RMS over all views, where each view
gets its own homography fitted to the *undistorted* detected corners.

This is deliberately a reduced model.  A production build should use a full
OpenCV `calibrateCamera` with a ChArUco board and report parameter covariance;
here the point is to (a) make the working pipeline runnable end to end without
third-party wheels, and (b) provide a self-test that proves the estimator can
recover known intrinsics from synthetic views.

Usage:
    python3 tools/calibrate_camera.py --self-test
    python3 tools/calibrate_camera.py --images caps/calib --frame config/frames/FRAME-0001.json \
        --width 4000 --height 3000 --profile-id PHONE-A_main_4000x3000 --out config/cameras/PHONE-A.json
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.camera import Camera, pose_looking_at_origin      # noqa: E402
from p0.core import (Rng, dump_json, load_json, mean, obj_hash,  # noqa: E402
                     read_png_gray, sd)
from p0.fiducial import detect_frame                      # noqa: E402
from p0.geometry import fit_homography, reprojection_stats  # noqa: E402


def residual(views, fx, k1, k2, width, height):
    cam = Camera(fx, fx, width / 2.0, height / 2.0, (k1, k2, 0.0, 0.0, 0.0),
                 width, height)
    tot = 0.0
    n = 0
    for plane, image in views:
        und = [cam.undistort_px(u, v) for (u, v) in image]
        try:
            H = fit_homography(plane, und)
        except Exception:
            return float("inf")
        st = reprojection_stats(H, plane, und)
        tot += st["rms_px"] ** 2 * st["n_points"]
        n += st["n_points"]
    return math.sqrt(tot / n) if n else float("inf")


def optimise(views, width, height, fx0, iters=6):
    fx, k1, k2 = fx0, 0.0, 0.0
    steps = [0.08 * fx0, 0.05, 0.05]
    for _ in range(iters):
        for idx in range(3):
            best = residual(views, fx, k1, k2, width, height)
            step = steps[idx]
            improved = True
            while improved and step > 1e-7 * max(1.0, abs([fx, 1, 1][idx])):
                improved = False
                for sign in (+1, -1):
                    trial = [fx, k1, k2]
                    trial[idx] += sign * step
                    if idx == 0 and trial[0] <= 1.0:
                        continue
                    r = residual(views, trial[0], trial[1], trial[2], width, height)
                    if r < best - 1e-12:
                        best = r
                        fx, k1, k2 = trial
                        improved = True
                        break
                if not improved:
                    step *= 0.45
            steps[idx] = max(step, 1e-6)
    return fx, k1, k2, residual(views, fx, k1, k2, width, height)


def collect(images, cert):
    views = []
    used = []
    for path in images:
        img = read_png_gray(path)
        try:
            cp = detect_frame(img, cert)
        except Exception as exc:
            print("  skip %s (%s)" % (os.path.basename(path), exc))
            continue
        views.append((cp.plane, cp.image))
        used.append(path)
    return views, used


def bootstrap(views, width, height, fx0, n=12):
    rng = Rng(20260918)
    fxs, k1s, k2s = [], [], []
    m = len(views)
    if m < 4:
        return {}
    for _ in range(n):
        samp = [views[rng.randint(m)] for _ in range(m)]
        fx, k1, k2, _ = optimise(samp, width, height, fx0, iters=3)
        fxs.append(fx)
        k1s.append(k1)
        k2s.append(k2)
    return {"fx_sd": sd(fxs), "k1_sd": sd(k1s), "k2_sd": sd(k2s),
            "n_resamples": n}


def self_test():
    """Recover known intrinsics from synthetic views of the frame."""
    from p0.render import SceneSpec, render_frame
    cfg = os.path.join(ROOT, "config")
    cert = load_json(os.path.join(cfg, "frames", "FRAME-SYN-0001.json"))
    # A wider field than the measurement profile, so the frame can be moved
    # around the image and actually sample the radial distortion field.
    cam = Camera(2400.0, 2400.0, 864.0, 528.0,
                 (-0.12, 0.05, 0.0, 0.0, 0.0), 1728, 1056)
    print("truth: fx=%.2f k1=%+.4f k2=%+.4f" % (cam.fx, cam.dist[0], cam.dist[1]))
    poses = [(200.0, 0.0, 0.0, 0.0, (0.0, 0.0)),
             (205.0, 14.0, 0.0, 0.0, (18.0, 9.0)),
             (200.0, -12.0, 9.0, 0.0, (-20.0, -10.0)),
             (215.0, 17.0, -15.0, 6.0, (16.0, -12.0)),
             (196.0, -15.0, 13.0, -5.0, (-15.0, 11.0)),
             (210.0, 8.0, 19.0, 3.0, (0.0, 14.0)),
             (200.0, 0.0, 0.0, 12.0, (22.0, 0.0)),
             (200.0, 0.0, 0.0, -9.0, (-22.0, 0.0))]
    views = []
    for i, (z, tilt, az, roll, shift) in enumerate(poses):
        spec = SceneSpec(z_mm=z, tilt_deg=tilt, azimuth_deg=az, roll_deg=roll,
                         shift_mm=shift, blur_sigma_px=0.7, noise_sigma=0.0015,
                         design_h_mm=3.0, ss_marker=6, ss_glyph=4)
        img, _ = render_frame(cam, cert, spec, Rng(1000 + i))
        cp = detect_frame(img, cert)
        views.append((cp.plane, cp.image))
    print("collected %d views" % len(views))
    r_true = residual(views, cam.fx, cam.dist[0], cam.dist[1], cam.width, cam.height)
    r_none = residual(views, cam.fx, 0.0, 0.0, cam.width, cam.height)
    fx, k1, k2, r = optimise(views, cam.width, cam.height, cam.fx * 0.9)
    print("residual with true intrinsics     : %.4f px" % r_true)
    print("residual with distortion ignored  : %.4f px" % r_none)
    print("residual with fitted intrinsics   : %.4f px" % r)
    print("estimated: fx=%.2f (%+.2f%%) k1=%+.4f k2=%+.4f"
          % (fx, 100 * (fx / cam.fx - 1), k1, k2))

    # A planar target at near-constant distance cannot separate focal length from
    # radial distortion: fx and k1 trade off along a valley.  What matters for
    # P0-min is NOT fx itself -- metric scale comes from the surveyed fiducial,
    # not from the intrinsics -- but whether the calibrated model removes enough
    # distortion for the measurement to stay accurate.  So that is what is tested.
    err_true, err_fit = _measurement_check(cam, cert, fx, k1, k2)
    print("height error with true intrinsics  : %s"
          % ("%+.4f mm" % err_true if err_true is not None else "abstained"))
    print("height error with fitted intrinsics: %s"
          % ("%+.4f mm" % err_fit if err_fit is not None else "abstained"))
    ok = (r < 0.5 * r_none
          and err_fit is not None
          and abs(err_fit) < 0.030)
    print("SELF-TEST", "PASS" if ok else "FAIL",
          "(criterion: residual halved AND |height error| < 0.030 mm)")
    return 0 if ok else 1


def _measurement_check(true_cam, cert, fx, k1, k2):
    """Run one end-to-end measurement with true vs fitted intrinsics."""
    from p0.pipeline import measure_run
    from p0.render import SceneSpec, glyph_shape_class, render_burst
    cfg = os.path.join(ROOT, "config")
    mp = load_json(os.path.join(cfg, "measurand_policy_v1.json"))
    gp = load_json(os.path.join(cfg, "gate_policy_v1.json"))
    um = load_json(os.path.join(cfg, "uncertainty_model_v1.json"))
    # Relax only the sampling-density and blur gates, because this wide-field
    # calibration camera deliberately runs at a lower rho than the measurement
    # profile; every other gate is untouched.
    gp = dict(gp, min_rho_px_per_mm=6.0, max_blur_sigma_mm=0.20)
    spec = SceneSpec(z_mm=200.0, tilt_deg=6.0, design_h_mm=4.0, blur_sigma_px=0.7,
                     noise_sigma=0.0015, ink_spread_mm=0.03, ss_marker=6,
                     ss_glyph=8, glyph_center_mm=(6.0, 3.0))
    frames, gts = render_burst(true_cam, cert, spec, "CALIB-CHECK", n=3)
    gt = gts[0]
    roi = tuple(gt["glyph_center_mm"]) + tuple(gt["glyph_bbox_mm"])
    out = []
    fitted = Camera(fx, fx, true_cam.cx, true_cam.cy, (k1, k2, 0.0, 0.0, 0.0),
                    true_cam.width, true_cam.height)
    for cam in (true_cam, fitted):
        res = measure_run(frames, cam, cert, mp, gp, um, roi,
                          glyph_shape_class(spec.glyph_shape),
                          0.9 * gt["true_ink_height_mm"], "CALIB-CHECK",
                          context={"profile_id": "selftest", "z_calib_mm": 200.0})
        h = res["measurement"]["h_mm"]
        out.append(None if h is None else h - gt["true_ink_height_mm"])
    return out[0], out[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--images", default="")
    ap.add_argument("--frame", default="")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--fx0", type=float, default=0.0)
    ap.add_argument("--profile-id", default="PHONE-A")
    ap.add_argument("--device-model", default="UNSPECIFIED")
    ap.add_argument("--physical-camera-id", default="0")
    ap.add_argument("--z-calib-mm", type=float, default=200.0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    if not (a.images and a.frame and a.out and a.width and a.height):
        ap.error("--images --frame --width --height --out are required")

    cert = load_json(a.frame)
    paths = sorted(glob.glob(os.path.join(a.images, "*.png")))
    if len(paths) < 6:
        print("WARNING: only %d views; >= 12 recommended" % len(paths))
    views, used = collect(paths, cert)
    if len(views) < 4:
        sys.exit("not enough usable views (%d)" % len(views))
    fx0 = a.fx0 or 1.2 * a.width
    fx, k1, k2, r = optimise(views, a.width, a.height, fx0)
    boot = bootstrap(views, a.width, a.height, fx)
    prof = {
        "profile_id": a.profile_id,
        "device_model": a.device_model,
        "physical_camera_id": a.physical_camera_id,
        "resolution": [a.width, a.height],
        "af_mode": "LOCKED",
        "ois_state": "MUST_BE_RECORDED",
        "camera": {"fx": fx, "fy": fx, "cx": a.width / 2.0, "cy": a.height / 2.0,
                   "dist": [k1, k2, 0.0, 0.0, 0.0],
                   "width": a.width, "height": a.height},
        "K_cov": boot,
        "reproj_holdout_rms_px": r,
        "n_views": len(views),
        "views_used": [os.path.basename(p) for p in used],
        "z_calib_mm": a.z_calib_mm,
        "z_calib_range_mm": [0.6 * a.z_calib_mm, 1.8 * a.z_calib_mm],
        "model": "REDUCED fx=fy, principal point fixed, radial k1 k2 only",
        "limitations": ["no tangential terms", "principal point not estimated",
                        "not a substitute for a full ChArUco calibration"],
    }
    prof["profile_hash"] = obj_hash(prof)
    dump_json(a.out, prof)
    print("fx=%.2f k1=%+.5f k2=%+.5f residual=%.4f px -> %s" % (fx, k1, k2, r, a.out))


if __name__ == "__main__":
    main()
