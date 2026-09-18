#!/usr/bin/env python3
"""P0-min experiment runner (synthetic fixtures).

Usage:
    python3 tools/run_experiment.py                      # whole suite
    python3 tools/run_experiment.py --only E_MATH,E_TILT
    python3 tools/run_experiment.py --frames 3 --fast    # quick smoke run
    python3 tools/run_experiment.py --out out/run2

Outputs:
    <out>/results.csv                     one row per run
    <out>/runs/<run_id>/result.json       full machine readable result
    <out>/runs/<run_id>/frame0.png        first frame of the burst (evidence)
    <out>/manifest.json                   configuration + fixture hashes
    <out>/run.log
"""
from __future__ import annotations

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.camera import Camera                                    # noqa: E402
from p0.core import (Img, dump_json, load_json, obj_hash, seed_from,  # noqa: E402
                     srgb_encode, write_png_gray)
from p0.pipeline import measure_run                             # noqa: E402
from p0.render import SceneSpec, glyph_shape_class, render_burst  # noqa: E402
from p0.results import flat_row, save_run, write_csv            # noqa: E402
from p0.version import ALGORITHM_VERSION                        # noqa: E402
from experiments import suite                                    # noqa: E402


def gamma_copy(img):
    """Re-express the buffer in sRGB-encoded units (the E2 ablation)."""
    out = Img(img.w, img.h)
    out.lin = type(img.lin)("d", [srgb_encode(v) for v in img.lin])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "synthetic"))
    ap.add_argument("--only", default="")
    ap.add_argument("--frames", type=int, default=7)
    ap.add_argument("--fast", action="store_true",
                    help="lower supersampling; for smoke tests only")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--save-png", default="first",
                    choices=["first", "none", "all"])
    args = ap.parse_args()

    cfg = os.path.join(ROOT, "config")
    mp = load_json(os.path.join(cfg, "measurand_policy_v1.json"))
    gp = load_json(os.path.join(cfg, "gate_policy_v1.json"))
    um = load_json(os.path.join(cfg, "uncertainty_model_v1.json"))

    only = set(x.strip() for x in args.only.split(",") if x.strip())
    fixtures = [f for f in suite() if not only or f["experiment"] in only
                or f["fixture_id"] in only]

    os.makedirs(args.out, exist_ok=True)
    log_path = os.path.join(args.out, "run.log")
    log = open(log_path, "w", encoding="utf-8")

    def emit(msg):
        print(msg)
        log.write(msg + "\n")
        log.flush()

    emit("P0-min runner  algorithm=%s  fixtures=%d  frames=%d  fast=%s"
         % (ALGORITHM_VERSION, len(fixtures), args.frames, args.fast))

    rows = []
    manifest = {"algorithm_version": ALGORITHM_VERSION,
                "measurand_policy_hash": obj_hash(mp),
                "gate_policy_hash": obj_hash(gp),
                "uncertainty_model": um,
                "frames_per_burst": args.frames,
                "fast_mode": bool(args.fast),
                "fixtures": []}

    t_start = time.time()

    if args.jobs > 1:
        import multiprocessing as mplib
        payload = [(fx, args, cfg, mp, gp, um) for fx in fixtures]
        with mplib.Pool(args.jobs) as pool:
            for i, (frows, fman, lines) in enumerate(
                    pool.imap(_worker, payload, chunksize=1)):
                rows.extend(frows)
                manifest["fixtures"].append(fman)
                for ln in lines:
                    emit("[%3d/%3d] %s" % (i + 1, len(fixtures), ln))
        _finish(args, rows, manifest, t_start, emit, log)
        return

    for i, fx in enumerate(fixtures):
        fid = fx["fixture_id"]
        cert = load_json(os.path.join(cfg, "frames", fx["frame"] + ".json"))
        prof = load_json(os.path.join(cfg, "cameras", fx["camera"] + ".json"))
        cam = Camera.from_dict(prof["camera"])
        spec_kw = dict(fx["spec"])
        if args.fast:
            spec_kw["ss_marker"] = 3
            spec_kw["ss_glyph"] = 4
        spec = SceneSpec(**spec_kw)

        t0 = time.time()
        frames, gts = render_burst(cam, cert, spec, fid, n=args.frames)
        t_render = time.time() - t0

        gt0 = dict(gts[0])
        gt0["frames"] = [g["frame_pose"] for g in gts]
        true_h = gt0["true_ink_height_mm"]
        roi = tuple(gt0["glyph_center_mm"]) + tuple(gt0["glyph_bbox_mm"])
        shape_class = glyph_shape_class(spec.glyph_shape)
        threshold = (3.0 if fx["threshold_mode"] == "FIXED_3.0"
                     else round(0.9 * true_h, 4))

        for variant in fx["variants"]:
            run_id = "%s__%s" % (fid, variant)
            proc_cam = cam
            imgs = frames
            meta = {"fixture_id": fid, "experiment": fx["experiment"],
                    "variant": variant, "source": "synthetic",
                    "undistort_enabled": True, "linearize_enabled": True}
            if variant == "undistort_off":
                d = dict(prof["camera"])
                d["dist"] = [0.0] * 5
                proc_cam = Camera.from_dict(d)
                meta["undistort_enabled"] = False
            glyph_imgs = None
            if variant == "gamma":
                imgs = [gamma_copy(f) for f in frames]
                meta["linearize_enabled"] = False
            if variant == "gamma_glyph_only":
                glyph_imgs = [gamma_copy(f) for f in frames]
                meta["linearize_enabled"] = False

            ctx = {"profile_id": prof["profile_id"],
                   "z_calib_mm": prof["z_calib_mm"],
                   "camera_identity_match": True,
                   "frame_serial_match": True,
                   "frame_not_expired": True,
                   "declared_flat": True,
                   "safety_class": fx["safety_class"],
                   "variant": variant}
            t1 = time.time()
            res = measure_run(imgs, proc_cam, cert, mp, gp, um, roi, shape_class,
                              threshold, run_id, context=ctx,
                              glyph_images=glyph_imgs)
            t_proc = time.time() - t1

            run_dir = os.path.join(args.out, "runs", run_id)
            gt_out = dict(gt0)
            gt_out["safety_class"] = fx["safety_class"]
            gt_out["note"] = fx["note"]
            gt_out["spec"] = spec.to_dict()
            gt_out["frame_cert"] = cert["serial"]
            gt_out["camera_profile"] = prof["profile_id"]
            save_run(run_dir, res, extra=gt_out)
            if args.save_png != "none":
                n_save = len(imgs) if args.save_png == "all" else 1
                for k in range(n_save):
                    write_png_gray(os.path.join(run_dir, "frame%d.png" % k),
                                   imgs[k].w, imgs[k].h, imgs[k].quantize_u8())

            row = flat_row(res, gt=gt_out, meta=meta)
            row["safety_class"] = fx["safety_class"]
            rows.append(row)

            m = res["measurement"]
            if m["h_mm"] is not None:
                emit("[%3d/%3d] %-34s %-14s true=%.4f est=%.4f err=%+.4f "
                     "u_c=%.4f %s (render %.1fs proc %.1fs)"
                     % (i + 1, len(fixtures), fid, variant, true_h, m["h_mm"],
                        m["h_mm"] - true_h, res["budget"]["u_c_mm"],
                        m["decision"], t_render, t_proc))
            else:
                emit("[%3d/%3d] %-34s %-14s ABSTAIN %-28s gate=%s "
                     "(render %.1fs proc %.1fs)"
                     % (i + 1, len(fixtures), fid, variant, res["status"],
                        res["gates"].get("failed_gate"), t_render, t_proc))

        manifest["fixtures"].append({
            "fixture_id": fid, "experiment": fx["experiment"],
            "safety_class": fx["safety_class"], "variants": fx["variants"],
            "frame": fx["frame"], "camera": fx["camera"],
            "threshold_mm": threshold, "true_ink_height_mm": true_h,
            "spec_hash": obj_hash(spec.to_dict()),
            "burst_seed_base": seed_from(fid, "frame", 0),
            "note": fx["note"]})

    _finish(args, rows, manifest, t_start, emit, log)


def _finish(args, rows, manifest, t_start, emit, log):
    from p0.results import CSV_COLUMNS
    if "safety_class" not in CSV_COLUMNS:
        CSV_COLUMNS.append("safety_class")
    rows = sorted(rows, key=lambda r: (str(r.get("fixture_id")), str(r.get("variant"))))
    write_csv(os.path.join(args.out, "results.csv"), rows)
    manifest["runs"] = len(rows)
    manifest["wall_clock_s"] = time.time() - t_start
    manifest["fixtures"] = sorted(manifest["fixtures"],
                                  key=lambda f: str(f.get("fixture_id")))
    dump_json(os.path.join(args.out, "manifest.json"), manifest)
    emit("done: %d runs in %.1fs -> %s" % (len(rows), manifest["wall_clock_s"],
                                           args.out))
    log.close()


def run_fixture(fx, args, cfg, mp, gp, um):
    """Render and process one fixture; returns (rows, manifest_entry, log_lines)."""
    fid = fx["fixture_id"]
    cert = load_json(os.path.join(cfg, "frames", fx["frame"] + ".json"))
    prof = load_json(os.path.join(cfg, "cameras", fx["camera"] + ".json"))
    cam = Camera.from_dict(prof["camera"])
    spec_kw = dict(fx["spec"])
    if args.fast:
        spec_kw["ss_marker"] = 3
        spec_kw["ss_glyph"] = 4
    spec = SceneSpec(**spec_kw)

    t0 = time.time()
    frames, gts = render_burst(cam, cert, spec, fid, n=args.frames)
    t_render = time.time() - t0

    gt0 = dict(gts[0])
    gt0["frames"] = [g["frame_pose"] for g in gts]
    true_h = gt0["true_ink_height_mm"]
    roi = tuple(gt0["glyph_center_mm"]) + tuple(gt0["glyph_bbox_mm"])
    shape_class = glyph_shape_class(spec.glyph_shape)
    threshold = (3.0 if fx["threshold_mode"] == "FIXED_3.0"
                 else round(0.9 * true_h, 4))

    rows = []
    lines = []
    for variant in fx["variants"]:
        run_id = "%s__%s" % (fid, variant)
        proc_cam = cam
        imgs = frames
        meta = {"fixture_id": fid, "experiment": fx["experiment"],
                "variant": variant, "source": "synthetic",
                "undistort_enabled": True, "linearize_enabled": True}
        if variant == "undistort_off":
            d = dict(prof["camera"])
            d["dist"] = [0.0] * 5
            proc_cam = Camera.from_dict(d)
            meta["undistort_enabled"] = False
        glyph_imgs = None
        if variant == "gamma":
            imgs = [gamma_copy(f) for f in frames]
            meta["linearize_enabled"] = False
        if variant == "gamma_glyph_only":
            glyph_imgs = [gamma_copy(f) for f in frames]
            meta["linearize_enabled"] = False

        ctx = {"profile_id": prof["profile_id"], "z_calib_mm": prof["z_calib_mm"],
               "camera_identity_match": True, "frame_serial_match": True,
               "frame_not_expired": True, "declared_flat": True,
               "safety_class": fx["safety_class"], "variant": variant}
        t1 = time.time()
        res = measure_run(imgs, proc_cam, cert, mp, gp, um, roi, shape_class,
                          threshold, run_id, context=ctx, glyph_images=glyph_imgs)
        t_proc = time.time() - t1

        run_dir = os.path.join(args.out, "runs", run_id)
        gt_out = dict(gt0)
        gt_out["safety_class"] = fx["safety_class"]
        gt_out["note"] = fx["note"]
        gt_out["spec"] = spec.to_dict()
        gt_out["frame_cert"] = cert["serial"]
        gt_out["camera_profile"] = prof["profile_id"]
        save_run(run_dir, res, extra=gt_out)
        if args.save_png != "none":
            n_save = len(imgs) if args.save_png == "all" else 1
            for k in range(n_save):
                write_png_gray(os.path.join(run_dir, "frame%d.png" % k),
                               imgs[k].w, imgs[k].h, imgs[k].quantize_u8())

        row = flat_row(res, gt=gt_out, meta=meta)
        row["safety_class"] = fx["safety_class"]
        rows.append(row)

        m = res["measurement"]
        if m["h_mm"] is not None:
            lines.append("%-34s %-17s true=%.4f est=%.4f err=%+.4f u_c=%.4f %s "
                         "(render %.1fs proc %.1fs)"
                         % (fid, variant, true_h, m["h_mm"], m["h_mm"] - true_h,
                            res["budget"]["u_c_mm"], m["decision"], t_render, t_proc))
        else:
            lines.append("%-34s %-17s ABSTAIN %-30s gate=%s (render %.1fs proc %.1fs)"
                         % (fid, variant, res["status"],
                            res["gates"].get("failed_gate"), t_render, t_proc))

    man = {"fixture_id": fid, "experiment": fx["experiment"],
           "safety_class": fx["safety_class"], "variants": fx["variants"],
           "frame": fx["frame"], "camera": fx["camera"],
           "threshold_mm": threshold, "true_ink_height_mm": true_h,
           "spec_hash": obj_hash(spec.to_dict()),
           "burst_seed_base": seed_from(fid, "frame", 0), "note": fx["note"]}
    return rows, man, lines


def _worker(payload):
    return run_fixture(*payload)


if __name__ == "__main__":
    main()
