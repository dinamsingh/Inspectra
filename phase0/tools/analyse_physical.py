#!/usr/bin/env python3
"""Physical (PHYSICAL_PILOT) analyser: computes P1-P7 from the frozen criteria.

Single source of truth
----------------------
Thresholds are **parsed out of `phase0/docs/P0_CRITERIA.md`** at run time.  Nothing in
this file hard-codes a P-criterion limit, so the document stays the only place a
physical threshold is written down.  If the table changes shape the parser raises
rather than guessing.

Populations come from the run manifest (`manifest_used.json`), i.e. from the
pre-registered assignment, never from the measured values.  The analyser therefore
cannot select panels, glyphs or conditions on the basis of their result.

Missing data is never zero-filled.  A criterion whose population is absent, whose
reference values are missing, or whose definition is not decidable from the frozen
documents returns `UNCOMPUTABLE` with a reason.  It never returns `PASS`.

Usage:
    python3 tools/analyse_physical.py --in out/pilot [--out out/pilot/analysis]
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, load_json, mean, median, sd  # noqa: E402
from p0.results import read_csv                             # noqa: E402

CRITERIA_DOC = os.path.join(ROOT, "docs", "P0_CRITERIA.md")
PHYSICAL_EXPERIMENT = "PHYSICAL_PILOT"
MEASURED = "MEASURED"
ND = 6                     # rounding for serialised statistics (determinism)

PASS, CONDITIONAL, FAIL, UNCOMPUTABLE = "PASS", "CONDITIONAL", "FAIL", "UNCOMPUTABLE"

REQUIRED_COLUMNS = ("run_id", "status", "safety_class", "panel_id", "device",
                    "operator", "repeat", "h_mm", "lower_mm", "upper_mm",
                    "true_h_mm", "design_h_mm")
REFERENCE_COLUMNS = ("panel_id", "glyph_shape", "nominal_h_mm", "glyph_index",
                     "method", "reference_h_mm")
SCANNER, MICROSCOPE = "SCANNER_2400DPI", "MICROSCOPE"


# ---------------------------------------------------------------------------
# criteria parsing (the frozen document is the only threshold source)
# ---------------------------------------------------------------------------

_GO_LOWER = re.compile(r"^<=\s*([0-9]*\.?[0-9]+)\s*(mm)?$")
_GO_HIGHER = re.compile(r"^>=\s*([0-9]*\.?[0-9]+)\s*(mm)?$")
_RANGE = re.compile(r"([0-9]*\.?[0-9]+)\s*-\s*([0-9]*\.?[0-9]+)")
_NUM = re.compile(r"([0-9]*\.?[0-9]+)")


class CriteriaError(Exception):
    pass


def load_physical_criteria(path=CRITERIA_DOC):
    """Parse the P1..P7 table out of P0_CRITERIA.md."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if "## Physical stage" not in text:
        raise CriteriaError("no '## Physical stage' section in %s" % path)
    section = text.split("## Physical stage", 1)[1].split("\n## ", 1)[0]
    out = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or not re.match(r"^P[0-9]+$", cells[0]):
            continue
        pid, criterion, go_raw, cond_raw, nogo_raw = cells[:5]
        c = {"id": pid, "criterion": criterion, "go_raw": go_raw,
             "conditional_raw": cond_raw, "nogo_raw": nogo_raw,
             "source": "docs/P0_CRITERIA.md"}
        m_lo, m_hi = _GO_LOWER.match(go_raw), _GO_HIGHER.match(go_raw)
        if m_lo:
            c["direction"] = "LOWER_IS_BETTER"
            c["go"] = float(m_lo.group(1))
            c["decidable"] = True
        elif m_hi:
            c["direction"] = "HIGHER_IS_BETTER"
            c["go"] = float(m_hi.group(1))
            c["decidable"] = True
        else:
            # Free text in the Go cell: the criterion references a quantity that
            # this document does not define numerically.  Do not guess it.
            c["direction"] = None
            c["go"] = None
            c["decidable"] = False
            c["undecidable_reason"] = (
                "the Go cell is free text (%r) and does not reduce to a single "
                "'<= value' or '>= value' rule" % go_raw)
        rng = _RANGE.search(cond_raw)
        if rng:
            c["conditional_lo"] = float(rng.group(1))
            c["conditional_hi"] = float(rng.group(2))
        else:
            c["conditional_lo"] = c["conditional_hi"] = None
        n = _NUM.search(nogo_raw)
        c["nogo_bound"] = float(n.group(1)) if n else None
        mn = re.search(r">=\s*([0-9]+)\s*glyphs", criterion)
        c["min_sample"] = int(mn.group(1)) if mn else None
        cm = re.search(r"\(([0-9]*\.?[0-9]+)\s*mm class\)", criterion)
        c["class_nominal_mm"] = float(cm.group(1)) if cm else None
        out[pid] = c
    expected = ["P%d" % i for i in range(1, 8)]
    missing = [p for p in expected if p not in out]
    if missing:
        raise CriteriaError("criteria table is missing %s" % missing)
    for pid in ("P1", "P2", "P3", "P4", "P6"):
        if out[pid].get("direction") != "LOWER_IS_BETTER":
            raise CriteriaError("%s was expected to be a 'lower is better' rule; "
                                "the frozen table changed shape" % pid)
    if out["P5"].get("direction") != "HIGHER_IS_BETTER":
        raise CriteriaError("P5 was expected to be a 'higher is better' rule")
    return out


def band(stat, crit):
    """Map a statistic onto the frozen Go / Conditional / No-go bands."""
    if not crit.get("decidable"):
        return UNCOMPUTABLE, crit.get("undecidable_reason", "criterion not decidable")
    if stat is None or stat != stat:
        return UNCOMPUTABLE, "statistic not available"
    go = crit["go"]
    lo, hi = crit.get("conditional_lo"), crit.get("conditional_hi")
    if crit["direction"] == "LOWER_IS_BETTER":
        if stat <= go:
            return PASS, None
        if hi is not None and stat <= hi:
            return CONDITIONAL, "inside the Conditional band %s" % crit["conditional_raw"]
        return FAIL, "beyond the No-go bound %s" % crit["nogo_raw"]
    if stat >= go:
        return PASS, None
    if lo is not None and stat >= lo:
        return CONDITIONAL, "inside the Conditional band %s" % crit["conditional_raw"]
    return FAIL, "beyond the No-go bound %s" % crit["nogo_raw"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - r), min(1.0, c + r))


def _r(x):
    if x is None or (isinstance(x, float) and x != x):
        return None
    return round(float(x), ND)


def _result(pid, crit, statistics, status, reason, population):
    return {"id": pid, "criterion": crit["criterion"],
            "threshold_reference": {"document": crit["source"], "id": pid,
                                    "go": crit["go_raw"],
                                    "conditional": crit["conditional_raw"],
                                    "nogo": crit["nogo_raw"]},
            "statistics": {k: _r(v) if isinstance(v, float) else v
                           for k, v in sorted(statistics.items())},
            "population": {k: v for k, v in sorted(population.items())},
            "status": status, "reason": reason}


class DatasetError(Exception):
    pass


def load_dataset(in_dir):
    """Load results.csv, the run manifest and the reference table."""
    res_path = os.path.join(in_dir, "results.csv")
    if not os.path.exists(res_path):
        raise DatasetError("no results.csv in %s" % in_dir)
    rows = read_csv(res_path)
    if not rows:
        raise DatasetError("results.csv is empty")
    missing = [c for c in REQUIRED_COLUMNS if c not in rows[0]]
    if missing:
        raise DatasetError("results.csv is missing required columns: %s" % missing)
    phys = [r for r in rows
            if r.get("source") == "real" or r.get("experiment") == PHYSICAL_EXPERIMENT]
    if not phys:
        raise DatasetError("no %s / source=real rows in %s" % (PHYSICAL_EXPERIMENT, in_dir))

    manifest = None
    for name in ("manifest_used.json", "manifest.json"):
        p = os.path.join(in_dir, name)
        if os.path.exists(p):
            manifest = load_json(p)
            break

    reference = None
    for cand in (os.path.join(in_dir, "reference_table.csv"),
                 os.path.join(in_dir, "reference", "reference_table.csv")):
        if os.path.exists(cand):
            reference = read_csv(cand)
            miss = [c for c in REFERENCE_COLUMNS if c not in reference[0]]
            if miss:
                raise DatasetError("reference_table.csv is missing columns: %s" % miss)
            break
    return phys, manifest, reference


def split_blocks(rows, manifest):
    """Nominal vs stress, taken from the pre-registered safety_class labels."""
    nominal = [r for r in rows if (r.get("safety_class") or "SAFE") == "SAFE"]
    stress = [r for r in rows if (r.get("safety_class") or "SAFE") != "SAFE"]
    expected_nominal = expected_stress = None
    if manifest and isinstance(manifest.get("runs"), list):
        exp_n = exp_s = 0
        for r in manifest["runs"]:
            if (r.get("safety_class") or "SAFE") == "SAFE":
                exp_n += 1
            else:
                exp_s += 1
        expected_nominal, expected_stress = exp_n, exp_s
    return nominal, stress, expected_nominal, expected_stress


def _measured_with_reference(rows):
    """Rows that produced a height AND carry a reference value."""
    out, missing_ref = [], []
    for r in rows:
        if r.get("status") != MEASURED:
            continue
        if r.get("h_mm") is None or r.get("true_h_mm") is None:
            missing_ref.append(r.get("run_id"))
            continue
        out.append(r)
    return out, missing_ref


def _errors(rows):
    # recomputed from h_mm and true_h_mm; the stored error column is not trusted
    return [(r, r["h_mm"] - r["true_h_mm"]) for r in rows]


# ---------------------------------------------------------------------------
# criteria
# ---------------------------------------------------------------------------


def compute_p1(reference, crit):
    pid = "P1"
    pop = {"source": "reference_table.csv", "required_min_glyphs": crit["min_sample"]}
    if reference is None:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "no reference_table.csv in the dataset; the scanner/microscope "
                       "cross-check has not been recorded", pop)
    keyed = {}
    for r in reference:
        if r.get("reference_h_mm") is None or not r.get("method"):
            continue
        key = (r.get("panel_id"), r.get("glyph_shape"), r.get("nominal_h_mm"),
               r.get("glyph_index"))
        keyed.setdefault(key, {}).setdefault(r["method"], []).append(r["reference_h_mm"])
    diffs = []
    for key, by_method in sorted(keyed.items(), key=lambda kv: str(kv[0])):
        if SCANNER in by_method and MICROSCOPE in by_method:
            s = mean(by_method[SCANNER])
            m = mean(by_method[MICROSCOPE])
            diffs.append(abs(s - m))
    pop.update({"glyphs_in_table": len(keyed), "glyphs_with_both_methods": len(diffs)})
    if not diffs:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "no glyph has both %s and %s measurements" % (SCANNER, MICROSCOPE),
                       pop)
    stats = {"mean_abs_difference_mm": mean(diffs),
             "max_abs_difference_mm": max(diffs),
             "median_abs_difference_mm": median(diffs)}
    if crit["min_sample"] is not None and len(diffs) < crit["min_sample"]:
        return _result(pid, crit, stats, UNCOMPUTABLE,
                       "the criterion requires >= %d cross-checked glyphs; only %d "
                       "have both methods" % (crit["min_sample"], len(diffs)), pop)
    status, reason = band(stats["mean_abs_difference_mm"], crit)
    return _result(pid, crit, stats, status, reason, pop)


def _global_bias(nominal_rows):
    """One global bias over all nominal observations, per P2's wording."""
    usable, missing_ref = _measured_with_reference(nominal_rows)
    if missing_ref or not usable:
        return None, usable, missing_ref
    return mean([e for _, e in _errors(usable)]), usable, missing_ref


def compute_p2(nominal_rows, crit):
    pid = "P2"
    bias, usable, missing_ref = _global_bias(nominal_rows)
    pop = {"nominal_rows": len(nominal_rows),
           "measured_with_reference": len(usable),
           "measured_missing_reference": len(missing_ref),
           "abstained": len([r for r in nominal_rows if r.get("status") != MEASURED]),
           "class_nominal_mm": crit["class_nominal_mm"]}
    if missing_ref:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "%d measured nominal runs have no reference value (%s); a global "
                       "bias may not be estimated from a partial population"
                       % (len(missing_ref), ", ".join(str(x) for x in missing_ref[:5])),
                       pop)
    if bias is None:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "no measured nominal observation carries a reference value", pop)
    target = crit["class_nominal_mm"]
    if target is None:
        return _result(pid, crit, {"global_bias_mm": bias}, UNCOMPUTABLE,
                       "the criterion names a nominal-height class but the frozen table "
                       "does not give its value", pop)
    cls = [(r, e) for r, e in _errors(usable)
           if r.get("design_h_mm") is not None
           and abs(r["design_h_mm"] - target) < 1e-9]
    pop["class_rows"] = len(cls)
    stats = {"global_bias_mm": bias, "class_residual_mean_mm": None,
             "class_residual_sd_mm": None}
    if len(cls) < 2:
        return _result(pid, crit, stats, UNCOMPUTABLE,
                       "the %.1f mm class has %d measured observations; a residual SD "
                       "needs at least 2 (see blocker B5, panel->glyph assignment)"
                       % (target, len(cls)), pop)
    resid = [e - bias for _, e in cls]
    stats["class_residual_mean_mm"] = mean(resid)
    stats["class_residual_sd_mm"] = sd(resid)
    status, reason = band(stats["class_residual_sd_mm"], crit)
    return _result(pid, crit, stats, status, reason, pop)


def compute_p3(nominal_rows, crit):
    pid = "P3"
    measured = [r for r in nominal_rows if r.get("status") == MEASURED
                and r.get("h_mm") is not None]
    cells = {}
    for r in measured:
        cells.setdefault((r.get("panel_id"), r.get("device"), r.get("operator")),
                         []).append(r["h_mm"])
    multi = {k: v for k, v in cells.items() if len(v) >= 2}
    pop = {"nominal_rows": len(nominal_rows), "measured_rows": len(measured),
           "cells_total": len(cells), "cells_with_repeats": len(multi),
           "abstained": len([r for r in nominal_rows if r.get("status") != MEASURED])}
    note = ("repeats are the angle block (P0_EXECUTION_PLAN.md 1.3: R1=0, R2=12, "
            "R3=25 deg), so this within-cell SD contains the angle effect and is not "
            "a pure repeatability term; the within-burst term is burst_sd_mm")
    if not multi:
        return _result(pid, crit, {"note": note}, UNCOMPUTABLE,
                       "no (panel, device, operator) cell has 2 or more measured runs",
                       pop)
    num = den = 0.0
    per_cell = []
    for k in sorted(multi, key=lambda t: tuple(str(x) for x in t)):
        v = multi[k]
        s = sd(v)
        per_cell.append(s)
        num += (len(v) - 1) * s * s
        den += (len(v) - 1)
    pooled = math.sqrt(num / den) if den > 0 else None
    bursts = [r["burst_sd_mm"] for r in measured if r.get("burst_sd_mm") is not None]
    stats = {"pooled_within_cell_sd_mm": pooled,
             "median_cell_sd_mm": median(per_cell),
             "max_cell_sd_mm": max(per_cell),
             "median_burst_sd_mm": median(bursts) if bursts else None,
             "aggregation": "pooled within-cell SD, df weighted",
             "note": note}
    status, reason = band(pooled, crit)
    return _result(pid, crit, stats, status, reason, pop)


def compute_p4(nominal_rows, crit):
    pid = "P4"
    bias, usable, missing_ref = _global_bias(nominal_rows)
    by_dev = {}
    if bias is not None:
        for r, e in _errors(usable):
            by_dev.setdefault(r.get("device"), []).append(e - bias)
    pop = {"nominal_rows": len(nominal_rows),
           "measured_with_reference": len(usable),
           "measured_missing_reference": len(missing_ref),
           "devices": sorted(str(d) for d in by_dev),
           "per_device_n": {str(k): len(v) for k, v in sorted(by_dev.items(),
                                                             key=lambda kv: str(kv[0]))}}
    if missing_ref:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "%d measured nominal runs have no reference value; the global "
                       "bias correction this criterion depends on is unavailable"
                       % len(missing_ref), pop)
    if len(by_dev) < 2:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "inter-device bias needs 2 devices; the dataset has %d. The "
                       "frozen Conditional band already covers this case as a "
                       "per-device claim" % len(by_dev), pop)
    if len(by_dev) > 2:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "the criterion is a two-device difference; the dataset has %d "
                       "devices and the frozen table does not define an aggregation"
                       % len(by_dev), pop)
    (da, va), (db, vb) = sorted(by_dev.items(), key=lambda kv: str(kv[0]))
    stats = {"device_a": str(da), "device_b": str(db),
             "mean_residual_a_mm": mean(va), "mean_residual_b_mm": mean(vb),
             "abs_inter_device_bias_mm": abs(mean(va) - mean(vb)),
             "global_bias_mm": bias}
    status, reason = band(stats["abs_inter_device_bias_mm"], crit)
    return _result(pid, crit, stats, status, reason, pop)


def _acceptance(rows, expected, crit, pid, label):
    attempted = len(rows)
    measured = len([r for r in rows if r.get("status") == MEASURED])
    abstained = attempted - measured
    reasons = {}
    for r in rows:
        if r.get("status") != MEASURED:
            g = r.get("failed_gate") or r.get("failed_stage") or "UNKNOWN"
            reasons[str(g)] = reasons.get(str(g), 0) + 1
    pop = {"block": label, "attempted": attempted, "measured": measured,
           "abstained": abstained, "expected_from_manifest": expected,
           "abstention_reasons": dict(sorted(reasons.items()))}
    if attempted == 0:
        return _result(pid, crit, {}, UNCOMPUTABLE,
                       "the %s block has no runs in this dataset" % label, pop)
    if expected is not None and attempted < expected:
        return _result(pid, crit,
                       {"acceptance_rate": measured / attempted,
                        "abstention_rate": abstained / attempted},
                       UNCOMPUTABLE,
                       "dataset incomplete: %d of %d pre-registered %s runs are "
                       "present; an acceptance rate on a partial block could be "
                       "misleading" % (attempted, expected, label), pop)
    stats = {"acceptance_rate": measured / attempted,
             "abstention_rate": abstained / attempted}
    status, reason = band(stats["acceptance_rate"], crit)
    return _result(pid, crit, stats, status, reason, pop)


def compute_p5(nominal_rows, expected, crit):
    return _acceptance(nominal_rows, expected, crit, "P5", "nominal")


def compute_p6(stress_rows, expected, crit):
    return _acceptance(stress_rows, expected, crit, "P6", "stress")


def compute_p7(nominal_rows, crit, unc_model):
    pid = "P7"
    rows = [r for r in nominal_rows if r.get("status") == MEASURED
            and r.get("true_h_mm") is not None and r.get("lower_mm") is not None
            and r.get("upper_mm") is not None]
    covered = [1 if (r["lower_mm"] <= r["true_h_mm"] <= r["upper_mm"]) else 0
               for r in rows]
    pop = {"nominal_rows": len(nominal_rows), "evaluable_rows": len(rows),
           "abstained": len([r for r in nominal_rows if r.get("status") != MEASURED]),
           "panels": sorted(set(str(r.get("panel_id")) for r in rows))}
    stats = {"k_lower": unc_model.get("k_lower"), "k_upper": unc_model.get("k_upper"),
             "model_version": unc_model.get("model_version"),
             "model_calibrated": unc_model.get("calibrated")}
    if rows:
        k = sum(covered)
        lo, hi = wilson(k, len(covered))
        stats.update({"observed_coverage": k / len(covered), "n_covered": k,
                      "n_evaluated": len(covered),
                      "wilson_ci95_lo": lo, "wilson_ci95_hi": hi,
                      "ci_method": "Wilson score interval, observations treated as "
                                   "independent (not clustered by panel)"})
    # The statistic is computable; the acceptance rule is not.  Do not guess it.
    reason = (
        "P7's Go cell reads %r, which is not decidable from the frozen documents for "
        "three reasons. (1) 'nominal' is undefined here: P0_CRITERIA.md C4 states that "
        "k = 1.645 one sided each side is a ~90 percent two sided region, while "
        "P0_ASSUMPTIONS.md A-07 describes the same k as ~95 percent one sided - and the "
        "'covered' statistic is two sided containment, so the two readings are not "
        "interchangeable. (2) If nominal is taken as 0.90 the two conditions 'CI includes "
        "nominal' and 'CI lower bound >= 0.90' can only both hold when the lower bound is "
        "exactly 0.90, which is unsatisfiable in practice. (3) The CI method is "
        "unspecified: P0_PROTOCOL.md section 6 calls for a cluster bootstrap and a "
        "development / held-back split, neither of which the result schema records. "
        "Resolving any of these is a criteria decision and is deliberately not made here."
        % crit["go_raw"])
    return _result(pid, crit, stats, UNCOMPUTABLE, reason, pop)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def analyse(in_dir, out_dir=None, criteria_path=CRITERIA_DOC):
    out_dir = out_dir or os.path.join(in_dir, "analysis")
    os.makedirs(out_dir, exist_ok=True)
    crits = load_physical_criteria(criteria_path)
    rows, manifest, reference = load_dataset(in_dir)
    unc_model = load_json(os.path.join(ROOT, "config", "uncertainty_model_v1.json"))

    nominal, stress, exp_n, exp_s = split_blocks(rows, manifest)
    results = {
        "P1": compute_p1(reference, crits["P1"]),
        "P2": compute_p2(nominal, crits["P2"]),
        "P3": compute_p3(nominal, crits["P3"]),
        "P4": compute_p4(nominal, crits["P4"]),
        "P5": compute_p5(nominal, exp_n, crits["P5"]),
        "P6": compute_p6(stress, exp_s, crits["P6"]),
        "P7": compute_p7(nominal, crits["P7"], unc_model),
    }
    tally = {}
    for r in results.values():
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    report = {
        "schema_version": "p0-physical-analysis-1",
        "criteria_source": os.path.relpath(criteria_path, ROOT),
        "dataset": {
            "input": os.path.basename(os.path.abspath(in_dir)),
            "physical_rows": len(rows),
            "nominal_rows": len(nominal), "stress_rows": len(stress),
            "expected_nominal_from_manifest": exp_n,
            "expected_stress_from_manifest": exp_s,
            "reference_table_present": reference is not None,
            "manifest_present": manifest is not None,
        },
        "uncertainty_model": {k: unc_model.get(k) for k in
                              ("model_version", "k_lower", "k_upper", "calibrated")},
        "criteria": {k: v for k, v in sorted(crits.items())},
        "results": results,
        "tally": dict(sorted(tally.items())),
        "overall": ("ALL_DECIDED" if UNCOMPUTABLE not in tally else
                    "INCOMPLETE_%d_UNCOMPUTABLE" % tally[UNCOMPUTABLE]),
        "notice": ("Statuses are computed against the frozen bands in "
                   "docs/P0_CRITERIA.md. UNCOMPUTABLE is never a pass. No physical "
                   "accuracy is claimed by this file."),
    }
    dump_json(os.path.join(out_dir, "analysis_physical.json"), report)
    _markdown(report, os.path.join(out_dir, "PHYSICAL_RESULT.md"))
    return report


def _markdown(report, path):
    L = ["# P0-min physical pilot - P1 to P7", "",
         "Criteria source: `%s` (single source of truth for every threshold below)."
         % report["criteria_source"], "",
         "**%s**" % report["notice"], "",
         "## Dataset", "", "| field | value |", "|---|---|"]
    for k, v in sorted(report["dataset"].items()):
        L.append("| %s | %s |" % (k, v))
    L += ["", "## Criteria", "",
          "| ID | statistic | value | n | Go | status | reason |",
          "|---|---|---|---|---|---|---|"]
    headline = {"P1": "mean_abs_difference_mm", "P2": "class_residual_sd_mm",
                "P3": "pooled_within_cell_sd_mm", "P4": "abs_inter_device_bias_mm",
                "P5": "acceptance_rate", "P6": "acceptance_rate",
                "P7": "observed_coverage"}
    for pid in ["P%d" % i for i in range(1, 8)]:
        r = report["results"][pid]
        key = headline[pid]
        val = r["statistics"].get(key)
        n = (r["population"].get("glyphs_with_both_methods")
             or r["population"].get("class_rows")
             or r["population"].get("cells_with_repeats")
             or r["population"].get("attempted")
             or r["population"].get("evaluable_rows"))
        L.append("| %s | %s | %s | %s | %s | **%s** | %s |"
                 % (pid, key, "-" if val is None else val, n if n is not None else "-",
                    r["threshold_reference"]["go"], r["status"],
                    (r["reason"] or "")[:180]))
    L += ["", "## Tally", "",
          ", ".join("%s=%d" % kv for kv in sorted(report["tally"].items())),
          "", "Overall: **%s**" % report["overall"], ""]
    for pid in ["P%d" % i for i in range(1, 8)]:
        r = report["results"][pid]
        L += ["", "### %s - %s" % (pid, r["criterion"]), "",
              "* status: **%s**" % r["status"],
              "* bands: Go `%s` | Conditional `%s` | No-go `%s`"
              % (r["threshold_reference"]["go"], r["threshold_reference"]["conditional"],
                 r["threshold_reference"]["nogo"])]
        if r["reason"]:
            L.append("* reason: %s" % r["reason"])
        L.append("* statistics: %s" % (r["statistics"] or "none"))
        L.append("* population: %s" % r["population"])
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", default=None)
    ap.add_argument("--criteria", default=CRITERIA_DOC)
    a = ap.parse_args(argv)
    try:
        report = analyse(a.inp, a.out, a.criteria)
    except (DatasetError, CriteriaError) as exc:
        print("PHYSICAL ANALYSIS ABORTED: %s" % exc)
        return 2
    print("=" * 78)
    for pid in ["P%d" % i for i in range(1, 8)]:
        r = report["results"][pid]
        print("%-3s %-13s %s" % (pid, r["status"], (r["reason"] or "")[:56]))
    print("=" * 78)
    print("tally:", ", ".join("%s=%d" % kv for kv in sorted(report["tally"].items())))
    print("overall:", report["overall"])
    print("written:", os.path.join(a.out or os.path.join(a.inp, "analysis"),
                                   "analysis_physical.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
