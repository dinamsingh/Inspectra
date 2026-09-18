#!/usr/bin/env python3
"""Emit printable 1:1 coupon sheets for the 20-panel physical pilot.

Each coupon carries the same four geometric glyph primitives used by the
synthetic renderer (BAR_I, H, T, RING_O) drawn at exact nominal millimetre
heights, plus one real-font text line for realism.

Important: the nominal height printed here is NOT ground truth.  Printer scaling
and ink spread change the real ink extent, so every coupon glyph must be measured
by the reference method (scanner / measuring microscope) as described in
docs/P0_PROTOCOL.md.

Usage: python3 tools/make_coupons_svg.py --out fixtures/physical/coupons
"""
from __future__ import annotations

import argparse
import os

HEIGHTS = (1.2, 2.0, 3.0, 4.0, 6.0)
SHAPES = ("BAR_I", "H", "T", "RING_O")
FONTS = ("DejaVu Sans", "DejaVu Serif", "DejaVu Sans Mono", "Helvetica")
SHEET = (210.0, 297.0)          # A4 portrait, millimetres
COUPON = (95.0, 55.0)
MARGIN = 8.0


def glyph_paths(shape, h, x, y):
    """Draw a glyph of exact ink height `h` mm with its centre at (x, y)."""
    out = []

    def rect(cx, cy, w, hh):
        out.append('<rect x="%.4f" y="%.4f" width="%.4f" height="%.4f" '
                   'fill="black" shape-rendering="crispEdges"/>'
                   % (x + cx - w / 2, y + cy - hh / 2, w, hh))

    if shape == "BAR_I":
        rect(0, 0, 0.18 * h, h)
    elif shape == "H":
        rect(-0.32 * h, 0, 0.16 * h, h)
        rect(0.32 * h, 0, 0.16 * h, h)
        rect(0, 0, 0.64 * h, 0.15 * h)
    elif shape == "T":
        rect(0, -0.425 * h, 0.80 * h, 0.15 * h)
        rect(0, 0, 0.16 * h, h)
    elif shape == "RING_O":
        a, b, t = 0.35 * h, 0.5 * h, 0.13 * h
        out.append('<ellipse cx="%.4f" cy="%.4f" rx="%.4f" ry="%.4f" fill="none" '
                   'stroke="black" stroke-width="%.4f"/>'
                   % (x, y, a - t / 2, b - t / 2, t))
    return out


def coupon(panel_id, x0, y0, heights, font):
    s = ['<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" fill="none" '
         'stroke="#bbb" stroke-width="0.1"/>' % (x0, y0, COUPON[0], COUPON[1])]
    s.append('<text x="%.3f" y="%.3f" font-size="3" font-family="monospace">'
             'panel %s | font %s</text>' % (x0 + 3, y0 + 5, panel_id, font))
    yy = y0 + 14.0
    for h in heights:
        xx = x0 + 8.0
        s.append('<text x="%.3f" y="%.3f" font-size="2.4" font-family="monospace" '
                 'fill="#555">%.1f</text>' % (x0 + 2.5, yy + 1.0, h))
        for shape in SHAPES:
            s += glyph_paths(shape, h, xx, yy)
            xx += max(1.2 * h, 4.0) + 2.0
        s.append('<text x="%.3f" y="%.3f" font-size="%.4f" font-family="%s">'
                 'MRP 45 NET 200g</text>' % (xx + 2.0, yy + 0.36 * h, h * 1.38, font))
        yy += max(h * 1.9, 7.0)
    s.append('<text x="%.3f" y="%.3f" font-size="2.1" font-family="monospace" '
             'fill="#777">nominal heights only - measure with the reference '
             'method</text>' % (x0 + 3, y0 + COUPON[1] - 2.5))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panels", type=int, default=20)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "fixtures", "physical", "coupons"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    per_sheet = 4
    manifest = []
    sheet_no = 0
    while sheet_no * per_sheet < a.panels:
        body = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="%.1fmm" '
                'height="%.1fmm" viewBox="0 0 %.1f %.1f">'
                % (SHEET[0], SHEET[1], SHEET[0], SHEET[1]),
                '<rect width="%.1f" height="%.1f" fill="white"/>' % SHEET]
        for k in range(per_sheet):
            idx = sheet_no * per_sheet + k
            if idx >= a.panels:
                break
            pid = "P%02d" % (idx + 1)
            font = FONTS[idx % len(FONTS)]
            # stagger the height sets so each panel is not identical
            heights = HEIGHTS if idx % 2 == 0 else tuple(reversed(HEIGHTS))
            x0 = MARGIN + (k % 2) * (COUPON[0] + 4.0)
            y0 = MARGIN + (k // 2) * (COUPON[1] + 6.0)
            body += coupon(pid, x0, y0, heights, font)
            manifest.append({"panel_id": pid, "sheet": sheet_no + 1,
                             "font": font, "nominal_heights_mm": list(heights),
                             "shapes": list(SHAPES)})
        body.append('<text x="%.1f" y="%.1f" font-size="3" font-family="monospace">'
                    'P0-min coupon sheet %d - print at 100%% scale, mount flat'
                    '</text>' % (MARGIN, SHEET[1] - 6, sheet_no + 1))
        body.append("</svg>")
        path = os.path.join(a.out, "coupons_sheet%02d.svg" % (sheet_no + 1))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(body) + "\n")
        print("wrote", path)
        sheet_no += 1

    import json
    with open(os.path.join(a.out, "panels.json"), "w", encoding="utf-8") as fh:
        json.dump({"panels": manifest, "note":
                   "nominal geometry only; reference measurement required"},
                  fh, indent=2, sort_keys=True)
    print("wrote", os.path.join(a.out, "panels.json"))


if __name__ == "__main__":
    main()
