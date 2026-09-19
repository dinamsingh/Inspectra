#!/usr/bin/env python3
"""Pre-capture mechanical flatness acceptance for the print plane (blocker B4).

Why this is mechanical and not a gate: `docs/P0_ASSUMPTIONS.md` **A-06** is measured,
not assumed — an undeclared 5 mm plane offset and a 20 degree local print tilt were
both MEASURED, with reprojection RMS 0.09-0.12 px and LOMO 0.0002, i.e. every
geometric gate comfortably satisfied while the height error reached 0.08 mm and
0.18 mm.  No software gate can catch that from a single view.  So flatness must be
verified with an instrument *before* capture and recorded per panel.

The acceptance is **not invented here**.  The shipped uncertainty budget already
assumes a bound: `p0/uncertainty.py` computes

    u_tilt = h * (1 - cos(residual_tilt_bound_deg)) / sqrt(3)

with `residual_tilt_bound_deg = 3.0` in `config/uncertainty_model_v1.json`.  Every
interval the pipeline has ever emitted rests on that bound.  This tool therefore
reads the bound out of the model and refuses a register that states a different one:
loosening the acceptance would require changing the uncertainty model, not this file.

What the operator can actually measure is a **gap**, not an angle
(`P0_PROTOCOL.md` §1 step 6: "feeler / straight edge").  The conversion uses the
first-order bow model of **A-05** (a bowed panel is locally a tilted, offset plane):
for a parabolic bow of sagitta `s` over a straightedge span `L`, the largest local
slope is `4 s / L`, so

    max_gap_mm = tan(bound) * L / 4

Usage:
    python3 tools/validate_flatness.py --template reference/flatness_register.json
    python3 tools/validate_flatness.py --register reference/flatness_register.json
    python3 tools/validate_flatness.py --register <reg> --manifest manifests/pilot.json
Exit code: 0 verified, 1 not verified, 2 could not load.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, load_json          # noqa: E402

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"
PASS, FAIL, UNVERIFIED = "PASS", "FAIL", "UNVERIFIED"
STATUSES = (PASS, FAIL, UNVERIFIED)

UNCERTAINTY_MODEL = os.path.join(ROOT, "config", "uncertainty_model_v1.json")
ACCEPTANCE_SOURCE = "config/uncertainty_model_v1.json:residual_tilt_bound_deg"

# `P0_PROTOCOL.md` §0 / `tools/make_configs.py: WINDOW` -- the measurement window.
WINDOW_MM = (50.0, 20.0)

MOUNTING_METHODS = ("BONDED", "CLAMPED", "VACUUM", "TAPED_PERIMETER",
                    "UNCONSTRAINED")
# The stress block deliberately uses an unclamped panel
# (`P0_EXECUTION_PLAN.md` §4: "bowed (unclamped) panel"), so this is reported, not
# forbidden -- a nominal panel should not be relying on it.
MOUNTING_ADVISORY = ("UNCONSTRAINED", "TAPED_PERIMETER")

FLUSH_OK = "NO_ROCK_NO_GAP"
FLUSH_STATES = (FLUSH_OK, "ROCK", "GAP", "NOT_CHECKED")

# Float bookkeeping only: a gap written at exactly the published limit must not fail
# on a round-trip through tan/atan.  This is not a relaxation of the acceptance.
TILT_FLOAT_TOL_DEG = 1e-9

PLACEHOLDERS = frozenset(("", "-", "?", "n/a", "na", "tbd", "todo", "none", "null",
                          "unknown", "unspecified", "pending"))


class FlatnessError(Exception):
    pass


def named(value):
    return isinstance(value, str) and value.strip().lower() not in PLACEHOLDERS


def as_number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def max_gap_for(bound_deg, span_mm):
    """Largest straightedge gap consistent with `bound_deg` of local tilt."""
    return math.tan(math.radians(bound_deg)) * span_mm / 4.0


def tilt_from_gap(gap_mm, span_mm):
    """Local tilt implied by a sagitta `gap_mm` over span `span_mm` (A-05, 4s/L)."""
    if span_mm <= 0:
        return float("inf")
    return math.degrees(math.atan(4.0 * gap_mm / span_mm))


def height_error_mm(h_mm, tilt_deg):
    """Foreshortening error of an in-plane length under local tilt: h*(1-cos a).

    This is the closed form that `out/synthetic` reproduces: at 10 deg on a 3.06 mm
    glyph it predicts -0.0465 mm against a measured -0.0456 mm, and at 20 deg
    -0.1845 mm against -0.1847 mm.
    """
    return h_mm * (1.0 - math.cos(math.radians(tilt_deg)))


def model_bound_deg(path=None):
    model = load_json(path or UNCERTAINTY_MODEL)
    bound = as_number(model.get("residual_tilt_bound_deg"))
    if bound is None or bound <= 0:
        raise FlatnessError("residual_tilt_bound_deg is missing from the "
                            "uncertainty model; there is no acceptance to enforce")
    return bound


# ---------------------------------------------------------------------------
# per-panel evaluation
# ---------------------------------------------------------------------------

def evaluate_panel(rec, bound_deg):
    """Return (derived_status, findings, detail).  Never optimistic."""
    findings = []
    detail = {}

    def bad(sev, code, text):
        findings.append({"severity": sev, "code": code, "detail": text})

    if not isinstance(rec, dict):
        return UNVERIFIED, [{"severity": ERROR, "code": "BAD_PANEL_RECORD",
                             "detail": "the panel record must be an object"}], detail

    missing = []
    instrument = rec.get("instrument")
    if not named(instrument):
        missing.append("instrument")
    res = as_number(rec.get("instrument_resolution_mm"))
    if res is None or res <= 0:
        missing.append("instrument_resolution_mm")
    if not named(rec.get("operator")):
        missing.append("operator")
    if not named(rec.get("measured_at")):
        missing.append("measured_at")

    spans = []
    for axis, default in (("long", WINDOW_MM[0]), ("short", WINDOW_MM[1])):
        span = as_number(rec.get("straightedge_span_%s_mm" % axis))
        gap = as_number(rec.get("max_gap_%s_mm" % axis))
        if span is None or span <= 0:
            missing.append("straightedge_span_%s_mm" % axis)
        if gap is None or gap < 0:
            missing.append("max_gap_%s_mm" % axis)
        if span and gap is not None and gap >= 0:
            spans.append((axis, span, gap, default))

    flush = rec.get("frame_flush_check")
    if flush not in FLUSH_STATES:
        missing.append("frame_flush_check")
    if not named(rec.get("backing_id")):
        missing.append("backing_id")
    if rec.get("backing_rigid_flat_verified") is not True:
        missing.append("backing_rigid_flat_verified")
    method = rec.get("mounting_method")
    if method not in MOUNTING_METHODS:
        missing.append("mounting_method")

    if missing:
        bad(ERROR, "FLATNESS_EVIDENCE_MISSING",
            "no verified flatness for this panel; missing: %s" % sorted(set(missing)))

    # --- the measurement itself ------------------------------------------
    worst_tilt, worst_axis = None, None
    for axis, span, gap, _default in spans:
        tilt = tilt_from_gap(gap, span)
        limit = max_gap_for(bound_deg, span)
        detail["tilt_%s_deg" % axis] = round(tilt, 6)
        detail["max_gap_%s_mm" % axis] = round(limit, 6)
        if worst_tilt is None or tilt > worst_tilt:
            worst_tilt, worst_axis = tilt, axis
        if res is not None and res > limit:
            bad(ERROR, "INSTRUMENT_CANNOT_RESOLVE_LIMIT",
                "the instrument resolves %.4f mm but the %s-axis acceptance is a "
                "%.4f mm gap; a pass would be unmeasurable" % (res, axis, limit))
    if worst_tilt is not None:
        detail["worst_tilt_deg"] = round(worst_tilt, 6)
        detail["worst_axis"] = worst_axis
        detail["acceptance_tilt_deg"] = bound_deg
        detail["error_on_3mm_glyph_mm"] = round(height_error_mm(3.06, worst_tilt), 6)
        if worst_tilt > bound_deg + TILT_FLOAT_TOL_DEG:
            bad(ERROR, "LOCAL_TILT_BEYOND_MODEL_BOUND",
                "the measured bow implies %.3f deg of local tilt on the %s axis, "
                "beyond the %.1f deg the uncertainty budget assumes. On a 3.06 mm "
                "glyph that is %.4f mm of foreshortening error that no gate can see"
                % (worst_tilt, worst_axis, bound_deg,
                   height_error_mm(3.06, worst_tilt)))

    if flush in ("ROCK", "GAP"):
        bad(ERROR, "FRAME_NOT_FLUSH",
            "frame_flush_check=%s: the fiducial plane is not on the print plane, "
            "which is the offset term A-06 shows is invisible to every gate" % flush)
    elif flush == "NOT_CHECKED":
        bad(ERROR, "FRAME_FLUSH_NOT_CHECKED",
            "the frame flush / rock-and-gap check named in A-06 was not performed")

    if method in MOUNTING_ADVISORY:
        bad(WARN, "WEAK_MOUNTING",
            "mounting_method=%s does not itself constrain the panel; the gap "
            "measurement is then the only thing holding flatness" % method)

    n_err = sum(1 for f in findings if f["severity"] == ERROR)
    if n_err == 0:
        return PASS, findings, detail
    hard = {"LOCAL_TILT_BEYOND_MODEL_BOUND", "FRAME_NOT_FLUSH"}
    if any(f["code"] in hard for f in findings):
        return FAIL, findings, detail
    return UNVERIFIED, findings, detail


# ---------------------------------------------------------------------------
# register + manifest
# ---------------------------------------------------------------------------

def validate(register, manifest=None, bound_deg=None):
    issues = []
    panels_out = {}

    def add(sev, code, detail, panel=None):
        issues.append({"severity": sev, "code": code, "panel": panel,
                       "detail": detail})

    if bound_deg is None:
        bound_deg = model_bound_deg()

    acc = register.get("acceptance") or {}
    stated = as_number(acc.get("max_local_tilt_deg"))
    if stated is None:
        add(ERROR, "ACCEPTANCE_MISSING",
            "acceptance.max_local_tilt_deg must be stated and must equal the "
            "model's residual_tilt_bound_deg (%s)" % ACCEPTANCE_SOURCE)
    elif abs(stated - bound_deg) > 1e-9:
        add(ERROR, "ACCEPTANCE_NOT_FROM_MODEL",
            "acceptance.max_local_tilt_deg=%s contradicts the uncertainty model's "
            "residual_tilt_bound_deg=%s. Loosening the mechanical acceptance "
            "without changing the model would invalidate every interval the "
            "pipeline emits" % (stated, bound_deg))

    panels = register.get("panels")
    if not isinstance(panels, dict) or not panels:
        add(ERROR, "NO_PANELS_RECORDED",
            "the register contains no panel records; an empty register verifies "
            "nothing")
        panels = {}

    for pid in sorted(panels):
        rec = panels[pid]
        derived, findings, detail = evaluate_panel(rec, bound_deg)
        panels_out[pid] = {"derived_status": derived, "detail": detail}
        for f in findings:
            add(f["severity"], f["code"], f["detail"], pid)
        declared = rec.get("status") if isinstance(rec, dict) else None
        if declared is not None:
            if declared not in STATUSES:
                add(ERROR, "BAD_STATUS",
                    "status=%r must be one of %s" % (declared, list(STATUSES)), pid)
            elif declared != derived:
                add(ERROR, "STATUS_CONTRADICTS_EVIDENCE",
                    "the record declares %s but its own measurements derive %s; "
                    "the evidence decides, not the declaration"
                    % (declared, derived), pid)
        if (isinstance(rec, dict) and derived != PASS
                and not str(rec.get("notes") or "").strip()):
            add(WARN, "NO_DISPOSITION_NOTE",
                "a panel that is %s needs a note recording what was done about it"
                % derived, pid)

    # --- manifest cross-check --------------------------------------------
    if manifest is not None:
        for r in manifest.get("runs") or []:
            pid, rid = r.get("panel_id"), r.get("run_id")
            if not named(pid):
                continue
            got = panels_out.get(pid)
            if got is None:
                add(ERROR, "NO_FLATNESS_RECORD_FOR_PANEL",
                    "run %s uses panel %s, which has no flatness record. An "
                    "unverified panel may not become accuracy data"
                    % (rid, pid), pid)
                continue
            if got["derived_status"] != PASS:
                add(ERROR, "RUN_ON_UNVERIFIED_PANEL",
                    "run %s uses panel %s whose flatness is %s"
                    % (rid, pid, got["derived_status"]), pid)
            if r.get("declared_flat") is True and got["derived_status"] != PASS:
                add(ERROR, "DECLARED_FLAT_WITHOUT_EVIDENCE",
                    "run %s sets declared_flat=true while panel %s derives %s. The "
                    "PLANARITY gate trusts that boolean, so this is how an "
                    "unverified panel would pass silently"
                    % (rid, pid, got["derived_status"]), pid)
            if r.get("declared_flat") is None:
                add(ERROR, "DECLARED_FLAT_ABSENT",
                    "run %s does not state declared_flat; it must be set from the "
                    "flatness record, never left to a default" % rid, pid)

    counts = {s: sum(1 for v in panels_out.values() if v["derived_status"] == s)
              for s in STATUSES}
    summary = {
        "acceptance_tilt_deg": bound_deg,
        "acceptance_source": ACCEPTANCE_SOURCE,
        "max_gap_long_mm": round(max_gap_for(bound_deg, WINDOW_MM[0]), 6),
        "max_gap_short_mm": round(max_gap_for(bound_deg, WINDOW_MM[1]), 6),
        "panels": len(panels_out),
        "panel_status_counts": counts,
        "issues": {sev: sum(1 for i in issues if i["severity"] == sev)
                   for sev in (ERROR, WARN, INFO)},
        "verified": (len(panels_out) > 0
                     and counts[PASS] == len(panels_out)
                     and summary_errors(issues) == 0),
    }
    return issues, summary, panels_out


def summary_errors(issues):
    return sum(1 for i in issues if i["severity"] == ERROR)


def template():
    bound = model_bound_deg()
    return {
        "_README": [
            "B4 flatness register.  One record per panel, filled BEFORE capture.",
            "A-06 is measured: local out-of-plane print tilt is invisible to every",
            "software gate, so this file is the only thing standing between a warped",
            "panel and accuracy data.  Leave a field null until it is measured;",
            "null reads as UNVERIFIED, never as flat.",
            "Acceptance comes from the uncertainty model and may not be edited here.",
            "max gap = tan(bound) * span / 4   (A-05 first-order bow, slope 4s/L)",
        ],
        "acceptance": {
            "max_local_tilt_deg": bound,
            "source": ACCEPTANCE_SOURCE,
            "max_gap_long_mm": round(max_gap_for(bound, WINDOW_MM[0]), 6),
            "max_gap_short_mm": round(max_gap_for(bound, WINDOW_MM[1]), 6),
            "window_mm": list(WINDOW_MM),
        },
        "panels": {
            "P01": {
                "backing_id": None, "backing_rigid_flat_verified": None,
                "mounting_method": None,
                "instrument": None, "instrument_resolution_mm": None,
                "straightedge_span_long_mm": WINDOW_MM[0], "max_gap_long_mm": None,
                "straightedge_span_short_mm": WINDOW_MM[1], "max_gap_short_mm": None,
                "frame_flush_check": None,
                "operator": None, "measured_at": None,
                "status": None, "notes": "",
            }
        },
    }


def report(issues, summary, panels, out=None):
    out = out or sys.stdout
    for k in sorted(summary):
        if k != "issues":
            out.write("  %-26s %s\n" % (k, summary[k]))
    out.write("  issues: %s\n" % summary["issues"])
    for pid in sorted(panels):
        d = panels[pid]["detail"]
        extra = ""
        if "worst_tilt_deg" in d:
            extra = ("  worst %.3f deg on the %s axis -> %.4f mm on a 3.06 mm glyph"
                     % (d["worst_tilt_deg"], d["worst_axis"],
                        d["error_on_3mm_glyph_mm"]))
        out.write("  %-6s %-11s%s\n" % (pid, panels[pid]["derived_status"], extra))
    for i in issues:
        out.write("  [%s] %-34s %s%s\n"
                  % (i["severity"], i["code"],
                     ("panel=%s " % i["panel"]) if i["panel"] else "", i["detail"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--register")
    ap.add_argument("--manifest")
    ap.add_argument("--template")
    ap.add_argument("--json-out")
    a = ap.parse_args(argv)

    if a.template:
        dump_json(a.template, template())
        sys.stdout.write("blank flatness register written: %s\n" % a.template)
        sys.stdout.write("every measurement field is null, so verification returns "
                         "NO until the panel is actually surveyed\n")
        return 0
    if not a.register:
        ap.error("one of --register or --template is required")

    try:
        reg = load_json(a.register)
        man = load_json(a.manifest) if a.manifest else None
    except Exception as exc:                                    # noqa: BLE001
        sys.stderr.write("B4_FLATNESS_VERIFIED = NO (%s)\n" % exc)
        return 2
    if not isinstance(reg, dict):
        sys.stderr.write("B4_FLATNESS_VERIFIED = NO (register must be an object)\n")
        return 2

    try:
        issues, summary, panels = validate(reg, man)
    except FlatnessError as exc:
        sys.stderr.write("B4_FLATNESS_VERIFIED = NO (%s)\n" % exc)
        return 2

    sys.stdout.write("flatness register: %s\n" % a.register)
    report(issues, summary, panels)
    if a.json_out:
        dump_json(a.json_out, {"summary": summary, "panels": panels,
                               "issues": issues,
                               "B4_FLATNESS_VERIFIED": "YES" if summary["verified"]
                               else "NO"})
    sys.stdout.write("B4_FLATNESS_VERIFIED = %s\n"
                     % ("YES" if summary["verified"] else "NO"))
    return 0 if summary["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
