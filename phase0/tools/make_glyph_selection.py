#!/usr/bin/env python3
"""Pre-register WHICH glyph each panel contributes to the pilot (blocker B5).

B3 settled *how* a glyph is located; B5 settles *which* glyphs the camera measures.
`P0_ASSUMPTIONS.md` **A-14** measures one glyph per run, so only **20** of the 400
glyph instances are ever camera-measured (`P0_EXECUTION_PLAN.md` §1.1), and the
choice decides what the accuracy statistics can cover at all — including whether
P2's 3 mm class has data (`tools/analyse_physical.py` says so in its own
`UNCOMPUTABLE` message, naming B5).

The frozen constraint (`P0_EXECUTION_PLAN.md` §1.6) is that the assignment must be
committed **before the first capture**, must cover all 5 nominal heights and both
shape classes, and must never change afterwards.

The allocation is a **complete 5 x 4 factorial with one panel per cell**, generated
from a closed form rather than chosen panel by panel:

    f = (i - 1) mod 4          # font group; panels.json assigns fonts by i mod 4
    p = (i - 1) div 4          # position within the font group (= sheet - 1)
    c = (p + f) mod 5          # height class
    nominal_h = HEIGHTS[c]
    glyph_shape = SHAPES[(f + c) mod 4]

which yields, and `tests/test_glyph_selection.py` asserts, every one of:

* each of the 5 nominal heights on exactly 4 panels;
* each of the 4 shapes on exactly 5 panels; both shape classes present;
* each of the 4 fonts on exactly 5 panels;
* all 20 (height, shape) pairs distinct -- a complete factorial;
* all 20 (font, height) pairs distinct -- font and height fully crossed.

Why balanced rather than weighted towards the 3 mm class: see
`docs/B5_GLYPH_SELECTION.md` §3.  The short version is that the selection is fixed
before any data exists, so it cannot know which height will be difficult, and §1.6's
constraint is about coverage.

Usage:
    python3 tools/make_glyph_selection.py --out fixtures/physical/coupons/glyph_selection.json
    python3 tools/make_glyph_selection.py --check fixtures/physical/coupons/glyph_selection.json
Exit code: 0 ok, 1 the committed selection is not what the current rule derives.
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
from p0.render import glyph_shape_class                  # noqa: E402
from make_coupons_svg import HEIGHTS, SHAPES             # noqa: E402
from make_glyph_map import glyph_key, load_panels        # noqa: E402

SCHEMA_VERSION = "GLYPH_SELECTION-1"
GLYPH_MAP = os.path.join(ROOT, "fixtures", "physical", "coupons", "glyph_map.json")

ROLE_NOMINAL = "NOMINAL_MEASURED"
# `P0_CRITERIA.md` P1 requires >= 15 cross-checked glyphs spanning heights, shapes and
# fonts.  The 20 measured glyphs satisfy that on their own, which is why the subset is
# defined as exactly them -- see docs/B5_GLYPH_SELECTION.md §4.
P1_MIN_GLYPHS = 15


def allocate(n_panels=20):
    """The closed-form allocation.  Returns [(index, height, shape), ...]."""
    out = []
    for i in range(1, n_panels + 1):
        f = (i - 1) % len(SHAPES)
        p = (i - 1) // len(SHAPES)
        c = (p + f) % len(HEIGHTS)
        out.append((i, HEIGHTS[c], SHAPES[(f + c) % len(SHAPES)]))
    return out


def build(panels, glyph_map=None):
    selected = []
    for (i, h, shape) in allocate(len(panels)):
        panel = panels[i - 1]
        pid = panel["panel_id"]
        if h not in [float(v) for v in panel["nominal_heights_mm"]]:
            raise SystemExit("panel %s does not print a %.1f mm row" % (pid, h))
        if shape not in panel["shapes"]:
            raise SystemExit("panel %s does not print shape %s" % (pid, shape))
        selected.append({
            "glyph_key": glyph_key(pid, shape, h, 1),
            "panel_id": pid,
            "sheet": panel.get("sheet"),
            "font": panel.get("font"),
            "nominal_h_mm": round(float(h), 6),
            "glyph_shape": shape,
            "shape_class": glyph_shape_class(shape),
            "glyph_index": 1,
            "role": ROLE_NOMINAL,
        })
    selected.sort(key=lambda g: g["panel_id"])

    keys = [g["glyph_key"] for g in selected]
    body = {
        "schema_version": SCHEMA_VERSION,
        "note": ("Pre-registered panel -> measured-glyph assignment.  One glyph per "
                 "panel (A-14), committed before the first capture and never changed "
                 "afterwards (P0_EXECUTION_PLAN.md §1.6)."),
        "derived_from": ["tools/make_coupons_svg.py",
                         "fixtures/physical/coupons/panels.json",
                         "p0/render.py:glyph_shape_class"],
        "allocation_rule": ("f=(i-1) mod 4; p=(i-1) div 4; c=(p+f) mod 5; "
                            "nominal_h=HEIGHTS[c]; shape=SHAPES[(f+c) mod 4]"),
        "prohibition": ("nominal_h_mm is a print instruction only and may never be "
                        "used as a reference value (P0_EXECUTION_PLAN.md §2.2). "
                        "Choosing or changing this assignment after seeing any "
                        "measured value is post-hoc selection."),
        "n_panels": len(selected),
        "p1_cross_check_subset": {
            "glyph_keys": list(keys),
            "n": len(keys),
            "minimum_required": P1_MIN_GLYPHS,
            "rationale": ("P1 must bound the reference values that P2/P3/P4 actually "
                          "consume, so the cross-check subset is exactly the "
                          "camera-measured glyphs. 20 >= 15, and it spans all 5 "
                          "heights, all 4 shapes, both shape classes and all 4 fonts "
                          "by construction (docs/B5_GLYPH_SELECTION.md §4)."),
        },
        "balance": balance(selected),
        "glyphs": selected,
    }
    if glyph_map is not None:
        body["glyph_map_hash"] = glyph_map.get("map_hash")
    body["selection_hash"] = obj_hash(body)
    return body


def balance(selected):
    def tally(key):
        out = {}
        for g in selected:
            out[str(g[key])] = out.get(str(g[key]), 0) + 1
        return dict(sorted(out.items()))
    return {
        "by_nominal_h_mm": tally("nominal_h_mm"),
        "by_glyph_shape": tally("glyph_shape"),
        "by_shape_class": tally("shape_class"),
        "by_font": tally("font"),
        "distinct_height_shape_pairs": len({(g["nominal_h_mm"], g["glyph_shape"])
                                            for g in selected}),
        "distinct_font_height_pairs": len({(g["font"], g["nominal_h_mm"])
                                           for g in selected}),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--panels", default=None)
    ap.add_argument("--map", default=GLYPH_MAP)
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", default=None)
    a = ap.parse_args(argv)

    gmap = load_json(a.map) if os.path.exists(a.map) else None
    fresh = build(load_panels(a.panels), gmap)

    if a.check:
        have = load_json(a.check)
        if have == fresh:
            print("selection matches a fresh derivation: %d panels, hash %s"
                  % (fresh["n_panels"], fresh["selection_hash"][:16]))
            return 0
        print("SELECTION MISMATCH: the committed assignment is not what the rule "
              "derives")
        print("  committed hash: %s" % have.get("selection_hash"))
        print("  derived   hash: %s" % fresh["selection_hash"])
        return 1

    if not a.out:
        ap.error("one of --out or --check is required")
    dump_json(a.out, fresh)
    print("glyph selection written: %s" % a.out)
    for k, v in fresh["balance"].items():
        print("  %-28s %s" % (k, v))
    print("  %-28s %s" % ("selection_hash", fresh["selection_hash"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
