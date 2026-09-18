#!/usr/bin/env python3
"""Generate the deterministic P0-min configuration set.

Creates:
  config/frames/FRAME-SYN-0001.json     synthetic fiducial frame certificate
  config/cameras/CAM-SYN-A.json         synthetic camera profile
  config/measurand_policy_v1.json
  config/gate_policy_v1.json
  config/uncertainty_model_v1.json      (uncalibrated by design)

The physical frame that the printable template produces (tools/make_frame_svg.py)
uses the same geometry, so the same certificate schema applies once the real
frame has been surveyed.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, obj_hash          # noqa: E402
from p0.gates import default_gate_policy          # noqa: E402
from p0.uncertainty import default_model          # noqa: E402

# --- frame geometry (millimetres, origin at frame centre, X right, Y up) ---
FRAME_OUTER = (100.0, 60.0)
MARKER_SIDE = 10.0
MARKER_CENTRES = {0: (-40.0, 22.0), 1: (40.0, 22.0), 2: (40.0, -22.0), 3: (-40.0, -22.0)}
WINDOW = (50.0, 20.0)


def frame_cert(serial="FRAME-SYN-0001", thickness_mm=0.0, thickness_u_mm=0.01,
               control_u_mm=0.02, survey_method="SYNTHETIC_EXACT"):
    markers = {}
    h = MARKER_SIDE / 2.0
    for mid, (cx, cy) in MARKER_CENTRES.items():
        markers[str(mid)] = {
            "centre_mm": [cx, cy],
            "side_mm": MARKER_SIDE,
            # order: TL, TR, BR, BL in plane coordinates (Y up)
            "corners_mm": [[cx - h, cy + h], [cx + h, cy + h],
                           [cx + h, cy - h], [cx - h, cy - h]],
        }
    cert = {
        "frame_id": serial,
        "serial": serial,
        "fiducial_scheme": "NDFID-1",
        "outer_mm": list(FRAME_OUTER),
        "window_mm": list(WINDOW),
        "expected_marker_ids": sorted(MARKER_CENTRES),
        "markers": markers,
        "thickness_mm": thickness_mm,
        "thickness_u_mm": thickness_u_mm,
        "control_point_u_mm": control_u_mm,
        "survey_method": survey_method,
        "survey_instrument": "N/A (synthetic)",
        "issued_at": "2026-09-18",
        "expires_at": "2027-09-18",
    }
    cert["certificate_hash"] = obj_hash(cert)
    return cert


def camera_profile(profile_id="CAM-SYN-A", rho_at_z=18.0, z_mm=200.0,
                   width=1728, height=1056, dist=(0.0, 0.0, 0.0, 0.0, 0.0)):
    f_px = rho_at_z * z_mm
    prof = {
        "profile_id": profile_id,
        "device_model": "SYNTHETIC",
        "physical_camera_id": "0",
        "resolution": [width, height],
        "af_mode": "LOCKED",
        "ois_state": "OFF",
        "camera": {"fx": f_px, "fy": f_px, "cx": width / 2.0, "cy": height / 2.0,
                   "dist": list(dist), "width": width, "height": height},
        "K_cov": None,
        "reproj_holdout_rms_px": None,
        "z_calib_mm": z_mm,
        "z_calib_range_mm": [0.6 * z_mm, 1.8 * z_mm],
        "issued_at": "2026-09-18",
        "expires_at": "2027-09-18",
        "notes": "synthetic profile; intrinsics are exact by construction",
    }
    prof["profile_hash"] = obj_hash(prof)
    return prof


def measurand_policy():
    p = {
        "policy_id": "MP-v1",
        "measurand": "VISIBLE_PRINTED_INK_EXTENT_PERPENDICULAR_TO_BASELINE",
        "measurand_note": ("Reports ink extent at the 50 percent linearised "
                           "luminance boundary. This is NOT a statutory "
                           "character height and NOT a nominal font size."),
        "linearization": "SRGB_EOTF",
        "boundary_fraction": 0.50,
        "sensitivity_fractions": [0.40, 0.60],
        "scanlines": 24,
        "apex_fit_window_frac": 0.35,
        "estimator": "FITTED_EXTREME_MODEL",
        "estimator_note": "max-minus-min retained only as a diagnostic",
        "shape_classes": {"FLAT_TOP": ["BAR_I", "H", "T", "E", "I", "1", "7"],
                          "ROUND": ["RING_O", "O", "0", "8", "S"]},
        "excluded_glyph_features": ["ACCENT", "DOT", "DESCENDER", "PUNCTUATION"],
        "aggregation": "MIN_ELIGIBLE_GLYPH",
        "sampling_mode": "IMAGE_LINE_BILINEAR",
    }
    p["policy_hash"] = obj_hash(p)
    return p


def main():
    cfg = os.path.join(ROOT, "config")
    os.makedirs(os.path.join(cfg, "frames"), exist_ok=True)
    os.makedirs(os.path.join(cfg, "cameras"), exist_ok=True)

    dump_json(os.path.join(cfg, "frames", "FRAME-SYN-0001.json"), frame_cert())
    dump_json(os.path.join(cfg, "frames", "FRAME-SYN-0002-THICK.json"),
              frame_cert("FRAME-SYN-0002-THICK", thickness_mm=0.45))
    dump_json(os.path.join(cfg, "cameras", "CAM-SYN-A.json"), camera_profile())
    dump_json(os.path.join(cfg, "cameras", "CAM-SYN-A-DIST.json"),
              camera_profile("CAM-SYN-A-DIST", dist=(-0.09, 0.03, 0.0005, -0.0004, 0.0)))
    # Larger sensor so the sampling-density sweep can also probe above 18 px/mm
    # while keeping the whole fiducial frame inside the image.
    dump_json(os.path.join(cfg, "cameras", "CAM-SYN-B-HIRES.json"),
              camera_profile("CAM-SYN-B-HIRES", rho_at_z=24.0, width=2304,
                             height=1408))
    dump_json(os.path.join(cfg, "measurand_policy_v1.json"), measurand_policy())

    gp = default_gate_policy()
    gp["policy_hash"] = obj_hash(gp)
    dump_json(os.path.join(cfg, "gate_policy_v1.json"), gp)

    um = default_model()
    dump_json(os.path.join(cfg, "uncertainty_model_v1.json"), um)
    print("configs written to", cfg)


if __name__ == "__main__":
    main()
