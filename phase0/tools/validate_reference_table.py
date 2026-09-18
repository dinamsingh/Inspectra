#!/usr/bin/env python3
"""Validate a reference (ground-truth) table before any phone data is processed.

Scope: this tool validates and reports on **manually recorded reference
measurements**.  It deliberately does **not** measure a scan or a microscope image -- see
`docs/P0_REFERENCE_PROCEDURE.md` §3.5 for why that remains an open B2 item.

What it enforces
----------------
* the full reference schema (`docs/P0_REFERENCE_PROCEDURE.md` §6);
* unit consistency (`unit` must be `mm`);
* the **independence rule**: a cross-check pair may not consist solely of rows produced
  by the pipeline estimator, and a `MICROSCOPE` row may never declare it.  Without this,
  estimator-definitional bias is common mode and cancels inside P1 (§5);
* duplicate / superseded row detection (rows are append-only, latest timestamp wins);
* the frozen prohibition on using the nominal artwork height as a reference value;
* provenance linkage to a run manifest, when one is supplied.

What it reports (without needing any phone data)
------------------------------------------------
The P1 scanner-vs-microscope agreement statistic, by delegating to
`analyse_physical.compute_p1`, so the threshold and the arithmetic keep a single source
of truth (`docs/P0_CRITERIA.md`).  P1 is computable from the reference table alone, so it
can and must be settled **before** any camera run is analysed.

Usage:
    python3 tools/validate_reference_table.py --table reference/reference_table.csv
    python3 tools/validate_reference_table.py --table <csv> --manifest <manifest.json>
    python3 tools/validate_reference_table.py --table <csv> --agreement
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

from p0.core import dump_json, load_json          # noqa: E402
from p0.results import read_csv                   # noqa: E402

# --- schema (docs/P0_REFERENCE_PROCEDURE.md §6) -----------------------------
REQUIRED_FIELDS = (
    "glyph_id", "panel_id", "glyph_shape", "nominal_h_mm", "glyph_index",
    "method", "measurement_procedure", "reference_h_mm", "unit", "reference_u_mm",
    "instrument_id", "instrument_cal_ref", "operator", "measured_at",
    "n_repeats", "raw_readings", "cross_check_status", "notes",
)
METHODS = ("SCANNER_2400DPI", "MICROSCOPE")
PROCEDURES = ("PIPELINE_ESTIMATOR_ON_SCAN", "MANUAL_VISUAL_CROSSHAIR", "UNRESOLVED")
PIPELINE_PROCEDURES = ("PIPELINE_ESTIMATOR_ON_SCAN",)
CROSS_CHECK_STATUS = ("PENDING", "AGREED", "DISAGREED", "UNUSABLE")
REQUIRE_NOTES_WHEN = ("DISAGREED", "UNUSABLE")
UNIT = "mm"

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"


class ReferenceTableError(Exception):
    pass


def canonical_glyph_id(panel_id, glyph_shape, nominal_h_mm, glyph_index):
    try:
        h = "%.2f" % float(nominal_h_mm)
    except (TypeError, ValueError):
        h = "NA"
    try:
        idx = "%d" % int(float(glyph_index))
    except (TypeError, ValueError):
        idx = "NA"
    return "%s:%s:%s:%s" % (panel_id, glyph_shape, h, idx)


def glyph_key(row):
    return (row.get("panel_id"), row.get("glyph_shape"),
            row.get("nominal_h_mm"), row.get("glyph_index"))


def load_table(path):
    if not os.path.exists(path):
        raise ReferenceTableError("no such reference table: %s" % path)
    rows = read_csv(path)
    if not rows:
        raise ReferenceTableError("reference table is empty: %s" % path)
    missing = [f for f in REQUIRED_FIELDS if f not in rows[0]]
    if missing:
        raise ReferenceTableError("reference table is missing required fields: %s"
                                  % sorted(missing))
    return rows


def validate(rows, manifest=None):
    """Return (issues, summary).  Issues are sorted and deterministic."""
    issues = []

    def add(sev, code, detail, row_no=None):
        issues.append({"severity": sev, "code": code, "row": row_no,
                       "detail": detail})

    seen_exact = {}
    by_key_method = {}

    for i, r in enumerate(rows, start=2):        # row 1 is the header
        # --- enumerations -------------------------------------------------
        if r.get("method") not in METHODS:
            add(ERROR, "BAD_METHOD",
                "method=%r must be one of %s" % (r.get("method"), list(METHODS)), i)
        proc = r.get("measurement_procedure")
        if proc not in PROCEDURES:
            add(ERROR, "BAD_PROCEDURE",
                "measurement_procedure=%r must be one of %s" % (proc, list(PROCEDURES)), i)
        elif proc == "UNRESOLVED":
            add(ERROR, "PROCEDURE_UNRESOLVED",
                "measurement_procedure=UNRESOLVED: this row cannot serve as a "
                "reference until the procedure is declared", i)
        st = r.get("cross_check_status")
        if st not in CROSS_CHECK_STATUS:
            add(ERROR, "BAD_CROSS_CHECK_STATUS",
                "cross_check_status=%r must be one of %s" % (st, list(CROSS_CHECK_STATUS)), i)
        elif st in REQUIRE_NOTES_WHEN and not str(r.get("notes") or "").strip():
            add(ERROR, "DISAGREEMENT_WITHOUT_NOTE",
                "cross_check_status=%s requires a non-empty notes field; a "
                "disagreement may never be recorded silently" % st, i)

        # --- units and values ---------------------------------------------
        if str(r.get("unit") or "").strip() != UNIT:
            add(ERROR, "BAD_UNIT",
                "unit=%r must be %r (no implicit conversion is performed)"
                % (r.get("unit"), UNIT), i)
        v = r.get("reference_h_mm")
        if not isinstance(v, float):
            add(ERROR, "MISSING_REFERENCE_VALUE",
                "reference_h_mm=%r is not a number" % (v,), i)
        elif v <= 0.0:
            add(ERROR, "NONPOSITIVE_REFERENCE_VALUE",
                "reference_h_mm=%s must be positive" % v, i)
        u = r.get("reference_u_mm")
        if u is None:
            add(WARN, "NO_REFERENCE_UNCERTAINTY",
                "reference_u_mm is empty; the protocol states an uncertainty target "
                "of <= 0.01 mm, so a stated value is expected", i)
        elif not isinstance(u, float) or u < 0.0:
            add(ERROR, "BAD_REFERENCE_UNCERTAINTY",
                "reference_u_mm=%r must be a non-negative number" % (u,), i)

        # --- the frozen prohibition on nominal-as-reference ---------------
        nom = r.get("nominal_h_mm")
        if isinstance(v, float) and isinstance(nom, float) and abs(v - nom) < 1e-12:
            add(WARN, "REFERENCE_EQUALS_NOMINAL",
                "reference_h_mm equals nominal_h_mm exactly (%s); the nominal artwork "
                "height may never be used as ground truth. Confirm this is a real "
                "measurement." % v, i)

        # --- identity -----------------------------------------------------
        want = canonical_glyph_id(r.get("panel_id"), r.get("glyph_shape"),
                                  r.get("nominal_h_mm"), r.get("glyph_index"))
        if str(r.get("glyph_id") or "").strip() != want:
            add(ERROR, "GLYPH_ID_MISMATCH",
                "glyph_id=%r does not match the canonical form %r"
                % (r.get("glyph_id"), want), i)
        for f in ("instrument_id", "operator", "measured_at"):
            if not str(r.get(f) or "").strip():
                add(ERROR, "MISSING_PROVENANCE",
                    "%s is empty; reference provenance is mandatory" % f, i)
        if not str(r.get("instrument_cal_ref") or "").strip():
            add(WARN, "NO_INSTRUMENT_CALIBRATION_REF",
                "instrument_cal_ref is empty; without a calibration reference the "
                "reference value is not traceable", i)

        # --- independence rule (per row) -----------------------------------
        if r.get("method") == "MICROSCOPE" and proc in PIPELINE_PROCEDURES:
            add(ERROR, "MICROSCOPE_NOT_INDEPENDENT",
                "a MICROSCOPE row may not declare measurement_procedure=%s; the "
                "cross-check exists to be independent of the pipeline estimator" % proc, i)

        # --- duplicates / supersession -------------------------------------
        exact = (glyph_key(r), r.get("method"), r.get("measured_at"))
        if exact in seen_exact:
            add(ERROR, "DUPLICATE_ROW",
                "same glyph, method and measured_at already appears at row %d"
                % seen_exact[exact], i)
        else:
            seen_exact[exact] = i
        by_key_method.setdefault((glyph_key(r), r.get("method")), []).append((i, r))

    # --- supersession + pairing + independence (per glyph) ----------------
    superseded = 0
    for (key, method), entries in sorted(by_key_method.items(),
                                         key=lambda kv: str(kv[0])):
        if len(entries) > 1:
            ordered = sorted(entries, key=lambda e: (str(e[1].get("measured_at")), e[0]))
            superseded += len(ordered) - 1
            add(INFO, "SUPERSEDED_ROWS",
                "glyph %s method %s has %d rows; the latest measured_at is taken as "
                "current and the earlier %d are retained as history"
                % (canonical_glyph_id(*key), method, len(ordered), len(ordered) - 1),
                ordered[-1][0])

    keys = sorted(set(k for (k, _m) in by_key_method), key=str)
    paired, pipeline_only = [], []
    for key in keys:
        methods = {m for (k, m) in by_key_method if k == key}
        if not METHODS[0] in methods or not METHODS[1] in methods:
            continue
        paired.append(key)
        procs = set()
        for m in METHODS:
            for _i, r in by_key_method.get((key, m), []):
                procs.add(r.get("measurement_procedure"))
        if procs and all(p in PIPELINE_PROCEDURES for p in procs):
            pipeline_only.append(key)
            add(ERROR, "PAIR_NOT_INDEPENDENT",
                "glyph %s is cross-checked but every row uses the pipeline estimator "
                "(%s); estimator-definitional bias would be common mode and cancel, "
                "so this pair cannot support P1" % (canonical_glyph_id(*key),
                                                    sorted(procs)))

    summary = {
        "rows": len(rows),
        "glyphs": len(keys),
        "glyphs_cross_checked": len(paired),
        "glyphs_cross_checked_pipeline_only": len(pipeline_only),
        "superseded_rows": superseded,
        "rows_by_method": {m: sum(1 for r in rows if r.get("method") == m)
                           for m in METHODS},
        "rows_by_procedure": {p: sum(1 for r in rows
                                     if r.get("measurement_procedure") == p)
                              for p in PROCEDURES},
        "cross_check_status_counts": {s: sum(1 for r in rows
                                             if r.get("cross_check_status") == s)
                                      for s in CROSS_CHECK_STATUS},
    }

    # --- provenance linkage ----------------------------------------------
    if manifest is not None:
        runs = manifest.get("runs") or []
        need = {}
        for r in runs:
            if (r.get("safety_class") or "SAFE") != "SAFE":
                continue
            k = canonical_glyph_id(r.get("panel_id"), r.get("glyph_label"),
                                   r.get("nominal_h_mm"), 1)
            need.setdefault(k, []).append(r.get("run_id"))
        have = {canonical_glyph_id(*k) for k in keys}
        missing = sorted(k for k in need if k not in have)
        for k in missing:
            add(ERROR, "NO_REFERENCE_FOR_RUN",
                "manifest runs %s measure glyph %s but the reference table has no row "
                "for it" % (sorted(need[k])[:3], k))
        panels_manifest = {str(r.get("panel_id")) for r in runs}
        orphan = sorted({str(k[0]) for k in keys} - panels_manifest)
        for p in orphan:
            add(WARN, "REFERENCE_PANEL_NOT_IN_MANIFEST",
                "reference table has rows for panel %s which the manifest never uses" % p)
        summary["manifest_glyphs_needing_reference"] = len(need)
        summary["manifest_glyphs_without_reference"] = len(missing)

    issues.sort(key=lambda d: (d["severity"], d["code"], d["row"] or 0, d["detail"]))
    return issues, summary


def agreement_report(table_path):
    """P1 agreement computed from the reference table alone (no phone data)."""
    import analyse_physical as ap
    crits = ap.load_physical_criteria()
    rows = read_csv(table_path)
    res = ap.compute_p1(rows, crits["P1"])
    return {"note": ("P1 is computable from the reference table alone and must be "
                     "settled before any camera run is analysed; thresholds come from "
                     "docs/P0_CRITERIA.md"),
            "P1": res}


def main(argv=None):
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--table", required=True)
    ap_.add_argument("--manifest", default="")
    ap_.add_argument("--agreement", action="store_true",
                     help="also report the P1 scanner-vs-microscope agreement")
    ap_.add_argument("--out", default="")
    a = ap_.parse_args(argv)

    try:
        rows = load_table(a.table)
    except ReferenceTableError as exc:
        print("REFERENCE TABLE REJECTED: %s" % exc)
        return 2

    manifest = None
    if a.manifest:
        if not os.path.exists(a.manifest):
            print("REFERENCE TABLE REJECTED: no such manifest: %s" % a.manifest)
            return 2
        manifest = load_json(a.manifest)

    issues, summary = validate(rows, manifest)
    report = {"table": os.path.basename(a.table), "summary": summary,
              "issues": issues,
              "counts": {s: sum(1 for i in issues if i["severity"] == s)
                         for s in (ERROR, WARN, INFO)}}
    if a.agreement:
        report["agreement"] = agreement_report(a.table)

    if a.out:
        dump_json(a.out, report)

    print("reference table: %s" % a.table)
    for k, v in sorted(summary.items()):
        print("  %-42s %s" % (k, v))
    print("  issues: %s" % report["counts"])
    for it in issues:
        if it["severity"] == INFO:
            continue
        print("  [%s] %-32s row=%s  %s" % (it["severity"], it["code"],
                                           it["row"] if it["row"] else "-",
                                           it["detail"]))
    if a.agreement:
        p1 = report["agreement"]["P1"]
        print("  P1 (reference-only pre-check): %s  %s"
              % (p1["status"], p1["statistics"].get("mean_abs_difference_mm")))
    n_err = report["counts"][ERROR]
    print("VERDICT: %s" % ("REJECTED (%d errors)" % n_err if n_err else "ACCEPTED"))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
