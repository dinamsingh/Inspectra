#!/usr/bin/env python3
"""Compute and validate `roi_mm` from the pre-registered glyph map (blocker B3).

`roi_mm` is `(cx, cy, w, h)` in **fiducial-plane millimetres** -- the frame's own
coordinate system, origin at the frame centre, +x right, +y up.  It is consumed by
`p0.pipeline.process_frame` -> `p0.measure.measure_glyph` and by
`tools/run_real_batch.py`.  Nothing in that chain changes here.

What this tool adds is that `roi_mm` is **computed, never typed**:

    roi_mm  =  f( glyph_map[panel_id, shape, nominal_h, glyph_index],
                  registration(panel mounting) )

The glyph map is committed before capture and derived from the coupon generator
(`tools/make_glyph_map.py`).  The registration is two caliper readings of one
physical mounting.  Neither input can be influenced by a measured height, so no
post-hoc glyph choice is possible.

Registration record, per panel mounting (fiducial-plane mm):

    "registration": {
      "corner_top_left_mm":  [x, y],   # coupon corner beside the printed panel label
      "corner_top_right_mm": [x, y],   # the same coupon edge, other end
      "u_mm": 0.02,                    # caliper survey uncertainty, as in §1 step 4
      "top_left_identified_by": "PANEL_LABEL_TEXT",
      "method": "CALIPER_TWO_POINT", "operator": "...", "measured_at": "..."
    }

Two points, not one, because rotation matters: a mounting rotated by theta moves a
glyph at lever arm r by r * theta, and for the smallest glyph the whole ROI budget
is 0.108 mm.  Measuring both ends derives theta instead of assuming it, and the
measured corner span doubles as a scale/orientation sanity check.

Usage:
    python3 tools/validate_roi_map.py --manifest m.json [--map glyph_map.json]
    python3 tools/validate_roi_map.py --manifest m.json --fill m_filled.json
Exit code: 0 clean, 1 validation errors, 2 could not load.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from p0.core import dump_json, load_json                 # noqa: E402
from make_glyph_map import glyph_key                     # noqa: E402

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

DEFAULT_MAP = os.path.join(ROOT, "fixtures", "physical", "coupons", "glyph_map.json")
DEFAULT_CERT = os.path.join(ROOT, "config", "frames", "FRAME-SYN-0001.json")

# tools/run_real_batch.py --scaffold writes this as a stub.  It is a *plausible*
# ROI at the frame centre, which is exactly why it must be rejected by name: left
# unedited it silently measures whatever sits at the middle of the window.
SCAFFOLD_PLACEHOLDER_ROI = [0.0, 0.0, 1.5, 3.2]
PLACEHOLDER_STRINGS = frozenset(("", "todo", "tbd", "n/a", "na", "none", "null",
                                 "unknown", "unspecified", "?", "-"))

# `roi_mm` must be the computed value, not an adjusted one.  This is a float
# bookkeeping tolerance, not a measurement threshold.
EXACT_TOL_MM = 1e-6
# Registration geometry is only accepted as a *derived* transform; a mounting
# rotated more than this is still handled exactly, but the lever arm on the
# registration uncertainty grows, so it is reported.
ROTATION_ADVISORY_DEG = 5.0


class RoiMapError(Exception):
    pass


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------

def registration_transform(reg, coupon_w_mm):
    """(ox, oy, theta_rad, span_mm, u_mm) from two measured coupon corners.

    The coupon's top-left corner is the panel-local origin.  `theta` is the angle
    of the coupon's +x edge in the fiducial plane.
    """
    tl = reg.get("corner_top_left_mm")
    tr = reg.get("corner_top_right_mm")
    for name, pt in (("corner_top_left_mm", tl), ("corner_top_right_mm", tr)):
        if not (isinstance(pt, (list, tuple)) and len(pt) == 2
                and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        for v in pt)):
            raise RoiMapError("%s must be two numbers in fiducial-plane mm" % name)
    dx, dy = float(tr[0]) - float(tl[0]), float(tr[1]) - float(tl[1])
    span = math.hypot(dx, dy)
    if span <= 0.0:
        raise RoiMapError("the two registration corners coincide")
    u = reg.get("u_mm")
    if not isinstance(u, (int, float)) or isinstance(u, bool) or u < 0:
        raise RoiMapError("u_mm must be a non-negative number (caliper survey "
                          "uncertainty, P0_PROTOCOL.md §1 step 4)")
    return float(tl[0]), float(tl[1]), math.atan2(dy, dx), span, float(u)


def panel_to_fiducial(px, py, ox, oy, theta):
    """Panel-local (y DOWN) -> fiducial-plane (y UP).

    X = ox + px*cos(t) + py*sin(t)
    Y = oy + px*sin(t) - py*cos(t)
    """
    c, s = math.cos(theta), math.sin(theta)
    return ox + px * c + py * s, oy + px * s - py * c


def registration_uncertainty_at(px, py, span, u_mm):
    """Positional uncertainty of a glyph centre, propagated from the two corners.

    The angle uncertainty is u*sqrt(2)/span, and it acts through the lever arm
    from the registration origin to the glyph.
    """
    r = math.hypot(px, py)
    u_theta = (u_mm * math.sqrt(2.0)) / span if span > 0 else float("inf")
    return u_mm + r * u_theta


def compute_roi(g, reg, coupon_w_mm):
    """The pre-registered ROI for one glyph under one mounting."""
    ox, oy, theta, span, u = registration_transform(reg, coupon_w_mm)
    cx, cy = panel_to_fiducial(g["panel_x_mm"], g["panel_y_mm"], ox, oy, theta)
    return {
        "roi_mm": [cx, cy, g["roi_w_mm"], g["roi_h_mm"]],
        "theta_deg": math.degrees(theta),
        "span_mm": span,
        "u_reg_mm": registration_uncertainty_at(g["panel_x_mm"], g["panel_y_mm"],
                                                span, u),
        "tolerance_mm": g["roi_tolerance_mm"],
    }


def frame_limits(cert):
    """(x_window, y_window, x_hull, y_hull) half-extents in fiducial mm."""
    win = cert.get("window_mm") or []
    xw = float(win[0]) / 2.0 if len(win) == 2 else None
    yw = float(win[1]) / 2.0 if len(win) == 2 else None
    xs, ys = [], []
    for m in (cert.get("markers") or {}).values():
        for c in m.get("corners_mm") or []:
            xs.append(abs(float(c[0])))
            ys.append(abs(float(c[1])))
    return xw, yw, (max(xs) if xs else None), (max(ys) if ys else None)


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def is_placeholder(value):
    return (value is None
            or (isinstance(value, str)
                and value.strip().lower() in PLACEHOLDER_STRINGS))


def index_map(glyph_map):
    idx = {}
    for g in glyph_map.get("glyphs") or []:
        key = g.get("glyph_key")
        if key in idx:
            raise RoiMapError("duplicate glyph_key in the map: %s" % key)
        idx[key] = g
    if not idx:
        raise RoiMapError("the glyph map contains no glyphs")
    return idx


def validate(manifest, glyph_map, cert=None, min_hull_margin_mm=None):
    """Return (issues, summary, computed).  Deterministic order."""
    issues = []

    def add(sev, code, detail, run_id=None):
        issues.append({"severity": sev, "code": code, "run": run_id,
                       "detail": detail})

    idx = index_map(glyph_map)
    coupon_w = float((glyph_map.get("coupon_size_mm") or [95.0, 55.0])[0])
    xw, yw, xh, yh = frame_limits(cert or {})
    regs = manifest.get("registrations") or {}
    runs = manifest.get("runs") or []
    computed = {}
    seen_runs, seen_cells = {}, {}

    for r in runs:
        rid = r.get("run_id")
        if is_placeholder(rid):
            add(ERROR, "MISSING_RUN_ID", "every run needs a run_id")
            continue
        if rid in seen_runs:
            add(ERROR, "DUPLICATE_RUN_ID",
                "run_id %r already appears in this manifest" % rid, rid)
        seen_runs[rid] = True

        # --- glyph identity -------------------------------------------------
        panel = r.get("panel_id")
        shape = r.get("glyph_label")
        nominal = r.get("nominal_h_mm")
        gindex = r.get("glyph_index", 1)
        if is_placeholder(panel) or is_placeholder(shape):
            add(ERROR, "GLYPH_NOT_PREREGISTERED",
                "panel_id and glyph_label must name a mapped glyph; the scaffold "
                "writes glyph_label='TODO' and that is not a glyph", rid)
            continue
        if not isinstance(nominal, (int, float)) or isinstance(nominal, bool):
            add(ERROR, "MISSING_NOMINAL_HEIGHT",
                "nominal_h_mm is required to identify the glyph row; it remains a "
                "print instruction and never a reference value", rid)
            continue
        key = glyph_key(panel, shape, nominal, gindex)
        g = idx.get(key)
        if g is None:
            add(ERROR, "GLYPH_NOT_IN_MAP",
                "%s is not in the pre-registered map; a glyph that was not "
                "registered before capture cannot be measured" % key, rid)
            continue
        if r.get("glyph_key") is not None and r.get("glyph_key") != key:
            add(ERROR, "GLYPH_KEY_MISMATCH",
                "glyph_key=%r contradicts panel_id/glyph_label/nominal_h_mm "
                "(%s)" % (r.get("glyph_key"), key), rid)
        if r.get("shape_class") is not None and r["shape_class"] != g["shape_class"]:
            add(ERROR, "SHAPE_CLASS_MISMATCH",
                "shape_class=%r but the map says %s for %s; the estimator branch "
                "would be wrong" % (r["shape_class"], g["shape_class"], key), rid)

        cell = (key, r.get("device"), r.get("operator"), r.get("repeat"))
        if cell in seen_cells:
            add(ERROR, "DUPLICATE_GLYPH_CELL",
                "glyph %s already has a run for device/operator/repeat "
                "%s (row %s); repeats must differ in at least one of them"
                % (key, cell[1:], seen_runs and rid), rid)
        seen_cells[cell] = rid

        # --- registration ---------------------------------------------------
        reg = r.get("registration") or regs.get(panel)
        if not isinstance(reg, dict):
            add(ERROR, "MISSING_REGISTRATION",
                "no registration for panel %s; roi_mm cannot be derived without "
                "the measured panel->fiducial transform" % panel, rid)
            continue
        if is_placeholder(reg.get("top_left_identified_by")):
            add(ERROR, "REGISTRATION_ORIGIN_UNIDENTIFIED",
                "top_left_identified_by must record how the panel-local origin "
                "corner was identified (the coupon prints its panel label there); "
                "otherwise a 180-degree mounting silently selects a different glyph",
                rid)
        try:
            c = compute_roi(g, reg, coupon_w)
        except RoiMapError as exc:
            add(ERROR, "BAD_REGISTRATION", str(exc), rid)
            continue
        computed[rid] = c

        if abs(c["span_mm"] - coupon_w) > g["roi_tolerance_mm"]:
            add(ERROR, "REGISTRATION_SPAN_IMPLAUSIBLE",
                "the measured corner span is %.3f mm but the coupon edge is "
                "%.3f mm; a discrepancy beyond this glyph's %.4f mm ROI budget "
                "means the wrong corners were measured, the panel is mounted in "
                "the wrong orientation, or the print is mis-scaled"
                % (c["span_mm"], coupon_w, g["roi_tolerance_mm"]), rid)
        if c["u_reg_mm"] > g["roi_tolerance_mm"]:
            add(ERROR, "REGISTRATION_UNCERTAINTY_EXCEEDS_ROI_TOLERANCE",
                "registration uncertainty at this glyph is %.4f mm but the ROI "
                "budget derived from p0/measure.py is %.4f mm; the run would "
                "abstain or, worse, scan the wrong region"
                % (c["u_reg_mm"], g["roi_tolerance_mm"]), rid)
        if abs(c["theta_deg"]) > ROTATION_ADVISORY_DEG:
            add(WARN, "LARGE_MOUNTING_ROTATION",
                "the mounting is rotated %.2f deg. The transform handles it "
                "exactly, but the lever arm on the registration uncertainty grows "
                "with it" % c["theta_deg"], rid)

        # --- the declared roi_mm -------------------------------------------
        declared = r.get("roi_mm")
        if declared is None:
            add(ERROR, "MISSING_ROI",
                "roi_mm is absent. Run with --fill to write the computed value; "
                "it must never be typed by hand", rid)
            continue
        if list(declared) == SCAFFOLD_PLACEHOLDER_ROI:
            add(ERROR, "SCAFFOLD_PLACEHOLDER_ROI",
                "roi_mm is still the run_real_batch.py --scaffold stub %s. It is a "
                "plausible box at the frame centre, so left unedited it would "
                "silently measure whatever lies there"
                % (SCAFFOLD_PLACEHOLDER_ROI,), rid)
            continue
        if not (isinstance(declared, (list, tuple)) and len(declared) == 4
                and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        for v in declared)):
            add(ERROR, "BAD_ROI_SHAPE",
                "roi_mm must be four numbers (cx, cy, w, h) in fiducial-plane "
                "millimetres, got %r" % (declared,), rid)
            continue
        dcx, dcy, dw, dh = (float(v) for v in declared)
        if dw <= 0 or dh <= 0:
            add(ERROR, "NONPOSITIVE_ROI_SIZE",
                "roi_mm width and height must be positive, got w=%s h=%s" % (dw, dh),
                rid)
            continue
        ecx, ecy, ew, eh = c["roi_mm"]
        if abs(dw - ew) > EXACT_TOL_MM or abs(dh - eh) > EXACT_TOL_MM:
            swapped = (abs(dw - eh) <= EXACT_TOL_MM and abs(dh - ew) <= EXACT_TOL_MM)
            add(ERROR, "ROI_SIZE_NOT_FROM_MAP",
                "roi_mm size is (%.4f, %.4f) but the map's glyph box is "
                "(%.4f, %.4f)%s" % (dw, dh, ew, eh,
                                    "; width and height look swapped" if swapped
                                    else ""), rid)
        off = math.hypot(dcx - ecx, dcy - ecy)
        if off > g["roi_tolerance_mm"]:
            add(ERROR, "ROI_WRONG_GLYPH",
                "roi_mm centre is %.4f mm from the pre-registered position, beyond "
                "this glyph's %.4f mm budget: this is a different region, not a "
                "correction" % (off, g["roi_tolerance_mm"]), rid)
        elif off > EXACT_TOL_MM:
            add(ERROR, "ROI_ADJUSTED_BY_HAND",
                "roi_mm centre differs from the computed position by %.6f mm. The "
                "ROI must be the computed value; any nudge is the post-hoc freedom "
                "the pre-registration exists to remove" % off, rid)

        # --- visibility, checked before capture ------------------------------
        if xw is not None and (abs(ecx) + 0.5 * ew > xw
                               or abs(ecy) + 0.5 * eh > yw):
            add(ERROR, "GLYPH_OUTSIDE_FRAME_WINDOW",
                "the glyph box reaches (%.2f, %.2f) mm but the frame window is "
                "+/-(%.2f, %.2f) mm: the frame would occlude it. Re-place the "
                "frame, then re-measure the registration"
                % (abs(ecx) + 0.5 * ew, abs(ecy) + 0.5 * eh, xw, yw), rid)
        if min_hull_margin_mm is not None and xh is not None:
            if (xh - abs(ecx) < min_hull_margin_mm
                    or yh - abs(ecy) < min_hull_margin_mm):
                add(ERROR, "ROI_OUTSIDE_HULL_MARGIN",
                    "the ROI centre is closer than min_hull_margin_mm=%.1f to the "
                    "control-point hull, so the HOMOGRAPHY gate will abstain"
                    % min_hull_margin_mm, rid)

    summary = {
        "runs": len(runs),
        "runs_with_computed_roi": len(computed),
        "map_glyphs": len(idx),
        "map_hash": glyph_map.get("map_hash"),
        "panels_registered": sorted(regs),
        "issues": {sev: sum(1 for i in issues if i["severity"] == sev)
                   for sev in (ERROR, WARN, INFO)},
    }
    return issues, summary, computed


def fill(manifest, glyph_map, computed):
    """Return a copy of the manifest with roi_mm set to the computed values."""
    out = dict(manifest)
    runs = []
    for r in manifest.get("runs") or []:
        r2 = dict(r)
        c = computed.get(r.get("run_id"))
        if c is not None:
            r2["roi_mm"] = [round(v, 6) for v in c["roi_mm"]]
            r2["roi_source"] = "COMPUTED_FROM_GLYPH_MAP"
            r2["glyph_map_hash"] = glyph_map.get("map_hash")
        runs.append(r2)
    out["runs"] = runs
    return out


def report(issues, summary, out=None):
    out = out or sys.stdout
    for k in sorted(summary):
        if k != "issues":
            out.write("  %-34s %s\n" % (k, summary[k]))
    out.write("  issues: %s\n" % summary["issues"])
    for i in issues:
        out.write("  [%s] %-44s %s%s\n"
                  % (i["severity"], i["code"],
                     ("run=%s " % i["run"]) if i["run"] else "", i["detail"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--map", default=DEFAULT_MAP)
    ap.add_argument("--frame-cert", default=DEFAULT_CERT)
    ap.add_argument("--gate-policy", default=None)
    ap.add_argument("--fill", default=None,
                    help="write a manifest with roi_mm computed from the map")
    a = ap.parse_args(argv)

    try:
        man = load_json(a.manifest)
        gmap = load_json(a.map)
        cert = load_json(a.frame_cert) if os.path.exists(a.frame_cert) else {}
    except Exception as exc:                                    # noqa: BLE001
        sys.stderr.write("ROI MAP REJECTED: %s\n" % exc)
        return 2

    margin = None
    if a.gate_policy and os.path.exists(a.gate_policy):
        margin = load_json(a.gate_policy).get("min_hull_margin_mm")

    try:
        issues, summary, computed = validate(man, gmap, cert, margin)
    except RoiMapError as exc:
        sys.stderr.write("ROI MAP REJECTED: %s\n" % exc)
        return 2

    sys.stdout.write("manifest: %s\n" % a.manifest)
    report(issues, summary)
    n_err = summary["issues"][ERROR]
    if a.fill:
        dump_json(a.fill, fill(man, gmap, computed))
        sys.stdout.write("filled manifest written: %s (%d roi_mm computed)\n"
                         % (a.fill, len(computed)))
    sys.stdout.write("VERDICT: %s\n"
                     % ("ACCEPTED" if n_err == 0
                        else "REJECTED (%d errors)" % n_err))
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
