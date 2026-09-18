"""Result persistence: per-run JSON plus a flat CSV row for analysis."""
from __future__ import annotations

import csv
import os

from .core import dump_json, fmt
from .version import SCHEMA_VERSION

CSV_COLUMNS = [
    "run_id", "fixture_id", "experiment", "variant", "source", "status",
    "decision", "reason_codes",
    "true_h_mm", "h_mm", "lower_mm", "upper_mm", "threshold_mm",
    "error_mm", "abs_error_mm", "covered",
    "h_raw_mean_mm", "h_maxminus_min_mm", "maxminus_min_error_mm",
    "burst_sd_mm", "u_random_mm", "u_scale_mm", "u_seg_mm", "u_c_mm",
    "interval_width_mm",
    "rho_min_px_per_mm", "blur_sigma_mm", "michelson_contrast", "snr",
    "overshoot_ratio", "reproj_rms_px", "reproj_max_px", "edge_rms_px",
    "lomo_rel_spread", "view_tilt_deg", "z_mm", "hull_margin_mm",
    "jacobian_ratio", "scanline_fraction", "median_crossings",
    "thickness_over_z", "clip_bright_frac", "clip_dark_frac",
    "frames_ok", "frames_requested", "failed_stage", "failed_gate",
    "glyph_shape", "shape_class", "design_h_mm", "ink_spread_mm",
    "pose_tilt_deg", "pose_z_mm", "glyph_plane_offset_mm",
    "glyph_plane_tilt_deg", "undistort_enabled", "linearize_enabled",
    "algorithm_version", "timing_s",
]


def save_run(out_dir, result, extra=None):
    os.makedirs(out_dir, exist_ok=True)
    payload = dict(result)
    payload["schema_version"] = SCHEMA_VERSION
    if extra:
        payload["ground_truth"] = extra
    m = payload.get("measurement", {})
    payload["display"] = {
        "h_mm": fmt(m.get("h_mm"), 4),
        "lower_mm": fmt(m.get("lower_mm"), 4),
        "upper_mm": fmt(m.get("upper_mm"), 4),
        "threshold_mm": fmt(m.get("threshold_mm"), 4),
        "u_c_mm": fmt((payload.get("budget") or {}).get("u_c_mm"), 4),
        "status": payload.get("status"),
        "decision": m.get("decision"),
    }
    dump_json(os.path.join(out_dir, "result.json"), payload)
    return payload


def flat_row(result, gt=None, meta=None):
    gt = gt or {}
    meta = meta or {}
    m = result.get("measurement") or {}
    b = result.get("budget") or {}
    mt = result.get("metrics") or {}
    pf = result.get("per_frame") or []
    true_h = gt.get("true_ink_height_mm")
    h = m.get("h_mm")
    err = (h - true_h) if (h is not None and true_h is not None) else None
    covered = None
    if h is not None and true_h is not None:
        covered = int(m["lower_mm"] <= true_h <= m["upper_mm"])
    mm_diag = None
    if pf:
        vals = [f["h_maxminus_min_diagnostic_mm"] for f in pf
                if f.get("h_maxminus_min_diagnostic_mm") is not None]
        if vals:
            mm_diag = sum(vals) / len(vals)
    row = {
        "run_id": result.get("run_id"),
        "fixture_id": meta.get("fixture_id"),
        "experiment": meta.get("experiment"),
        "variant": meta.get("variant"),
        "source": meta.get("source", "synthetic"),
        "status": result.get("status"),
        "decision": m.get("decision"),
        "reason_codes": "|".join(result.get("reason_codes") or []),
        "true_h_mm": true_h,
        "h_mm": h,
        "lower_mm": m.get("lower_mm"),
        "upper_mm": m.get("upper_mm"),
        "threshold_mm": m.get("threshold_mm"),
        "error_mm": err,
        "abs_error_mm": abs(err) if err is not None else None,
        "covered": covered,
        "h_raw_mean_mm": b.get("h_raw_mean_mm"),
        "h_maxminus_min_mm": mm_diag,
        "maxminus_min_error_mm": (mm_diag - true_h) if (mm_diag is not None and true_h) else None,
        "burst_sd_mm": b.get("burst_sd_mm"),
        "u_random_mm": b.get("u_random_mm"),
        "u_scale_mm": b.get("u_scale_mm"),
        "u_seg_mm": b.get("u_seg_mm"),
        "u_c_mm": b.get("u_c_mm"),
        "interval_width_mm": b.get("interval_width_mm"),
        "failed_stage": (result.get("gates") or {}).get("failed_stage"),
        "failed_gate": (result.get("gates") or {}).get("failed_gate"),
        "frames_ok": (result.get("inputs") or {}).get("frames_ok"),
        "frames_requested": (result.get("inputs") or {}).get("frames_requested"),
        "glyph_shape": gt.get("glyph_shape"),
        "shape_class": gt.get("shape_class"),
        "design_h_mm": gt.get("design_h_mm"),
        "ink_spread_mm": gt.get("ink_spread_mm"),
        "pose_tilt_deg": gt.get("pose_tilt_deg"),
        "pose_z_mm": gt.get("pose_z_mm"),
        "glyph_plane_offset_mm": gt.get("glyph_plane_offset_mm"),
        "glyph_plane_tilt_deg": gt.get("glyph_plane_tilt_deg"),
        "undistort_enabled": meta.get("undistort_enabled"),
        "linearize_enabled": meta.get("linearize_enabled"),
        "algorithm_version": (result.get("inputs") or {}).get("algorithm_version"),
        "timing_s": result.get("timing_s"),
    }
    for key in ("rho_min_px_per_mm", "blur_sigma_mm", "michelson_contrast", "snr",
                "overshoot_ratio", "reproj_rms_px", "reproj_max_px", "edge_rms_px",
                "lomo_rel_spread", "view_tilt_deg", "z_mm", "hull_margin_mm",
                "jacobian_ratio", "scanline_fraction", "median_crossings",
                "thickness_over_z", "clip_bright_frac", "clip_dark_frac"):
        row[key] = mt.get(key)
    return row


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {}
            for k in CSV_COLUMNS:
                v = r.get(k)
                if isinstance(v, float):
                    if v != v or v in (float("inf"), float("-inf")):
                        v = ""
                    else:
                        v = "%.6f" % v
                out[k] = "" if v is None else v
            w.writerow(out)


def read_csv(path):
    with open(path, "r", encoding="utf-8") as fh:
        rows = []
        for r in csv.DictReader(fh):
            out = {}
            for k, v in r.items():
                if v == "":
                    out[k] = None
                    continue
                try:
                    out[k] = float(v)
                except (TypeError, ValueError):
                    out[k] = v
            rows.append(out)
    return rows
