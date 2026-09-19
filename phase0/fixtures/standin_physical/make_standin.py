#!/usr/bin/env python3
"""Generate the STAND-IN PHYSICAL_PILOT dataset used to test analyser plumbing.

THIS IS NOT PHYSICAL EVIDENCE.  Every number is synthetic and arbitrary.  No camera,
coupon, scanner or microscope was involved.  See NOTICE.md.

The generator fixes *generator parameters* (a global offset, a per-device offset, a
within-cell spread, one abstained nominal run, a mostly-abstaining stress block) and
then lets the criteria fall wherever they fall.  It deliberately does not target a
particular verdict, and it deliberately produces a mixture of PASS / CONDITIONAL /
FAIL / UNCOMPUTABLE so every branch of the analyser is exercised.

Run:  python3 fixtures/standin_physical/make_standin.py
"""
from __future__ import annotations

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from p0.core import Rng, dump_json, seed_from  # noqa: E402

# ---- generator parameters (arbitrary, documented in NOTICE.md) -------------
GLOBAL_OFFSET_MM = 0.020          # a systematic offset shared by both devices
DEVICE_OFFSET_MM = {"A": +0.015, "B": -0.015}
WITHIN_CELL_SD_MM = 0.090         # spread across the three angle repeats
U_C_MM = 0.050                    # reported combined uncertainty per run
K = 1.645                         # matches config/uncertainty_model_v1.json
REFERENCE_DIFF_MM = 0.018         # scanner vs microscope disagreement scale

# ---- M1 stand-in crosshair readings (arbitrary; see NOTICE.md) -------------
# The microscope rows carry raw readings in the frozen M1 form so the validator's
# auditability check has something to exercise.  The spread is symmetric, so the
# mean of the repeats is exactly reference_h_mm and P1 is unaffected.
M1_REPEATS = 3
M1_BAND_MM = 0.030                # apparent transition-band width, both edges
M1_SPREAD_MM = 0.017320           # +/- offset of the outer repeats; 0.01*sqrt(3)


def m1_raw_readings(h_mm):
    """`Obot/Ibot/Itop/Otop` per re-setting, bottom boundary placed at stage 0."""
    out = []
    half = M1_BAND_MM / 2.0
    for d in (-M1_SPREAD_MM, 0.0, +M1_SPREAD_MM):
        h = h_mm + d
        out.append("%.6f/%.6f/%.6f/%.6f" % (-half, +half, h - half, h + half))
    return ";".join(out)

PANELS = [
    {"panel_id": "P01", "glyph_label": "BAR_I", "shape_class": "FLAT_TOP",
     "nominal_h_mm": 3.0, "reference_h_mm": 3.041},
    {"panel_id": "P02", "glyph_label": "RING_O", "shape_class": "ROUND",
     "nominal_h_mm": 2.0, "reference_h_mm": 2.028},
]
DEVICES = ["A", "B"]
OPERATORS = ["OP1", "OP2"]
REPEATS = [("R1", 0.0), ("R2", 12.0), ("R3", 25.0)]
ABSTAINED_NOMINAL = ("P02", "B", "OP2", "R3")       # exactly one
STRESS_CLASSES = ["DEFOCUS", "MOTION", "GLARE", "MARKER_OCCLUDED",
                  "WRONG_FRAME", "LOW_CONTRAST", "BOWED_PANEL", "FRAME_NOT_FLUSH"]
STRESS_MEASURED = {"LOW_CONTRAST"}                  # one stress run slips through

COLUMNS = ["run_id", "fixture_id", "experiment", "variant", "source", "status",
           "decision", "reason_codes", "true_h_mm", "h_mm", "lower_mm", "upper_mm",
           "threshold_mm", "error_mm", "abs_error_mm", "covered", "burst_sd_mm",
           "u_c_mm", "failed_stage", "failed_gate", "frames_ok", "frames_requested",
           "design_h_mm", "shape_class", "safety_class", "panel_id", "operator",
           "device", "repeat", "angle_deg", "reference_method", "glyph_label"]


def _row(**kw):
    r = {c: "" for c in COLUMNS}
    r.update({"experiment": "PHYSICAL_PILOT", "variant": "base", "source": "real",
              "frames_requested": 7, "reference_method": "SCANNER_2400DPI"})
    r.update(kw)
    return r


def build():
    rows, runs = [], []

    for p in PANELS:
        for dev in DEVICES:
            for op in OPERATORS:
                for rep, ang in REPEATS:
                    rid = "%s-%s-%s-%s" % (p["panel_id"], dev, op, rep)
                    runs.append({"run_id": rid, "panel_id": p["panel_id"],
                                 "device": dev, "operator": op, "repeat": rep,
                                 "angle_deg": ang, "safety_class": "SAFE",
                                 "shape_class": p["shape_class"],
                                 "glyph_label": p["glyph_label"],
                                 "nominal_h_mm": p["nominal_h_mm"],
                                 "reference_h_mm": p["reference_h_mm"],
                                 "reference_method": "SCANNER_2400DPI"})
                    if (p["panel_id"], dev, op, rep) == ABSTAINED_NOMINAL:
                        rows.append(_row(
                            run_id=rid, fixture_id=p["panel_id"], status=
                            "PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY",
                            reason_codes="PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY"
                                         "|GATE_BLUR_SIGMA_MM",
                            failed_stage="IMAGE_QUALITY", failed_gate="blur_sigma_mm",
                            frames_ok=7, true_h_mm=p["reference_h_mm"],
                            design_h_mm=p["nominal_h_mm"],
                            shape_class=p["shape_class"], safety_class="SAFE",
                            panel_id=p["panel_id"], operator=op, device=dev,
                            repeat=rep, angle_deg=ang,
                            glyph_label=p["glyph_label"]))
                        continue
                    rng = Rng(seed_from("standin", rid))
                    h = (p["reference_h_mm"] + GLOBAL_OFFSET_MM
                         + DEVICE_OFFSET_MM[dev]
                         + rng.normal(0.0, WITHIN_CELL_SD_MM))
                    lo, hi = h - K * U_C_MM, h + K * U_C_MM
                    err = h - p["reference_h_mm"]
                    rows.append(_row(
                        run_id=rid, fixture_id=p["panel_id"], status="MEASURED",
                        decision="MEETS_SCREENING_THRESHOLD",
                        true_h_mm=p["reference_h_mm"], h_mm=h, lower_mm=lo,
                        upper_mm=hi, threshold_mm=1.0, error_mm=err,
                        abs_error_mm=abs(err),
                        covered=1 if lo <= p["reference_h_mm"] <= hi else 0,
                        burst_sd_mm=abs(rng.normal(0.012, 0.004)), u_c_mm=U_C_MM,
                        frames_ok=7, design_h_mm=p["nominal_h_mm"],
                        shape_class=p["shape_class"], safety_class="SAFE",
                        panel_id=p["panel_id"], operator=op, device=dev,
                        repeat=rep, angle_deg=ang, glyph_label=p["glyph_label"]))

    p = PANELS[0]
    for i, cls in enumerate(STRESS_CLASSES):
        rid = "%s-A-OP1-%s-S%02d" % (p["panel_id"], cls, i + 1)
        runs.append({"run_id": rid, "panel_id": p["panel_id"], "device": "A",
                     "operator": "OP1", "repeat": "S%02d" % (i + 1),
                     "safety_class": "UNSAFE_DETECTABLE",
                     "shape_class": p["shape_class"], "glyph_label": p["glyph_label"],
                     "nominal_h_mm": p["nominal_h_mm"],
                     "reference_h_mm": p["reference_h_mm"],
                     "reference_method": "SCANNER_2400DPI", "stress_class": cls})
        if cls in STRESS_MEASURED:
            rng = Rng(seed_from("standin-stress", rid))
            h = p["reference_h_mm"] + rng.normal(0.0, 0.20)
            lo, hi = h - K * U_C_MM, h + K * U_C_MM
            rows.append(_row(
                run_id=rid, fixture_id=p["panel_id"], status="MEASURED",
                decision="MEETS_SCREENING_THRESHOLD",
                true_h_mm=p["reference_h_mm"], h_mm=h, lower_mm=lo, upper_mm=hi,
                threshold_mm=1.0, error_mm=h - p["reference_h_mm"],
                abs_error_mm=abs(h - p["reference_h_mm"]),
                covered=1 if lo <= p["reference_h_mm"] <= hi else 0,
                burst_sd_mm=0.02, u_c_mm=U_C_MM, frames_ok=7,
                design_h_mm=p["nominal_h_mm"], shape_class=p["shape_class"],
                safety_class="UNSAFE_DETECTABLE", panel_id=p["panel_id"],
                operator="OP1", device="A", repeat="S%02d" % (i + 1),
                glyph_label=p["glyph_label"]))
        else:
            rows.append(_row(
                run_id=rid, fixture_id=p["panel_id"],
                status="PHYSICAL_SIZE_NOT_ESTABLISHED_SEGMENTATION",
                reason_codes="PHYSICAL_SIZE_NOT_ESTABLISHED_SEGMENTATION",
                failed_stage="SEGMENTATION", failed_gate="median_crossings",
                frames_ok=7, true_h_mm=p["reference_h_mm"],
                design_h_mm=p["nominal_h_mm"], shape_class=p["shape_class"],
                safety_class="UNSAFE_DETECTABLE", panel_id=p["panel_id"],
                operator="OP1", device="A", repeat="S%02d" % (i + 1),
                glyph_label=p["glyph_label"]))

    # reference table: 16 glyphs measured by both methods (P1 needs >= 15)
    ref = []
    shapes = ["BAR_I", "H", "T", "RING_O"]
    heights = [1.2, 2.0, 3.0, 4.0]
    n = 0
    for pi, panel in enumerate(("P01", "P02")):
        for sh in shapes:
            for hgt in heights:
                if n >= 16:
                    break
                rng = Rng(seed_from("standin-ref", panel, sh, hgt))
                base = hgt + 0.035 + rng.normal(0.0, 0.01)
                delta = rng.normal(0.0, REFERENCE_DIFF_MM)
                for method, val in (("SCANNER_2400DPI", base),
                                    ("MICROSCOPE", base + delta)):
                    scanner = method.startswith("SCANNER")
                    ref.append({
                        "glyph_id": "%s:%s:%.2f:%d" % (panel, sh, hgt, 1),
                        "panel_id": panel, "glyph_shape": sh,
                        "nominal_h_mm": hgt, "glyph_index": 1,
                        "method": method,
                        # the independence rule: the microscope cross-check must not
                        # be produced by the pipeline estimator
                        "measurement_procedure": ("PIPELINE_ESTIMATOR_ON_SCAN" if scanner
                                                  else "MANUAL_VISUAL_CROSSHAIR"),
                        "reference_h_mm": val, "unit": "mm", "reference_u_mm": 0.01,
                        "instrument_id": ("STANDIN-SCANNER" if scanner
                                          else "STANDIN-MICROSCOPE"),
                        "instrument_cal_ref": "STANDIN-NO-CERTIFICATE",
                        "operator": "OP1" if scanner else "OP2",
                        "measured_at": "2026-01-01T00:00:00Z",
                        "n_repeats": 1 if scanner else M1_REPEATS,
                        "raw_readings": "" if scanner else m1_raw_readings(val),
                        "cross_check_status": "PENDING",
                        "notes": "STAND-IN, NOT PHYSICAL EVIDENCE"})
                n += 1
    return rows, runs, ref


def main():
    rows, runs, ref = build()
    with open(os.path.join(HERE, "results.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {}
            for k in COLUMNS:
                v = r.get(k, "")
                out[k] = ("%.6f" % v) if isinstance(v, float) else v
            w.writerow(out)
    dump_json(os.path.join(HERE, "manifest_used.json"), {
        "NOTICE": "STAND-IN dataset for analyser plumbing tests. NOT physical evidence.",
        "frame_cert": "config/frames/FRAME-SYN-0001.json",
        "camera_profiles": {"A": "config/cameras/CAM-SYN-A.json",
                            "B": "config/cameras/CAM-SYN-A.json"},
        "measurand_policy": "config/measurand_policy_v1.json",
        "gate_policy": "config/gate_policy_v1.json",
        "uncertainty_model": "config/uncertainty_model_v1.json",
        "runs": runs})
    cols = ["glyph_id", "panel_id", "glyph_shape", "nominal_h_mm", "glyph_index",
            "method", "measurement_procedure", "reference_h_mm", "unit",
            "reference_u_mm", "instrument_id", "instrument_cal_ref", "operator",
            "measured_at", "n_repeats", "raw_readings", "cross_check_status", "notes"]
    with open(os.path.join(HERE, "reference_table.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in ref:
            out = dict(r)
            for k, v in out.items():
                if isinstance(v, float):
                    out[k] = "%.6f" % v
            w.writerow(out)
    print("stand-in written: %d result rows, %d manifest runs, %d reference rows"
          % (len(rows), len(runs), len(ref)))


if __name__ == "__main__":
    main()
