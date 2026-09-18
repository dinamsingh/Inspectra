#!/usr/bin/env python3
"""Turn caliper measurements of a printed frame into a frame certificate.

What is measured (all with a calibrated digital caliper, 10 repeats each):
  --cx-span   distance between the centres of the left and right marker columns
  --cy-span   distance between the centres of the top and bottom marker rows
  --side      mean marker side length
  --thickness frame thickness (the offset between the marker plane and the
              printed surface it is laid on)

Why this is sufficient: the nominal template geometry is known exactly, and the
dominant real error is anisotropic printer scaling, which a two-parameter
(sx, sy) correction captures.  The scale contribution of a caliper survey is
~0.02 mm over a ~100 mm baseline, i.e. ~0.02 percent, which is roughly 300 times
smaller than the P0-min accuracy target -- so a CMM is *not* required here
(PHASE0_REVIEW F2.3).  What a caliper cannot capture is out-of-plane form error;
that is why flatness is a fixture requirement, not a certificate field.

Example:
  python3 tools/survey_frame.py --serial FRAME-0001 \
      --cx-span 80.14 --cy-span 44.07 --side 10.02 --thickness 0.42 \
      --u-span 0.02 --u-side 0.02 --u-thickness 0.01 \
      --instrument "Mitutoyo 500-196-30 (cal 2026-03)" \
      --out config/frames/FRAME-0001.json
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, obj_hash                 # noqa: E402
from make_configs import (FRAME_OUTER, MARKER_CENTRES,  # noqa: E402
                          MARKER_SIDE, WINDOW)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", required=True)
    ap.add_argument("--cx-span", type=float, required=True)
    ap.add_argument("--cy-span", type=float, required=True)
    ap.add_argument("--side", type=float, required=True)
    ap.add_argument("--thickness", type=float, required=True)
    ap.add_argument("--u-span", type=float, default=0.02)
    ap.add_argument("--u-side", type=float, default=0.02)
    ap.add_argument("--u-thickness", type=float, default=0.01)
    ap.add_argument("--instrument", default="UNSPECIFIED")
    ap.add_argument("--flatness-mm", type=float, default=0.10,
                    help="verified peak-to-valley flatness over the window")
    ap.add_argument("--issued", default="")
    ap.add_argument("--expires", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    xs = sorted(set(c[0] for c in MARKER_CENTRES.values()))
    ys = sorted(set(c[1] for c in MARKER_CENTRES.values()))
    nom_cx = xs[-1] - xs[0]
    nom_cy = ys[-1] - ys[0]
    sx = a.cx_span / nom_cx
    sy = a.cy_span / nom_cy
    s_side = a.side / MARKER_SIDE

    markers = {}
    for mid, (cx, cy) in sorted(MARKER_CENTRES.items()):
        CX = cx * sx
        CY = cy * sy
        hx = 0.5 * MARKER_SIDE * s_side
        hy = 0.5 * MARKER_SIDE * s_side
        markers[str(mid)] = {
            "centre_mm": [CX, CY],
            "side_mm": MARKER_SIDE * s_side,
            "corners_mm": [[CX - hx, CY + hy], [CX + hx, CY + hy],
                           [CX + hx, CY - hy], [CX - hx, CY - hy]],
        }

    # Propagate the survey uncertainty to an equivalent per-corner uncertainty.
    u_corner = max(a.u_span / 2.0, a.u_side / 2.0)
    cert = {
        "frame_id": a.serial,
        "serial": a.serial,
        "fiducial_scheme": "NDFID-1",
        "outer_mm": [FRAME_OUTER[0] * sx, FRAME_OUTER[1] * sy],
        "window_mm": [WINDOW[0] * sx, WINDOW[1] * sy],
        "expected_marker_ids": sorted(MARKER_CENTRES),
        "markers": markers,
        "thickness_mm": a.thickness,
        "thickness_u_mm": a.u_thickness,
        "control_point_u_mm": u_corner,
        "flatness_mm": a.flatness_mm,
        "survey_method": "CALIPER_TWO_AXIS_SCALE",
        "survey_instrument": a.instrument,
        "survey_inputs": {"cx_span_mm": a.cx_span, "cy_span_mm": a.cy_span,
                          "side_mm": a.side, "scale_x": sx, "scale_y": sy,
                          "scale_side": s_side},
        "issued_at": a.issued or "UNSET",
        "expires_at": a.expires or "UNSET",
        "limitations": [
            "two-axis scale correction only; no per-corner survey",
            "out-of-plane form error is NOT characterised by this survey",
            "not metrologically traceable unless the caliper certificate is retained",
        ],
    }
    cert["certificate_hash"] = obj_hash(cert)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    dump_json(a.out, cert)
    print("wrote %s" % a.out)
    print("scale_x=%.5f scale_y=%.5f scale_side=%.5f" % (sx, sy, s_side))
    print("implied relative scale error if left uncorrected: x %.3f%%  y %.3f%%"
          % (abs(sx - 1) * 100, abs(sy - 1) * 100))
    print("per-corner survey uncertainty: %.3f mm" % u_corner)


if __name__ == "__main__":
    main()
