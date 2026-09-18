#!/usr/bin/env python3
"""Emit a printable 1:1 SVG template of the NDFID-1 fiducial frame.

Print at exactly 100% scale on dimensionally stable stock (polyester film or a
film label applied to rigid board / acrylic).  The printed geometry is only the
*nominal* geometry -- it must then be surveyed with `tools/survey_frame.py`,
because printer scaling of 0.2 to 1 percent is normal and is the dominant
reference error if it is left unmeasured.

Usage:  python3 tools/make_frame_svg.py [--out fixtures/physical/FRAME-0001.svg]
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.fiducial import CELLS, marker_bit_grid          # noqa: E402
from make_configs import (FRAME_OUTER, MARKER_CENTRES,  # noqa: E402
                          MARKER_SIDE, WINDOW)

MARGIN = 10.0


def build(serial="FRAME-0001"):
    W = FRAME_OUTER[0] + 2 * MARGIN
    H = FRAME_OUTER[1] + 2 * MARGIN

    def X(x_mm):
        return x_mm + FRAME_OUTER[0] / 2.0 + MARGIN

    def Y(y_mm):
        return FRAME_OUTER[1] / 2.0 - y_mm + MARGIN

    s = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%.3fmm" height="%.3fmm" '
         'viewBox="0 0 %.3f %.3f">' % (W, H, W, H),
         '<rect width="%.3f" height="%.3f" fill="white"/>' % (W, H),
         '<!-- NDFID-1 fiducial frame, nominal geometry in millimetres -->']
    s.append('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="none" '
             'stroke="black" stroke-width="0.15"/>'
             % (X(-FRAME_OUTER[0] / 2), Y(FRAME_OUTER[1] / 2),
                FRAME_OUTER[0], FRAME_OUTER[1]))
    s.append('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="none" '
             'stroke="black" stroke-width="0.15" stroke-dasharray="2,1.5"/>'
             % (X(-WINDOW[0] / 2), Y(WINDOW[1] / 2), WINDOW[0], WINDOW[1]))

    cell = MARKER_SIDE / CELLS
    for mid, (cx, cy) in sorted(MARKER_CENTRES.items()):
        grid = marker_bit_grid(mid)
        x0 = cx - MARKER_SIDE / 2.0
        y1 = cy + MARKER_SIDE / 2.0
        for r in range(CELLS):
            for c in range(CELLS):
                if grid[r][c]:
                    s.append('<rect x="%.4f" y="%.4f" width="%.4f" height="%.4f" '
                             'fill="black" stroke="none" shape-rendering="crispEdges"/>'
                             % (X(x0 + c * cell), Y(y1 - r * cell), cell, cell))
        s.append('<text x="%.3f" y="%.3f" font-size="2.2" font-family="monospace" '
                 'text-anchor="middle">id%d</text>'
                 % (X(cx), Y(cy - MARKER_SIDE / 2.0 - 1.4), mid))

    # scale-verification bars: measure these after printing
    s.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="black" '
             'stroke-width="0.12"/>'
             % (X(-50), Y(-FRAME_OUTER[1] / 2 + 3.0), X(50),
                Y(-FRAME_OUTER[1] / 2 + 3.0)))
    for x in (-50.0, 0.0, 50.0):
        s.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="black" '
                 'stroke-width="0.12"/>'
                 % (X(x), Y(-FRAME_OUTER[1] / 2 + 3.0),
                    X(x), Y(-FRAME_OUTER[1] / 2 + 5.0)))
    s.append('<text x="%.3f" y="%.3f" font-size="2.4" font-family="monospace" '
             'text-anchor="middle">100.000 mm nominal check bar</text>'
             % (X(0), Y(-FRAME_OUTER[1] / 2 + 6.6)))
    s.append('<text x="%.3f" y="%.3f" font-size="2.6" font-family="monospace">'
             '%s  NDFID-1  outer %.1fx%.1f mm  marker %.1f mm  window %.1fx%.1f mm'
             '</text>' % (X(-FRAME_OUTER[0] / 2), Y(FRAME_OUTER[1] / 2 + 3.2),
                          serial, FRAME_OUTER[0], FRAME_OUTER[1], MARKER_SIDE,
                          WINDOW[0], WINDOW[1]))
    s.append('<text x="%.3f" y="%.3f" font-size="2.1" font-family="monospace" '
             'fill="#444">print at 100%% scale, then SURVEY before use</text>'
             % (X(-FRAME_OUTER[0] / 2), Y(-FRAME_OUTER[1] / 2 - 2.0)))
    s.append("</svg>")
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", default="FRAME-0001")
    ap.add_argument("--out", default=os.path.join(ROOT, "fixtures", "physical",
                                                  "FRAME-0001.svg"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(build(a.serial) + "\n")
    print("wrote", a.out)
    print("cut out the dashed window; the printed surface must sit flush on the "
          "measured face, and the frame thickness must be entered in the "
          "certificate (tools/survey_frame.py)")


if __name__ == "__main__":
    main()
