#!/usr/bin/env python3
"""Enforce the pre-registered panel -> measured-glyph assignment (blocker B5).

`make_glyph_selection.py` commits *which* glyph each panel contributes.  This tool
refuses anything that quietly measures a different one:

* the committed selection must still be what the allocation rule derives, and every
  selected glyph must resolve in the B3 glyph map;
* the balance invariants of §1.6 must hold (all 5 heights, both shape classes) and
  P2's 3 mm class must actually be populated;
* every **nominal** run must measure its panel's selected glyph -- one panel may not
  contribute two different glyphs, and no run may measure an unselected one;
* the manifest must carry the `selection_hash` it was built against;
* the P1 cross-check subset must be the declared one.

Stress runs are exempt from the glyph rule by design: `P0_EXECUTION_PLAN.md` §1.4
gives them no accuracy expectation, they feed P6 only.

Usage:
    python3 tools/validate_selection.py --manifest manifests/pilot.json
    python3 tools/validate_selection.py --manifest m.json --reference reference/reference_table.csv
Exit code: 0 clean, 1 validation errors, 2 could not load.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from p0.core import load_json                            # noqa: E402
from p0.results import read_csv                          # noqa: E402
from make_coupons_svg import HEIGHTS, SHAPES             # noqa: E402
from make_glyph_map import glyph_key                     # noqa: E402
import make_glyph_selection as mgs                       # noqa: E402

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

DEFAULT_SELECTION = os.path.join(ROOT, "fixtures", "physical", "coupons",
                                 "glyph_selection.json")
DEFAULT_MAP = os.path.join(ROOT, "fixtures", "physical", "coupons",
                           "glyph_map.json")
# `tools/analyse_physical.py` computes P2 on this class and needs >= 2 observations.
P2_CLASS_MM = 3.0
SAFE = "SAFE"

PLACEHOLDERS = frozenset(("", "todo", "tbd", "n/a", "na", "none", "null", "unknown",
                          "unspecified", "?", "-"))


class SelectionError(Exception):
    pass


def named(value):
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def index_selection(selection):
    by_panel, by_key = {}, {}
    for g in selection.get("glyphs") or []:
        pid, key = g.get("panel_id"), g.get("glyph_key")
        if pid in by_panel:
            raise SelectionError("panel %s is selected twice; A-14 measures one "
                                 "glyph per run and §1.1 one glyph per panel" % pid)
        by_panel[pid] = g
        by_key[key] = g
    if not by_panel:
        raise SelectionError("the selection contains no glyphs")
    return by_panel, by_key


def validate(selection, manifest=None, glyph_map=None, reference=None, panels=None):
    issues = []

    def add(sev, code, detail, where=None):
        issues.append({"severity": sev, "code": code, "where": where,
                       "detail": detail})

    by_panel, by_key = index_selection(selection)

    # --- the selection is still the derived one --------------------------
    if panels is not None:
        fresh = mgs.build(panels, glyph_map)
        if fresh != selection:
            add(ERROR, "SELECTION_NOT_DERIVED",
                "the committed selection is not what the allocation rule derives; "
                "committed hash %s vs derived %s"
                % (str(selection.get("selection_hash"))[:16],
                   fresh["selection_hash"][:16]))

    # --- every selected glyph exists in the B3 map -----------------------
    if glyph_map is not None:
        known = {g.get("glyph_key") for g in glyph_map.get("glyphs") or []}
        for key, g in sorted(by_key.items()):
            if key not in known:
                add(ERROR, "SELECTED_GLYPH_NOT_IN_MAP",
                    "%s is selected but does not resolve in the glyph map, so it "
                    "cannot be located at capture time" % key, g.get("panel_id"))
            want = glyph_key(g.get("panel_id"), g.get("glyph_shape"),
                             g.get("nominal_h_mm"), g.get("glyph_index", 1))
            if key != want:
                add(ERROR, "SELECTION_KEY_INCONSISTENT",
                    "glyph_key=%r does not match its own fields (%s)" % (key, want),
                    g.get("panel_id"))
        if (selection.get("glyph_map_hash") is not None
                and selection["glyph_map_hash"] != glyph_map.get("map_hash")):
            add(ERROR, "GLYPH_MAP_HASH_MISMATCH",
                "the selection was built against a different glyph map")

    # --- §1.6 coverage invariants ---------------------------------------
    heights = {g.get("nominal_h_mm") for g in by_panel.values()}
    classes = {g.get("shape_class") for g in by_panel.values()}
    missing_h = sorted(set(float(h) for h in HEIGHTS) - heights)
    if missing_h:
        add(ERROR, "HEIGHT_NOT_COVERED",
            "nominal heights %s are not measured by any panel; §1.6 requires all "
            "five" % missing_h)
    if len(classes) < 2:
        add(ERROR, "SHAPE_CLASS_NOT_COVERED",
            "only shape class(es) %s are measured; §1.6 requires both FLAT_TOP and "
            "ROUND" % sorted(classes))
    n_p2 = sum(1 for g in by_panel.values()
               if abs(float(g.get("nominal_h_mm") or -1) - P2_CLASS_MM) < 1e-9)
    if n_p2 == 0:
        add(ERROR, "P2_CLASS_EMPTY",
            "no panel measures the %.1f mm class, so P2 is UNCOMPUTABLE by "
            "construction" % P2_CLASS_MM)

    # --- the P1 subset ---------------------------------------------------
    sub = selection.get("p1_cross_check_subset") or {}
    sub_keys = list(sub.get("glyph_keys") or [])
    if not sub_keys:
        add(ERROR, "P1_SUBSET_MISSING",
            "the selection declares no P1 cross-check subset")
    else:
        if len(set(sub_keys)) != len(sub_keys):
            add(ERROR, "P1_SUBSET_DUPLICATES",
                "the P1 subset lists a glyph twice")
        minimum = sub.get("minimum_required") or mgs.P1_MIN_GLYPHS
        if len(set(sub_keys)) < minimum:
            add(ERROR, "P1_SUBSET_TOO_SMALL",
                "the P1 subset has %d glyphs; the criterion requires >= %d"
                % (len(set(sub_keys)), minimum))
        not_measured = sorted(set(sub_keys) - set(by_key))
        if not_measured:
            add(WARN, "P1_SUBSET_BEYOND_MEASURED",
                "the P1 subset includes %d glyph(s) that are not camera-measured; "
                "that is allowed, but only the measured ones bound the references "
                "P2/P3/P4 consume" % len(not_measured))
        missed = sorted(set(by_key) - set(sub_keys))
        if missed:
            add(ERROR, "MEASURED_GLYPH_NOT_CROSS_CHECKED",
                "%d camera-measured glyph(s) are absent from the P1 subset, so their "
                "reference values would never be cross-checked: %s"
                % (len(missed), missed[:5]))

    # --- the manifest -----------------------------------------------------
    seen_panel_glyph = {}
    nominal_panels = set()
    if manifest is not None:
        if manifest.get("selection_hash") != selection.get("selection_hash"):
            add(ERROR, "SELECTION_HASH_MISMATCH",
                "the manifest does not record the selection_hash it was built "
                "against (%s); without it a swapped selection is invisible"
                % str(selection.get("selection_hash"))[:16])
        for r in manifest.get("runs") or []:
            rid = r.get("run_id")
            if (r.get("safety_class") or SAFE) != SAFE:
                continue                     # stress runs: §1.4, no accuracy role
            pid = r.get("panel_id")
            if not named(pid):
                add(ERROR, "RUN_WITHOUT_PANEL",
                    "a nominal run must name its panel", rid)
                continue
            nominal_panels.add(pid)
            sel = by_panel.get(pid)
            if sel is None:
                add(ERROR, "PANEL_NOT_SELECTED",
                    "panel %s has a nominal run but no pre-registered glyph" % pid,
                    rid)
                continue
            key = glyph_key(pid, r.get("glyph_label"), r.get("nominal_h_mm"),
                            r.get("glyph_index", 1))
            if key != sel["glyph_key"]:
                add(ERROR, "RUN_MEASURES_UNSELECTED_GLYPH",
                    "run measures %s but panel %s is pre-registered for %s; the "
                    "assignment was fixed before capture and may not be changed"
                    % (key, pid, sel["glyph_key"]), rid)
            seen_panel_glyph.setdefault(pid, set()).add(key)
        for pid, keys in sorted(seen_panel_glyph.items()):
            if len(keys) > 1:
                add(ERROR, "PANEL_MEASURES_TWO_GLYPHS",
                    "panel %s has nominal runs on %d different glyphs (%s); one "
                    "glyph per panel (§1.1)" % (pid, len(keys), sorted(keys)), pid)
        absent = sorted(set(by_panel) - nominal_panels)
        if absent:
            add(WARN, "SELECTED_PANEL_HAS_NO_RUNS",
                "%d selected panel(s) have no nominal run yet: %s"
                % (len(absent), absent[:5]))

    # --- the reference table ---------------------------------------------
    if reference is not None:
        have = set()
        for row in reference:
            have.add(glyph_key(row.get("panel_id"), row.get("glyph_shape"),
                               row.get("nominal_h_mm"), row.get("glyph_index", 1)))
        for key in sorted(set(sub_keys)):
            if key not in have:
                add(WARN, "P1_SUBSET_NOT_IN_REFERENCE_TABLE",
                    "%s is in the P1 subset but has no reference row yet; producing "
                    "those values is blocker B2" % key)

    summary = {
        "selection_hash": selection.get("selection_hash"),
        "panels_selected": len(by_panel),
        "p1_subset_n": len(set(sub_keys)),
        "p2_class_panels": n_p2,
        "p2_class_mm": P2_CLASS_MM,
        "heights_covered": sorted(heights),
        "shape_classes_covered": sorted(classes),
        "balance": selection.get("balance"),
        "nominal_panels_in_manifest": len(nominal_panels),
        "issues": {sev: sum(1 for i in issues if i["severity"] == sev)
                   for sev in (ERROR, WARN, INFO)},
    }
    return issues, summary


def report(issues, summary, out=None):
    out = out or sys.stdout
    for k in sorted(summary):
        if k != "issues":
            out.write("  %-30s %s\n" % (k, summary[k]))
    out.write("  issues: %s\n" % summary["issues"])
    for i in issues:
        out.write("  [%s] %-38s %s%s\n"
                  % (i["severity"], i["code"],
                     ("%s " % i["where"]) if i["where"] else "", i["detail"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selection", default=DEFAULT_SELECTION)
    ap.add_argument("--map", default=DEFAULT_MAP)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--reference", default=None)
    ap.add_argument("--no-rederive", action="store_true",
                    help="skip re-deriving the selection from panels.json")
    a = ap.parse_args(argv)

    try:
        selection = load_json(a.selection)
        gmap = load_json(a.map) if os.path.exists(a.map) else None
        man = load_json(a.manifest) if a.manifest else None
        ref = read_csv(a.reference) if a.reference else None
        panels = None if a.no_rederive else mgs.load_panels()
    except Exception as exc:                                    # noqa: BLE001
        sys.stderr.write("SELECTION REJECTED: %s\n" % exc)
        return 2

    try:
        issues, summary = validate(selection, man, gmap, ref, panels)
    except SelectionError as exc:
        sys.stderr.write("SELECTION REJECTED: %s\n" % exc)
        return 2

    sys.stdout.write("selection: %s\n" % a.selection)
    report(issues, summary)
    n_err = summary["issues"][ERROR]
    sys.stdout.write("VERDICT: %s\n"
                     % ("ACCEPTED" if n_err == 0
                        else "REJECTED (%d errors)" % n_err))
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
