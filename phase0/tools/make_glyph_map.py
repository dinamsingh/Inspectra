#!/usr/bin/env python3
"""Derive the pre-registered glyph map for the printed coupons (blocker B3).

**Nothing here is invented.**  Every coordinate is recomputed from the two pieces
of committed code that already determine it:

* `tools/make_coupons_svg.py` -- `HEIGHTS`, `SHAPES`, `COUPON`, and the row/column
  stepping inside `coupon()`, which is what actually places ink on paper;
* `p0.render.glyph_bbox_mm` -- the glyph bounding box, which is the same function
  the synthetic suite uses to build `roi_mm`
  (`tests/test_p0.py`: `roi = glyph_center_mm + glyph_bbox_mm`).

Per-panel height order comes from `fixtures/physical/coupons/panels.json`, because
`make_coupons_svg.py` staggers it (`HEIGHTS` reversed on odd panels) and the row
pitch depends on that order.

Coordinate convention, stated once and used everywhere:

    PANEL-LOCAL  origin at the coupon's top-left corner, +x right, +y DOWN.
                 This is the SVG convention the coupon generator draws in.
    FIDUCIAL     origin at the frame centre, +x right, +y UP.  This is what
                 `roi_mm` means to `p0.measure` and it is NOT the panel frame.

The map is deliberately in *panel-local* millimetres.  The panel -> fiducial
transform is a property of one physical mounting, is measured at capture time, and
lives in the run manifest -- see `docs/B3_GLYPH_ROI_MAP.md` §3.

Usage:
    python3 tools/make_glyph_map.py --out fixtures/physical/coupons/glyph_map.json
    python3 tools/make_glyph_map.py --check fixtures/physical/coupons/glyph_map.json
Exit code: 0 ok, 1 the committed map does not match a fresh derivation.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from p0.core import dump_json, load_json, obj_hash       # noqa: E402
from p0.render import glyph_bbox_mm, glyph_shape_class   # noqa: E402
from make_coupons_svg import COUPON, HEIGHTS, SHAPES     # noqa: E402

SCHEMA_VERSION = "GLYPH_MAP-1"

# The map records the *nominal artwork* box, i.e. zero ink spread.  Real print
# gain makes the ink taller, which is why the ROI has vertical headroom: the
# scan reaches 0.725*roi_h either side of the centre (p0/measure.py `span_n`),
# so an ink spread below 0.225*h is still fully enclosed.
MAP_INK_SPREAD_MM = 0.0


def row_pitch_mm(h):
    """Vertical step after a height row -- `coupon()`: max(h * 1.9, 7.0)."""
    return max(h * 1.9, 7.0)


def col_pitch_mm(h):
    """Horizontal step between shapes -- `coupon()`: max(1.2 * h, 4.0) + 2.0."""
    return max(1.2 * h, 4.0) + 2.0


def panel_layout(heights):
    """Replicate `coupon()` exactly: (shape, h, panel_x, panel_y) in mm, y DOWN."""
    out = []
    yy = 14.0                      # `coupon()`: yy = y0 + 14.0
    for h in heights:
        xx = 8.0                   # `coupon()`: xx = x0 + 8.0
        for shape in SHAPES:
            out.append((shape, h, xx, yy))
            xx += col_pitch_mm(h)
        yy += row_pitch_mm(h)
    return out


def glyph_key(panel_id, shape, nominal_h_mm, glyph_index):
    """Same canonical form as the reference table (P0_REFERENCE_PROCEDURE.md §6)."""
    return "%s:%s:%.2f:%d" % (panel_id, shape, float(nominal_h_mm), int(glyph_index))


def roi_tolerance_mm(roi_w, roi_h):
    """Largest ROI-centre error the *existing* pipeline can still measure through.

    Derived, not invented, from two committed sources:

    * `p0/measure.py`: scanlines are placed at +/- 0.4 * roi_w about the centre
      (`half_t = 0.5 * w * 0.80`) and each profile reaches +/- 0.725 * roi_h
      (`span_n = 0.5 * h * 1.45`);
    * `config/gate_policy_v1.json`: `min_scanline_fraction = 0.5`.

    Perpendicular to the baseline the profile must still contain both edges:
    0.725 * h - 0.5 * h = 0.225 * h.  Along the baseline at least half the
    scanlines must still fall on ink, which fails once the centre error reaches
    half the ink width.  The binding figure is the smaller of the two.

    This is an UPPER bound.  A measured check on a 1.2 mm `BAR_I` abstained at a
    0.20 mm perpendicular offset, i.e. earlier than 0.225 * h would allow, so the
    registration must aim at zero and never at this bound.
    """
    return min(0.5 * roi_w, 0.225 * roi_h)


def build(panels):
    glyphs = []
    for panel in panels:
        pid = panel["panel_id"]
        heights = [float(h) for h in panel["nominal_heights_mm"]]
        for shape, h, px, py in panel_layout(heights):
            w, hh = glyph_bbox_mm(shape, h, MAP_INK_SPREAD_MM)
            glyphs.append({
                "glyph_key": glyph_key(pid, shape, h, 1),
                "panel_id": pid,
                "sheet": panel.get("sheet"),
                "font": panel.get("font"),
                "glyph_shape": shape,
                "shape_class": glyph_shape_class(shape),
                "nominal_h_mm": round(h, 6),
                "glyph_index": 1,
                "panel_x_mm": round(px, 6),
                "panel_y_mm": round(py, 6),
                "roi_w_mm": round(w, 6),
                "roi_h_mm": round(hh, 6),
                "roi_tolerance_mm": round(roi_tolerance_mm(w, hh), 6),
                "measurement_orientation": "PERPENDICULAR_TO_FITTED_BASELINE",
            })
    glyphs.sort(key=lambda g: (g["panel_id"], g["nominal_h_mm"], g["glyph_shape"]))
    body = {
        "schema_version": SCHEMA_VERSION,
        "note": ("Pre-registered glyph map.  Panel-local millimetres, origin at the "
                 "coupon top-left corner, +x right, +y DOWN (SVG convention).  These "
                 "are NOT roi_mm values: roi_mm is in fiducial-plane millimetres and "
                 "is computed per mounting by tools/validate_roi_map.py."),
        "derived_from": ["tools/make_coupons_svg.py", "p0/render.py:glyph_bbox_mm",
                         "fixtures/physical/coupons/panels.json"],
        "prohibition": ("nominal_h_mm is a print instruction only and may never be "
                        "used as a reference value (P0_EXECUTION_PLAN.md §2.2)"),
        "coupon_size_mm": list(COUPON),
        "map_ink_spread_mm": MAP_INK_SPREAD_MM,
        "heights_mm": list(HEIGHTS),
        "shapes": list(SHAPES),
        "n_glyphs": len(glyphs),
        "glyphs": glyphs,
    }
    body["map_hash"] = obj_hash(body)
    return body


def default_panels_path():
    return os.path.join(ROOT, "fixtures", "physical", "coupons", "panels.json")


def load_panels(path=None):
    data = load_json(path or default_panels_path())
    panels = data.get("panels")
    if not panels:
        raise SystemExit("panels.json contains no panels")
    return panels


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--panels", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", default=None,
                    help="verify a committed map matches a fresh derivation")
    a = ap.parse_args(argv)

    fresh = build(load_panels(a.panels))

    if a.check:
        have = load_json(a.check)
        if have == fresh:
            print("glyph map matches a fresh derivation: %d glyphs, hash %s"
                  % (fresh["n_glyphs"], fresh["map_hash"][:16]))
            return 0
        print("GLYPH MAP MISMATCH: the committed map is not what the current "
              "generator derives")
        print("  committed hash: %s" % have.get("map_hash"))
        print("  derived   hash: %s" % fresh["map_hash"])
        return 1

    if not a.out:
        ap.error("one of --out or --check is required")
    dump_json(a.out, fresh)
    print("glyph map written: %s" % a.out)
    print("  %d glyphs, %d panels, hash %s"
          % (fresh["n_glyphs"],
             len({g["panel_id"] for g in fresh["glyphs"]}), fresh["map_hash"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
