#!/usr/bin/env python3
"""Run the P0-min pipeline over real camera captures described by a manifest.

The output CSV is schema-compatible with the synthetic runner, so
`tools/analyse_results.py` works unchanged and the same pre-registered criteria
apply.  `reference_h_mm` (the measurement from the reference method) is written
into the `true_h_mm` column -- there is no other source of truth for real panels.

Images must be 8-bit greyscale PNG (see docs/P0_ASSUMPTIONS.md A-02 for why, and
for the one-line conversion from phone JPEG/DNG).

Usage:
    python3 tools/run_real_batch.py --scaffold caps --out manifests/pilot.json
    python3 tools/run_real_batch.py --manifest manifests/pilot.json --out out/pilot
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.camera import Camera                                  # noqa: E402
from p0.core import dump_json, load_json, read_png_gray        # noqa: E402
from p0.pipeline import measure_run                            # noqa: E402
from p0.results import CSV_COLUMNS, flat_row, save_run, write_csv  # noqa: E402

REQUIRED = ("run_id", "frames", "roi_mm", "shape_class", "device")


def scaffold(root, out):
    """Walk caps/<panel>/<device>/<operator>/<repeat>/*.png into a manifest stub."""
    runs = []
    for d in sorted(glob.glob(os.path.join(root, "*", "*", "*", "*"))):
        pngs = sorted(glob.glob(os.path.join(d, "*.png")))
        if not pngs:
            continue
        parts = os.path.normpath(d).split(os.sep)[-4:]
        panel, device, operator, repeat = parts
        runs.append({
            "run_id": "%s-%s-%s-%s" % (panel, device, operator, repeat),
            "panel_id": panel, "device": device, "operator": operator,
            "repeat": repeat, "frames": pngs,
            # roi_mm is deliberately null, never a plausible stub: a stub box at
            # the frame centre would silently measure whatever lies there.  It is
            # computed from the pre-registered glyph map --
            # tools/validate_roi_map.py --fill (docs/B3_GLYPH_ROI_MAP.md).
            "roi_mm": None, "roi_source": "UNSET",
            "shape_class": None, "glyph_label": None, "nominal_h_mm": None,
            "glyph_index": 1, "registration": None,
            "threshold_mm": 3.0,
            "reference_h_mm": None, "reference_method": "TODO",
            # B4: null, not True.  A default-true flatness declaration is exactly
            # how an unsurveyed panel would pass the PLANARITY gate (A-06).
            "declared_flat": None, "flatness_record": None, "angle_deg": None,
            "camera_identity_match": True, "frame_serial_match": True,
            "frame_not_expired": True,
        })
    man = {"frame_cert": "config/frames/FRAME-0001.json",
           "camera_profiles": {"PHONE-A": "config/cameras/PHONE-A.json"},
           "measurand_policy": "config/measurand_policy_v1.json",
           "gate_policy": "config/gate_policy_v1.json",
           "uncertainty_model": "config/uncertainty_model_v1.json",
           "runs": runs}
    dump_json(out, man)
    print("scaffolded %d runs -> %s" % (len(runs), out))
    print("next: record panel_id, glyph_label, nominal_h_mm, glyph_index and the "
          "per-panel registration, then")
    print("      python3 tools/validate_roi_map.py --manifest %s --fill %s"
          % (out, out))
    print("      to COMPUTE roi_mm from the pre-registered glyph map. Do not type "
          "roi_mm by hand.")
    print("      reference_h_mm / reference_method come from the reference table "
          "(blocker B2).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scaffold", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.scaffold:
        scaffold(a.scaffold, a.out)
        return

    man = load_json(a.manifest)
    base = os.path.dirname(os.path.abspath(a.manifest))

    def rel(p):
        return p if os.path.isabs(p) else os.path.join(ROOT, p)

    cert = load_json(rel(man["frame_cert"]))
    mp = load_json(rel(man["measurand_policy"]))
    gp = load_json(rel(man["gate_policy"]))
    um = load_json(rel(man["uncertainty_model"]))
    profiles = {k: load_json(rel(v)) for k, v in man["camera_profiles"].items()}

    os.makedirs(a.out, exist_ok=True)
    if "safety_class" not in CSV_COLUMNS:
        CSV_COLUMNS.append("safety_class")
    for extra in ("panel_id", "operator", "device", "repeat", "angle_deg",
                  "reference_method", "glyph_label"):
        if extra not in CSV_COLUMNS:
            CSV_COLUMNS.append(extra)

    rows = []
    for r in man["runs"]:
        for k in REQUIRED:
            if k not in r:
                sys.exit("run %s missing %s" % (r.get("run_id"), k))
        # B3: roi_mm must be a real, computed ROI.  Refuse placeholders here as
        # well as in tools/validate_roi_map.py, so the pipeline cannot be driven
        # with an unset or stub region even if the validator is skipped.
        roi = r.get("roi_mm")
        if not (isinstance(roi, (list, tuple)) and len(roi) == 4
                and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        for v in roi)
                and roi[2] > 0 and roi[3] > 0):
            sys.exit("run %s: roi_mm must be four positive-sized numbers in "
                     "fiducial-plane mm; compute it with "
                     "tools/validate_roi_map.py --fill (see docs/B3_GLYPH_ROI_MAP.md)"
                     % r.get("run_id"))
        if str(r.get("glyph_label") or "").strip().upper() in ("", "TODO", "NONE"):
            sys.exit("run %s: glyph_label must name the pre-registered glyph"
                     % r.get("run_id"))
        # B4: the PLANARITY gate trusts `declared_flat`, and A-06 shows no gate can
        # see local print-plane tilt.  A default of True would let an unsurveyed
        # panel pass silently, so the flag must be stated and evidenced.
        if not isinstance(r.get("declared_flat"), bool):
            sys.exit("run %s: declared_flat must be stated explicitly (true/false) "
                     "and must come from the panel's flatness record; verify it with "
                     "tools/validate_flatness.py (see docs/B4_FLATNESS_CONTROL.md)"
                     % r.get("run_id"))
        prof = profiles.get(r["device"])
        if prof is None:
            sys.exit("no camera profile for device %s" % r["device"])
        cam = Camera.from_dict(prof["camera"])
        paths = [p if os.path.isabs(p) else os.path.join(base, p)
                 for p in r["frames"]]
        try:
            imgs = [read_png_gray(p) for p in paths]
        except Exception as exc:
            print("SKIP %s: %s" % (r["run_id"], exc))
            continue
        ctx = {"profile_id": prof["profile_id"],
               "z_calib_mm": prof.get("z_calib_mm"),
               "camera_identity_match": r.get("camera_identity_match", True),
               "frame_serial_match": r.get("frame_serial_match", True),
               "frame_not_expired": r.get("frame_not_expired", True),
               "declared_flat": r["declared_flat"],
               "operator": r.get("operator"), "panel_id": r.get("panel_id"),
               "angle_deg": r.get("angle_deg"),
               "reference_method": r.get("reference_method")}
        res = measure_run(imgs, cam, cert, mp, gp, um, tuple(r["roi_mm"]),
                          r["shape_class"], r.get("threshold_mm"), r["run_id"],
                          context=ctx)
        gt = {"true_ink_height_mm": r.get("reference_h_mm"),
              "glyph_shape": r.get("glyph_label"),
              "shape_class": r["shape_class"],
              "design_h_mm": r.get("nominal_h_mm"),
              "pose_tilt_deg": r.get("angle_deg"),
              "safety_class": r.get("safety_class", "SAFE"),
              "reference_method": r.get("reference_method"),
              "source_images": [os.path.basename(p) for p in paths]}
        save_run(os.path.join(a.out, "runs", r["run_id"]), res, extra=gt)
        row = flat_row(res, gt=gt, meta={"fixture_id": r.get("panel_id"),
                                         "experiment": "PHYSICAL_PILOT",
                                         "variant": "base", "source": "real",
                                         "undistort_enabled": cam.has_distortion,
                                         "linearize_enabled": True})
        row.update({"safety_class": gt["safety_class"],
                    "panel_id": r.get("panel_id"), "operator": r.get("operator"),
                    "device": r.get("device"), "repeat": r.get("repeat"),
                    "angle_deg": r.get("angle_deg"),
                    "reference_method": r.get("reference_method"),
                    "glyph_label": r.get("glyph_label")})
        rows.append(row)
        m = res["measurement"]
        if m["h_mm"] is not None:
            ref = r.get("reference_h_mm")
            print("%-22s est=%.4f ref=%s err=%s u_c=%.4f %s"
                  % (r["run_id"], m["h_mm"], ref,
                     ("%+.4f" % (m["h_mm"] - ref)) if ref else "n/a",
                     res["budget"]["u_c_mm"], m["decision"]))
        else:
            print("%-22s ABSTAIN %s gate=%s"
                  % (r["run_id"], res["status"], res["gates"].get("failed_gate")))

    write_csv(os.path.join(a.out, "results.csv"), rows)
    dump_json(os.path.join(a.out, "manifest_used.json"), man)
    print("wrote %d rows -> %s" % (len(rows), a.out))


if __name__ == "__main__":
    main()
