"""End-to-end measurement pipeline for one burst (one measurement run).

Normative stage order (frozen; changing it changes results):

    linear luminance
      -> fiducial detection (subpixel edge-line corners, distorted space)
      -> undistort control points
      -> homography plane(mm) -> ideal pixel
      -> geometric diagnostics (rho, jacobian, tilt, Z, hull margin, LOMO)
      -> baseline refinement
      -> scanline boundary crossings (distorted space)
      -> undistort crossings -> H^-1 -> plane mm
      -> fitted top/bottom extremes -> raw height
      -> fiducial-thickness correction
      -> burst aggregation -> uncertainty budget
      -> gates -> MEASURE / ABSTAIN
      -> guard-band decision
"""
from __future__ import annotations

import math
import time

from .camera import Camera, rho_at, view_tilt_deg, z_estimate_mm
from .core import mat3_inv, mean, median, obj_hash
from .fiducial import DetectError, detect_frame
from .geometry import (fit_homography, hull_margin_mm,
                       leave_one_group_out_scale, reprojection_stats)
from .gates import evaluate, status_from
from .measure import (MeasureError, clipping_stats, estimate_baseline_dir,
                      measure_glyph)
from .uncertainty import build_budget, decide, thickness_correction
from .version import ALGORITHM_VERSION

MIN_FRAME_FRACTION = 0.70


def _control_baseline_mm(plane_pts):
    best = 0.0
    for i in range(len(plane_pts)):
        for j in range(i + 1, len(plane_pts)):
            d = math.hypot(plane_pts[i][0] - plane_pts[j][0],
                           plane_pts[i][1] - plane_pts[j][1])
            if d > best:
                best = d
    return best


def process_frame(img, cam: Camera, frame_cert, measurand_policy, roi_mm,
                 shape_class, rng, glyph_img=None):
    """Single frame -> per frame metrics.  Raises DetectError / MeasureError.

    `glyph_img` exists only for ablation studies: geometry is taken from `img`
    while the glyph boundary is measured on `glyph_img`.  In production both are
    the same buffer.
    """
    gimg = glyph_img if glyph_img is not None else img
    cp = detect_frame(img, frame_cert)
    img_undist = [cam.undistort_px(u, v) for (u, v) in cp.image]
    H = fit_homography(cp.plane, img_undist)
    Hinv = mat3_inv(H)
    rep = reprojection_stats(H, cp.plane, img_undist)

    cx, cy = roi_mm[0], roi_mm[1]
    rho_geo, rho_min, jratio = rho_at(H, cx, cy)
    tilt = view_tilt_deg(cam, H)
    z = z_estimate_mm(cam, H, cx, cy)
    margin = hull_margin_mm((cx, cy), cp.plane)
    lomo = leave_one_group_out_scale(cp.plane, img_undist, cp.groups, (cx, cy))

    bdir, bang = estimate_baseline_dir(gimg, cam, H, Hinv, roi_mm, measurand_policy)
    m = measure_glyph(gimg, cam, H, Hinv, roi_mm, shape_class, measurand_policy,
                      rng=rng, baseline_dir=bdir)
    clip = clipping_stats(gimg, cam, H, roi_mm)

    h_corr, thick_rel = thickness_correction(
        m["h_mm"], float(frame_cert.get("thickness_mm", 0.0)), z)

    sens_dev = 0.0
    for v in m["h_mm_sensitivity"].values():
        sens_dev = max(sens_dev, abs(v - m["h_mm"]))

    # Blur is estimated on the long straight marker borders, not on the glyph:
    # a curved glyph apex inflates the apparent 10-90 rise and would make the
    # gate shape dependent (PHASE0_REVIEW F7.3).
    rises = cp.diagnostics.get("edge_rise_px") or []
    marker_rise_px = median(rises) if rises else float("nan")
    marker_sigma_mm = ((marker_rise_px / 2.563) / rho_geo
                       if rises and rho_geo > 0 else float("nan"))

    return {
        "h_raw_mm": m["h_mm"],
        "h_thickness_corrected_mm": h_corr,
        "thickness_rel_correction": thick_rel,
        "h_sensitivity_dev_mm": sens_dev,
        "h_maxminus_min_diagnostic_mm": m["h_mm_maxminus_min_diagnostic"],
        "u_edge_mm": m["u_edge_mm"],
        "rho_geo_px_per_mm": rho_geo,
        "rho_min_px_per_mm": rho_min,
        "jacobian_ratio": jratio,
        "view_tilt_deg": tilt,
        "z_mm": z,
        "hull_margin_mm": margin,
        "lomo_rel_spread": lomo["rel_spread"],
        "reproj_rms_px": rep["rms_px"],
        "reproj_max_px": rep["max_px"],
        "n_control_points": rep["n_points"],
        "control_baseline_mm": _control_baseline_mm(cp.plane),
        "edge_rms_px": max(cp.diagnostics["edge_rms_px"]) if cp.diagnostics["edge_rms_px"] else float("nan"),
        "blur_sigma_mm": marker_sigma_mm,
        "blur_sigma_glyph_mm": m["edge_sigma_mm"],
        "marker_rise_px": marker_rise_px,
        "sensitivity_dev_frac": (sens_dev / m["h_mm"]) if m["h_mm"] else float("nan"),
        "edge_fit_rms_mm": m["edge_fit_rms_mm"],
        "n_top_cluster": m["n_top_cluster"],
        "n_bot_cluster": m["n_bot_cluster"],
        "michelson_contrast": m["michelson_contrast"],
        "snr": m["snr"],
        "overshoot_ratio": m["overshoot_ratio"],
        "scanline_fraction": m["scanlines_used"] / float(m["scanlines_requested"]),
        "median_crossings": m["crossings_median"],
        "baseline_angle_deg": bang,
        "clip_dark_frac": clip["clip_dark_frac"],
        "clip_bright_frac": clip["clip_bright_frac"],
        "detected_marker_ids": list(cp.marker_ids),
    }


def measure_run(images, cam: Camera, frame_cert, measurand_policy, gate_policy,
                unc_model, roi_mm, shape_class, threshold_mm, run_id,
                context=None, rng_factory=None, glyph_images=None):
    """Process a burst and return the full machine-readable result."""
    t0 = time.time()
    ctx_in = dict(context or {})
    per_frame = []
    frame_errors = []
    from .core import Rng, seed_from
    for idx, img in enumerate(images):
        rng = (rng_factory(idx) if rng_factory
               else Rng(seed_from(run_id, "boot", idx)))
        try:
            gimg = glyph_images[idx] if glyph_images else None
            per_frame.append(process_frame(img, cam, frame_cert, measurand_policy,
                                           roi_mm, shape_class, rng,
                                           glyph_img=gimg))
        except DetectError as exc:
            frame_errors.append({"frame": idx, "stage": "FIDUCIAL",
                                 "code": exc.code, "detail": exc.detail})
        except MeasureError as exc:
            frame_errors.append({"frame": idx, "stage": "SEGMENTATION",
                                 "code": exc.code, "detail": exc.detail})
        except Exception as exc:                       # pragma: no cover
            frame_errors.append({"frame": idx, "stage": "GEOMETRY",
                                 "code": type(exc).__name__, "detail": str(exc)})

    n_req = len(images)
    n_ok = len(per_frame)
    inputs = {
        "algorithm_version": ALGORITHM_VERSION,
        "measurand_policy_hash": obj_hash(measurand_policy),
        "gate_policy_hash": obj_hash(gate_policy),
        "uncertainty_model": unc_model.get("model_version"),
        "frame_cert_serial": frame_cert.get("serial"),
        "frame_cert_hash": obj_hash(frame_cert),
        "camera_profile_id": ctx_in.get("profile_id"),
        "frames_requested": n_req,
        "frames_ok": n_ok,
    }

    if n_ok < max(2, int(math.ceil(MIN_FRAME_FRACTION * n_req))):
        stage = frame_errors[0]["stage"] if frame_errors else "FIDUCIAL"
        codes = sorted(set(e["code"] for e in frame_errors))
        return {
            "run_id": run_id,
            "status": "PHYSICAL_SIZE_NOT_ESTABLISHED_" + stage,
            "reason_codes": codes,
            "measurement": {"h_mm": None, "lower_mm": None, "upper_mm": None,
                            "threshold_mm": threshold_mm, "decision": None},
            "metrics": {},
            "budget": None,
            "gates": {"rows": [], "failed_stage": stage,
                      "failed_gate": codes[0] if codes else None},
            "per_frame": per_frame,
            "frame_errors": frame_errors,
            "inputs": inputs,
            "context": ctx_in,
            "timing_s": time.time() - t0,
        }

    def agg(key, how=median):
        vals = [f[key] for f in per_frame if f.get(key) is not None and f[key] == f[key]]
        return how(vals) if vals else float("nan")

    h_frames = [f["h_thickness_corrected_mm"] for f in per_frame]
    geom = {
        "lomo_rel_spread": agg("lomo_rel_spread"),
        "z_mm": agg("z_mm"),
        "control_baseline_mm": agg("control_baseline_mm"),
    }
    budget = build_budget(h_frames,
                          [f["u_edge_mm"] for f in per_frame],
                          [f["h_sensitivity_dev_mm"] for f in per_frame],
                          geom, frame_cert, unc_model)

    thickness = float(frame_cert.get("thickness_mm", 0.0))
    gate_ctx = {
        "profile_id": ctx_in.get("profile_id"),
        "camera_identity_match": ctx_in.get("camera_identity_match", True),
        "frame_serial_match": ctx_in.get("frame_serial_match", True),
        "frame_not_expired": ctx_in.get("frame_not_expired", True),
        "declared_flat": ctx_in.get("declared_flat", True),
        "z_calib_mm": ctx_in.get("z_calib_mm"),
        "n_control_points": agg("n_control_points", min),
        "edge_rms_px": agg("edge_rms_px", max),
        "blur_sigma_mm": agg("blur_sigma_mm"),
        "michelson_contrast": agg("michelson_contrast"),
        "snr": agg("snr"),
        "clip_dark_frac": agg("clip_dark_frac", max),
        "clip_bright_frac": agg("clip_bright_frac", max),
        "overshoot_ratio": agg("overshoot_ratio", max),
        "reproj_rms_px": agg("reproj_rms_px", max),
        "reproj_max_px": agg("reproj_max_px", max),
        "rho_min_px_per_mm": agg("rho_min_px_per_mm", min),
        "jacobian_ratio": agg("jacobian_ratio", max),
        "hull_margin_mm": agg("hull_margin_mm", min),
        "view_tilt_deg": agg("view_tilt_deg", max),
        "lomo_rel_spread": agg("lomo_rel_spread", max),
        "thickness_over_z": (thickness / geom["z_mm"]) if geom["z_mm"] == geom["z_mm"] and geom["z_mm"] > 0 else float("nan"),
        "scanline_fraction": agg("scanline_fraction", min),
        "median_crossings": agg("median_crossings", max),
        "sensitivity_dev_frac": agg("sensitivity_dev_frac", max),
        "edge_fit_rms_mm": agg("edge_fit_rms_mm", max),
        "min_cluster_points": min(agg("n_top_cluster", min), agg("n_bot_cluster", min)),
        "blur_sigma_glyph_mm": agg("blur_sigma_glyph_mm"),
        "burst_sd_mm": budget["burst_sd_mm"],
        "interval_width_mm": budget["interval_width_mm"],
        "threshold_mm": threshold_mm,
    }

    gt = evaluate(gate_policy, gate_ctx)
    status, reasons = status_from(gt)
    if frame_errors:
        reasons = reasons + ["FRAME_ERRORS_%d" % len(frame_errors)]

    if status == "MEASURED":
        decision = decide(budget, threshold_mm)
        meas = {"h_mm": budget["h_corrected_mm"],
                "lower_mm": budget["lower_mm"],
                "upper_mm": budget["upper_mm"],
                "threshold_mm": threshold_mm,
                "decision": decision}
    else:
        meas = {"h_mm": None, "lower_mm": None, "upper_mm": None,
                "threshold_mm": threshold_mm, "decision": None}

    return {
        "run_id": run_id,
        "status": status,
        "reason_codes": reasons,
        "measurement": meas,
        "metrics": gate_ctx,
        "budget": budget,
        "gates": gt.as_dict(),
        "per_frame": per_frame,
        "frame_errors": frame_errors,
        "inputs": inputs,
        "context": ctx_in,
        "timing_s": time.time() - t0,
    }
