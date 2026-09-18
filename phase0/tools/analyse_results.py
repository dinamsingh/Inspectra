#!/usr/bin/env python3
"""Analyse a P0-min result set: statistics, diagnostic plots, PASS/FAIL verdict.

Every criterion is pre-registered in docs/P0_CRITERIA.md.  Nothing in this
script is allowed to change a threshold based on the data it is reading; the
criteria are constants below and the verdict is computed mechanically.

Usage:
    python3 tools/analyse_results.py --in out/synthetic --out out/synthetic/analysis
"""
from __future__ import annotations

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from p0.core import dump_json, mean, median, percentile, sd   # noqa: E402
from p0.plots import Plot, histogram                          # noqa: E402
from p0.results import read_csv                               # noqa: E402

sys.path.insert(0, HERE)
from analyse_physical import PHYSICAL_EXPERIMENT              # noqa: E402
from analyse_physical import main as analyse_physical_main    # noqa: E402

# ---------------------------------------------------------------------------
# PRE-REGISTERED CRITERIA (do not tune against observed data)
# ---------------------------------------------------------------------------
CRIT = {
    "C1_math_max_abs_err_mm": 0.010,
    "C2_bias_abs_mm": 0.030,
    "C2_p95_abs_err_mm": 0.060,
    "C3_repeatability_sd_mm": 0.030,
    "C4_min_coverage": 0.90,
    "C7_unsafe_detectable_abstention": 1.00,
    "C8_max_false_clear": 0,
    "C11_min_safe_measure_rate": 0.80,
}
SAFE_ACCURACY_EXPERIMENTS = ("E_NOMINAL", "E_INKSPREAD", "E_ILLUM", "E_THICKNESS")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def one_sided_upper(k, n, z=1.645):
    if n == 0:
        return float("nan")
    return wilson(k, n, z * 2 / 1.96 * 0.98)[1] if k else 1.0 - (0.05 ** (1.0 / n))


def sel(rows, **kw):
    out = rows
    for k, v in kw.items():
        if isinstance(v, (list, tuple, set)):
            out = [r for r in out if r.get(k) in v]
        else:
            out = [r for r in out if r.get(k) == v]
    return out


def measured(rows):
    return [r for r in rows if r.get("status") == "MEASURED"
            and r.get("error_mm") is not None]


def stat_block(rows):
    errs = [r["error_mm"] for r in measured(rows)]
    abse = [abs(e) for e in errs]
    sds = [r["burst_sd_mm"] for r in measured(rows) if r.get("burst_sd_mm") is not None]
    cov = [r["covered"] for r in measured(rows) if r.get("covered") is not None]
    widths = [r["interval_width_mm"] for r in measured(rows)
              if r.get("interval_width_mm") is not None]
    n_all = len(rows)
    n_m = len(measured(rows))
    blk = {
        "n_runs": n_all,
        "n_measured": n_m,
        "measure_rate": (n_m / n_all) if n_all else float("nan"),
        "bias_mm": mean(errs) if errs else float("nan"),
        "median_error_mm": median(errs) if errs else float("nan"),
        "mae_mm": mean(abse) if abse else float("nan"),
        "p95_abs_error_mm": percentile(abse, 0.95) if abse else float("nan"),
        "max_abs_error_mm": max(abse) if abse else float("nan"),
        "sd_error_mm": sd(errs) if len(errs) > 1 else float("nan"),
        "median_burst_sd_mm": median(sds) if sds else float("nan"),
        "max_burst_sd_mm": max(sds) if sds else float("nan"),
        "coverage": (sum(cov) / len(cov)) if cov else float("nan"),
        "coverage_n": len(cov),
        "median_interval_width_mm": median(widths) if widths else float("nan"),
    }
    if cov:
        lo, hi = wilson(sum(cov), len(cov))
        blk["coverage_ci95"] = [lo, hi]
    return blk


def abstention_block(rows):
    out = {"n": len(rows), "abstained": 0, "measured": 0, "by_gate": {},
           "by_stage": {}}
    for r in rows:
        if r.get("status") == "MEASURED":
            out["measured"] += 1
        else:
            out["abstained"] += 1
            g = r.get("failed_gate") or "UNKNOWN"
            s = r.get("failed_stage") or "UNKNOWN"
            out["by_gate"][g] = out["by_gate"].get(g, 0) + 1
            out["by_stage"][s] = out["by_stage"].get(s, 0) + 1
    out["abstention_rate"] = (out["abstained"] / len(rows)) if rows else float("nan")
    return out


# ---------------------------------------------------------------------------


def sweep_table(rows, key):
    groups = {}
    for r in rows:
        groups.setdefault(r.get(key), []).append(r)
    table = []
    for k in sorted(groups, key=lambda v: (v is None, v)):
        g = groups[k]
        m = measured(g)
        table.append({
            key: k,
            "n": len(g),
            "measured": len(m),
            "bias_mm": mean([r["error_mm"] for r in m]) if m else None,
            "mae_mm": mean([abs(r["error_mm"]) for r in m]) if m else None,
            "median_u_c_mm": median([r["u_c_mm"] for r in m if r.get("u_c_mm")]) if m else None,
            "median_burst_sd_mm": median([r["burst_sd_mm"] for r in m
                                          if r.get("burst_sd_mm") is not None]) if m else None,
            "abstain_gates": sorted(set(r.get("failed_gate") or "" for r in g
                                        if r.get("status") != "MEASURED")),
        })
    return table


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=os.path.join(ROOT, "out", "synthetic"))
    ap.add_argument("--out", dest="out", default=None)
    args = ap.parse_args(argv)
    out_dir = args.out or os.path.join(args.inp, "analysis")
    os.makedirs(out_dir, exist_ok=True)

    rows = read_csv(os.path.join(args.inp, "results.csv"))

    # PHYSICAL_PILOT is a valid analysis population, but it is judged against the
    # physical criteria P1-P7, not against the synthetic C-criteria below.  Before
    # this routing existed, physical rows fell outside SAFE_ACCURACY_EXPERIMENTS and
    # the C-block silently produced all-nan statistics and a misleading OVERALL: FAIL.
    # SAFE_ACCURACY_EXPERIMENTS semantics are unchanged; the dataset is dispatched.
    physical = [r for r in rows if r.get("source") == "real"
                or r.get("experiment") == PHYSICAL_EXPERIMENT]
    if physical and len(physical) != len(rows):
        print("MIXED DATASET: %d physical and %d synthetic rows in %s.\n"
              "Refusing to analyse: the two populations answer different criteria "
              "(P1-P7 vs C1-C11). Separate them and re-run."
              % (len(physical), len(rows) - len(physical), args.inp))
        return 2
    if physical:
        print("physical dataset detected (%d rows) -> routing to analyse_physical"
              % len(physical))
        return analyse_physical_main(["--in", args.inp]
                                     + (["--out", args.out] if args.out else []))

    base = [r for r in rows if r.get("variant") in ("base", "linear")]
    report = {"n_rows": len(rows), "criteria": CRIT, "sections": {}}
    S = report["sections"]

    # ---- C1 arithmetic exactness ---------------------------------------
    math_rows = sel(base, experiment="E_MATH")
    S["E_MATH"] = stat_block(math_rows)
    S["E_MATH"]["by_shape"] = sweep_table(math_rows, "glyph_shape")

    # ---- C2/C3/C4 accuracy on nominal SAFE conditions -------------------
    safe = [r for r in base if r.get("experiment") in SAFE_ACCURACY_EXPERIMENTS]
    S["SAFE_ACCURACY"] = stat_block(safe)
    S["SAFE_ACCURACY"]["by_experiment"] = sweep_table(safe, "experiment")
    S["SAFE_ACCURACY"]["by_true_height"] = sweep_table(safe, "true_h_mm")
    S["SAFE_ACCURACY"]["by_shape"] = sweep_table(safe, "glyph_shape")

    # ---- sweeps ---------------------------------------------------------
    S["E_BLUR"] = {"table": sweep_table(sel(base, experiment="E_BLUR"), "blur_sigma_mm"),
                   "abstention": abstention_block(sel(base, experiment="E_BLUR"))}
    S["E_TILT"] = {"table": sweep_table(sel(base, experiment="E_TILT"), "pose_tilt_deg"),
                   "abstention": abstention_block(sel(base, experiment="E_TILT"))}
    S["E_RHO"] = {"table": sweep_table(sel(base, experiment="E_RHO"), "pose_z_mm"),
                  "abstention": abstention_block(sel(base, experiment="E_RHO"))}
    S["E_NOISE"] = {"table": sweep_table(sel(base, experiment="E_NOISE"), "fixture_id"),
                    "abstention": abstention_block(sel(base, experiment="E_NOISE"))}
    S["E_INKSPREAD"] = {"table": sweep_table(sel(base, experiment="E_INKSPREAD"),
                                             "ink_spread_mm")}

    # ---- C5 estimator ablation -----------------------------------------
    est_rows = [r for r in measured(safe) if r.get("maxminus_min_error_mm") is not None]
    S["C5_ESTIMATOR"] = {
        "n": len(est_rows),
        "model_fit_mae_mm": mean([abs(r["error_mm"]) for r in est_rows]) if est_rows else None,
        "maxminus_min_mae_mm": mean([abs(r["maxminus_min_error_mm"]) for r in est_rows]) if est_rows else None,
        "model_fit_bias_mm": mean([r["error_mm"] for r in est_rows]) if est_rows else None,
        "maxminus_min_bias_mm": mean([r["maxminus_min_error_mm"] for r in est_rows]) if est_rows else None,
    }
    blur_est = []
    for r in measured(sel(base, experiment="E_BLUR")):
        if r.get("maxminus_min_error_mm") is not None:
            blur_est.append((r["blur_sigma_mm"], r["error_mm"], r["maxminus_min_error_mm"]))
    S["C5_ESTIMATOR"]["vs_blur"] = [{"blur_sigma_mm": b, "model_fit_err_mm": e,
                                     "maxminus_min_err_mm": m}
                                    for b, e, m in sorted(blur_est)]

    # ---- C6 linearisation ablation --------------------------------------
    lin = {}
    for v in ("linear", "gamma", "gamma_glyph_only"):
        r = sel(rows, experiment="E_LINEARIZE", variant=v)
        lin[v] = {"status": r[0]["status"] if r else None,
                  "error_mm": r[0].get("error_mm") if r else None,
                  "failed_gate": r[0].get("failed_gate") if r else None}
    S["C6_LINEARIZE"] = lin

    # ---- E3 undistortion ablation ---------------------------------------
    dist = {}
    for v in ("undistort_on", "undistort_off"):
        r = sel(rows, experiment="E_DISTORT", variant=v)
        dist[v] = {"status": r[0]["status"] if r else None,
                   "error_mm": r[0].get("error_mm") if r else None,
                   "reproj_rms_px": r[0].get("reproj_rms_px") if r else None,
                   "failed_gate": r[0].get("failed_gate") if r else None}
    if (dist.get("undistort_on", {}).get("error_mm") is not None
            and dist.get("undistort_off", {}).get("error_mm") is not None):
        dist["delta_mm"] = (dist["undistort_off"]["error_mm"]
                            - dist["undistort_on"]["error_mm"])
    S["E3_UNDISTORTION"] = dist

    # ---- C7 unsafe detectable -------------------------------------------
    neg = sel(base, safety_class="UNSAFE_DETECTABLE")
    S["UNSAFE_DETECTABLE"] = abstention_block(neg)
    S["UNSAFE_DETECTABLE"]["per_fixture"] = [
        {"fixture_id": r["fixture_id"], "status": r["status"],
         "failed_stage": r.get("failed_stage"), "failed_gate": r.get("failed_gate"),
         "error_mm": r.get("error_mm")} for r in neg]

    # ---- C9 undetectable ------------------------------------------------
    und = sel(base, safety_class="UNSAFE_UNDETECTABLE")
    S["UNSAFE_UNDETECTABLE"] = {
        "n": len(und),
        "per_fixture": [{"fixture_id": r["fixture_id"], "status": r["status"],
                         "error_mm": r.get("error_mm"),
                         "u_c_mm": r.get("u_c_mm"),
                         "covered": r.get("covered"),
                         "failed_gate": r.get("failed_gate"),
                         "reproj_rms_px": r.get("reproj_rms_px"),
                         "lomo_rel_spread": r.get("lomo_rel_spread")} for r in und],
    }

    # ---- C8 decision safety ---------------------------------------------
    dec = sel(base, experiment="E_DECISION")
    tally = {"MEETS_SCREENING_THRESHOLD": 0, "POTENTIAL_UNDERSIZE": 0,
             "REQUIRES_OFFICER_REVIEW_BORDERLINE": 0, "ABSTAINED": 0}
    false_clear = []
    false_accuse = []
    detail = []
    for r in dec:
        thr = r.get("threshold_mm") or 3.0
        truly_under = r["true_h_mm"] < thr
        d = r.get("decision")
        if r.get("status") != "MEASURED":
            tally["ABSTAINED"] += 1
            d = "ABSTAINED"
        else:
            tally[d] = tally.get(d, 0) + 1
            if truly_under and d == "MEETS_SCREENING_THRESHOLD":
                false_clear.append(r["fixture_id"])
            if (not truly_under) and d == "POTENTIAL_UNDERSIZE":
                false_accuse.append(r["fixture_id"])
        detail.append({"fixture_id": r["fixture_id"], "true_h_mm": r["true_h_mm"],
                       "threshold_mm": thr, "truly_undersize": truly_under,
                       "decision": d, "h_mm": r.get("h_mm"),
                       "lower_mm": r.get("lower_mm"), "upper_mm": r.get("upper_mm")})
    n_under = len([r for r in dec if r["true_h_mm"] < (r.get("threshold_mm") or 3.0)])
    n_over = len(dec) - n_under
    S["C8_DECISION"] = {
        "tally": tally, "detail": detail,
        "n_truly_undersize": n_under, "n_truly_compliant": n_over,
        "false_clear": false_clear, "false_accuse": false_accuse,
        "false_clear_count": len(false_clear),
        "false_accuse_count": len(false_accuse),
    }

    # ---- verdict ---------------------------------------------------------
    v = {}
    m1 = S["E_MATH"]["max_abs_error_mm"]
    v["C1_arithmetic"] = _mk(m1 <= CRIT["C1_math_max_abs_err_mm"],
                             "max|err|=%.5f mm <= %.3f" % (m1, CRIT["C1_math_max_abs_err_mm"]))
    sa = S["SAFE_ACCURACY"]
    v["C2_accuracy"] = _mk(abs(sa["bias_mm"]) <= CRIT["C2_bias_abs_mm"]
                           and sa["p95_abs_error_mm"] <= CRIT["C2_p95_abs_err_mm"],
                           "bias=%+.4f (<=%.3f), p95|err|=%.4f (<=%.3f)"
                           % (sa["bias_mm"], CRIT["C2_bias_abs_mm"],
                              sa["p95_abs_error_mm"], CRIT["C2_p95_abs_err_mm"]))
    v["C3_repeatability"] = _mk(sa["median_burst_sd_mm"] <= CRIT["C3_repeatability_sd_mm"],
                                "median burst SD=%.4f mm (<=%.3f)"
                                % (sa["median_burst_sd_mm"], CRIT["C3_repeatability_sd_mm"]))
    cov = sa.get("coverage")
    v["C4_coverage"] = _mk(cov == cov and cov >= CRIT["C4_min_coverage"],
                           "coverage=%.3f on n=%d (>=%.2f); k is NOMINAL, not validated"
                           % (cov, sa.get("coverage_n", 0), CRIT["C4_min_coverage"]))
    e = S["C5_ESTIMATOR"]
    ok5 = (e["model_fit_mae_mm"] is not None
           and e["maxminus_min_mae_mm"] is not None
           and e["model_fit_mae_mm"] < e["maxminus_min_mae_mm"])
    v["C5_estimator"] = _mk(ok5, "model-fit MAE=%.4f vs max-minus-min MAE=%.4f"
                            % (e["model_fit_mae_mm"] or float("nan"),
                               e["maxminus_min_mae_mm"] or float("nan")))
    gl = lin.get("gamma_glyph_only", {}).get("error_mm")
    ll = lin.get("linear", {}).get("error_mm")
    ok6 = (gl is not None and ll is not None and abs(gl) > abs(ll))
    v["C6_linearisation"] = _mk(ok6,
                                "linear err=%s vs gamma-glyph err=%s; full gamma: %s"
                                % (_f(ll), _f(gl), lin.get("gamma", {}).get("status")))
    ud = S["UNSAFE_DETECTABLE"]
    v["C7_unsafe_detection"] = _mk(ud["n"] > 0 and ud["abstention_rate"] >= CRIT["C7_unsafe_detectable_abstention"],
                                   "abstained %d/%d" % (ud["abstained"], ud["n"]))
    v["C8_decision_safety"] = _mk(S["C8_DECISION"]["false_clear_count"] <= CRIT["C8_max_false_clear"],
                                  "false-clear=%d of %d undersize; false-accuse=%d of %d compliant"
                                  % (S["C8_DECISION"]["false_clear_count"], n_under,
                                     S["C8_DECISION"]["false_accuse_count"], n_over))
    und_errs = [abs(p["error_mm"]) for p in S["UNSAFE_UNDETECTABLE"]["per_fixture"]
                if p.get("error_mm") is not None]
    v["C9_undetectable_documented"] = _mk(
        True, "single-view undetectable defects measured with |err| up to %s mm; "
              "these require fixture control, not gates"
              % (_f(max(und_errs)) if und_errs else "n/a"), warn=True)
    v["C11_safe_measure_rate"] = _mk(sa["measure_rate"] >= CRIT["C11_min_safe_measure_rate"],
                                     "measure rate on SAFE=%.2f (>=%.2f)"
                                     % (sa["measure_rate"], CRIT["C11_min_safe_measure_rate"]))
    report["verdict"] = v
    report["overall"] = "PASS" if all(x["pass"] for x in v.values()
                                     if not x.get("informational")) else "FAIL"

    dump_json(os.path.join(out_dir, "analysis.json"), report)
    _plots(base, rows, S, out_dir)
    _markdown(report, S, out_dir)

    print("=" * 78)
    for k in sorted(v):
        print("%-26s %-5s %s" % (k, "PASS" if v[k]["pass"] else
                                 ("WARN" if v[k].get("informational") else "FAIL"),
                                 v[k]["detail"]))
    print("=" * 78)
    print("OVERALL:", report["overall"])
    print("written:", out_dir)
    return 0


def _f(x, nd=4):
    return "n/a" if x is None else ("%." + str(nd) + "f") % x


def _mk(ok, detail, warn=False):
    return {"pass": bool(ok), "detail": detail, "informational": bool(warn)}


def _plots(base, rows, S, out_dir):
    pd = os.path.join(out_dir, "plots")
    os.makedirs(pd, exist_ok=True)
    safe = [r for r in base if r.get("experiment") in SAFE_ACCURACY_EXPERIMENTS
            and r.get("status") == "MEASURED"]

    # 1. true vs estimated
    p = Plot("True vs estimated ink height (SAFE conditions)",
             "true ink height (mm)", "estimated height (mm)")
    xs = [r["true_h_mm"] for r in safe]
    ys = [r["h_mm"] for r in safe]
    if xs:
        lo, hi = min(xs), max(xs)
        p.line([lo, hi], [lo, hi], label="identity", color="#888")
    p.scatter(xs, ys, label="estimate")
    p.errorbars(xs, [r["lower_mm"] for r in safe], [r["upper_mm"] for r in safe],
                label="interval", color="#c0392b")
    p.note("n=%d runs; intervals use a NOMINAL coverage factor k=1.645" % len(safe))
    p.save(os.path.join(pd, "01_true_vs_estimated.svg"))

    # 2. bias vs true height
    p = Plot("Signed error vs true height", "true ink height (mm)", "error (mm)")
    p.hline(0.0, "zero")
    p.hline(CRIT["C2_bias_abs_mm"], "+bias limit", "#c0392b")
    p.hline(-CRIT["C2_bias_abs_mm"], "-bias limit", "#c0392b")
    p.scatter(xs, [r["error_mm"] for r in safe], label="error")
    p.save(os.path.join(pd, "02_bias_vs_height.svg"))

    # 3. repeatability
    p = Plot("Burst repeatability (SD of 7 frames)", "true ink height (mm)",
             "burst SD (mm)")
    p.hline(CRIT["C3_repeatability_sd_mm"], "limit", "#c0392b")
    p.scatter(xs, [r["burst_sd_mm"] for r in safe], label="burst SD")
    p.save(os.path.join(pd, "03_repeatability.svg"))

    # 4. error distribution
    c, n = histogram([r["error_mm"] for r in safe], bins=16)
    p = Plot("Error distribution (SAFE)", "error (mm)", "count")
    if c:
        p.bars(["%.3f" % v for v in c], n, label="runs")
    p.save(os.path.join(pd, "04_error_distribution.svg"))

    # 5. blur sensitivity + estimator comparison
    bl = sorted(measured(sel(base, experiment="E_BLUR")),
                key=lambda r: r["blur_sigma_mm"] or 0)
    p = Plot("Blur sensitivity and estimator comparison",
             "estimated blur sigma (mm)", "signed error (mm)")
    p.hline(0.0, "zero")
    p.line([r["blur_sigma_mm"] for r in bl], [r["error_mm"] for r in bl],
           label="fitted-extreme estimator")
    p.line([r["blur_sigma_mm"] for r in bl],
           [r["maxminus_min_error_mm"] for r in bl],
           label="max-minus-min (diagnostic)", color="#c0392b")
    ab = [r for r in sel(base, experiment="E_BLUR") if r.get("status") != "MEASURED"]
    p.note("abstained at higher blur: %d of %d fixtures"
           % (len(ab), len(sel(base, experiment="E_BLUR"))))
    p.save(os.path.join(pd, "05_blur_sensitivity.svg"))

    # 6. perspective sensitivity
    tl = sorted(measured(sel(base, experiment="E_TILT")),
                key=lambda r: r["pose_tilt_deg"] or 0)
    p = Plot("Perspective sensitivity", "view tilt (deg)", "signed error (mm)")
    p.hline(0.0, "zero")
    p.line([r["pose_tilt_deg"] for r in tl], [r["error_mm"] for r in tl],
           label="error")
    p.line([r["pose_tilt_deg"] for r in tl], [r["u_c_mm"] for r in tl],
           label="u_c", color="#148f56")
    abst = [r for r in sel(base, experiment="E_TILT") if r.get("status") != "MEASURED"]
    p.note("abstained: %s" % ", ".join("%.0fdeg/%s" % (r["pose_tilt_deg"],
                                                       r.get("failed_gate"))
                                       for r in abst) or "none")
    p.save(os.path.join(pd, "06_perspective_sensitivity.svg"))

    # 7. sampling density
    rh = sorted(measured(sel(base, experiment="E_RHO")),
                key=lambda r: r["rho_min_px_per_mm"] or 0)
    p = Plot("Sampling density sensitivity", "rho_min (px/mm)", "signed error (mm)")
    p.hline(0.0, "zero")
    p.line([r["rho_min_px_per_mm"] for r in rh], [r["error_mm"] for r in rh],
           label="error")
    p.line([r["rho_min_px_per_mm"] for r in rh], [r["u_c_mm"] for r in rh],
           label="u_c", color="#148f56")
    ab = [r for r in sel(base, experiment="E_RHO") if r.get("status") != "MEASURED"]
    p.note("abstained: %s" % (", ".join("z=%.0f/%s" % (r["pose_z_mm"], r.get("failed_gate"))
                                        for r in ab) or "none"))
    p.save(os.path.join(pd, "07_sampling_density.svg"))

    # 8. illumination / glare
    il = sel(base, experiment=("E_ILLUM", "E_NOISE"))
    p = Plot("Illumination, glare and noise conditions", "fixture", "signed error (mm)")
    p.hline(0.0, "zero")
    labs = [str(r["fixture_id"]).replace("E_ILLUM-", "").replace("E_NOISE-", "noise ")
            for r in il]
    p.bars(labs, [r.get("error_mm") if r.get("error_mm") is not None else 0.0
                  for r in il], label="error (0 = abstained)")
    p.note("abstained: %s" % (", ".join(str(r["fixture_id"]) for r in il
                                        if r.get("status") != "MEASURED") or "none"))
    p.save(os.path.join(pd, "08_illumination_glare.svg"))

    # 9. ink / edge spread
    isp = sorted(measured(sel(base, experiment="E_INKSPREAD")),
                 key=lambda r: r["ink_spread_mm"] or 0)
    p = Plot("Ink (edge) spread tracking", "rendered ink spread (mm)",
             "signed error vs true ink extent (mm)")
    p.hline(0.0, "zero")
    p.line([r["ink_spread_mm"] for r in isp], [r["error_mm"] for r in isp],
           label="error")
    p.note("ground truth includes the spread: a flat line means the estimator "
           "tracks the real ink boundary, not the nominal outline")
    p.save(os.path.join(pd, "09_ink_spread.svg"))

    # 10. abstention map
    gate_counts = {}
    for r in rows:
        if r.get("status") != "MEASURED":
            g = r.get("failed_gate") or "UNKNOWN"
            gate_counts[g] = gate_counts.get(g, 0) + 1
    p = Plot("Abstention causes (all runs)", "gate", "count")
    if gate_counts:
        ks = sorted(gate_counts, key=lambda k: -gate_counts[k])
        p.bars(ks, [gate_counts[k] for k in ks], label="abstentions")
    p.save(os.path.join(pd, "10_abstention_causes.svg"))

    # 11. decision guard band
    dec = sorted(sel(base, experiment="E_DECISION"), key=lambda r: r["true_h_mm"])
    p = Plot("Guard-band decisions around a fixed threshold",
             "true ink height (mm)", "height (mm)")
    thr = (dec[0].get("threshold_mm") if dec else 3.0) or 3.0
    p.hline(thr, "threshold", "#c0392b")
    mdec = [r for r in dec if r.get("status") == "MEASURED"]
    p.scatter([r["true_h_mm"] for r in mdec], [r["h_mm"] for r in mdec],
              label="estimate")
    p.errorbars([r["true_h_mm"] for r in mdec], [r["lower_mm"] for r in mdec],
                [r["upper_mm"] for r in mdec], label="interval", color="#c0392b")
    p.note("decisions: " + ", ".join("%s=%d" % kv for kv in
                                     sorted(S["C8_DECISION"]["tally"].items())))
    p.save(os.path.join(pd, "11_decision_guard_band.svg"))

    # 12. undetectable defects
    und = S["UNSAFE_UNDETECTABLE"]["per_fixture"]
    p = Plot("Defects a single view cannot detect", "fixture",
             "measured error (mm)")
    if und:
        p.bars([u["fixture_id"].replace("N_", "") for u in und],
               [abs(u["error_mm"]) if u.get("error_mm") is not None else 0.0
                for u in und], label="|error|", color="#c0392b")
    p.note("all of these were MEASURED, not abstained: geometry gates are blind "
           "to out-of-plane print, so the fixture must guarantee it")
    p.save(os.path.join(pd, "12_undetectable_defects.svg"))


def _markdown(report, S, out_dir):
    v = report["verdict"]
    sa = S["SAFE_ACCURACY"]
    L = ["# P0-min synthetic experiment result", "",
         "**Overall verdict: %s**" % report["overall"], "",
         "All criteria are pre-registered in `docs/P0_CRITERIA.md`.  Numbers below",
         "are measured on the synthetic harness, where ground truth is exact; they",
         "are NOT physical-camera results and are NOT a legal accuracy claim.", "",
         "## Verdict", "", "| Criterion | Result | Detail |", "|---|---|---|"]
    for k in sorted(v):
        res = "PASS" if v[k]["pass"] else ("WARN" if v[k].get("informational") else "FAIL")
        L.append("| %s | %s | %s |" % (k, res, v[k]["detail"]))
    L += ["", "## Accuracy on nominal (SAFE) conditions", "",
          "| quantity | value |", "|---|---|"]
    for key in ("n_runs", "n_measured", "measure_rate", "bias_mm", "mae_mm",
                "p95_abs_error_mm", "max_abs_error_mm", "median_burst_sd_mm",
                "coverage", "coverage_n", "median_interval_width_mm"):
        L.append("| %s | %s |" % (key, _f(sa.get(key), 5)))
    L += ["", "## Abstention on defects the gates target", "",
          "| fixture | status | stage | gate |", "|---|---|---|---|"]
    for r in S["UNSAFE_DETECTABLE"]["per_fixture"]:
        L.append("| %s | %s | %s | %s |" % (r["fixture_id"], r["status"],
                                            r.get("failed_stage"), r.get("failed_gate")))
    L += ["", "## Defects a single view cannot detect", "",
          "| fixture | status | error (mm) | u_c (mm) | covered | reproj RMS px | LOMO |",
          "|---|---|---|---|---|---|---|"]
    for r in S["UNSAFE_UNDETECTABLE"]["per_fixture"]:
        L.append("| %s | %s | %s | %s | %s | %s | %s |"
                 % (r["fixture_id"], r["status"], _f(r.get("error_mm")),
                    _f(r.get("u_c_mm")), r.get("covered"),
                    _f(r.get("reproj_rms_px"), 3), _f(r.get("lomo_rel_spread"), 5)))
    L += ["", "## Guard-band decisions", "",
          "| fixture | true (mm) | threshold | truly undersize | decision | interval |",
          "|---|---|---|---|---|---|"]
    for d in S["C8_DECISION"]["detail"]:
        iv = ("[%s, %s]" % (_f(d.get("lower_mm")), _f(d.get("upper_mm")))
              if d.get("lower_mm") is not None else "-")
        L.append("| %s | %s | %s | %s | %s | %s |"
                 % (d["fixture_id"], _f(d["true_h_mm"], 3), _f(d["threshold_mm"], 3),
                    d["truly_undersize"], d["decision"], iv))
    L += ["", "## Ablations", "",
          "| ablation | outcome |", "|---|---|",
          "| linearisation (linear) | err=%s |" % _f(S["C6_LINEARIZE"]["linear"].get("error_mm")),
          "| linearisation (gamma, end to end) | %s (gate %s) |"
          % (S["C6_LINEARIZE"]["gamma"].get("status"),
             S["C6_LINEARIZE"]["gamma"].get("failed_gate")),
          "| linearisation (gamma, glyph only) | err=%s |"
          % _f(S["C6_LINEARIZE"]["gamma_glyph_only"].get("error_mm")),
          "| undistortion on | err=%s reproj=%s px |"
          % (_f(S["E3_UNDISTORTION"].get("undistort_on", {}).get("error_mm")),
             _f(S["E3_UNDISTORTION"].get("undistort_on", {}).get("reproj_rms_px"), 3)),
          "| undistortion off | err=%s reproj=%s px |"
          % (_f(S["E3_UNDISTORTION"].get("undistort_off", {}).get("error_mm")),
             _f(S["E3_UNDISTORTION"].get("undistort_off", {}).get("reproj_rms_px"), 3)),
          "| estimator: fitted extreme | MAE=%s |" % _f(S["C5_ESTIMATOR"]["model_fit_mae_mm"]),
          "| estimator: max-minus-min | MAE=%s |" % _f(S["C5_ESTIMATOR"]["maxminus_min_mae_mm"]),
          ""]
    with open(os.path.join(out_dir, "RESULT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main() or 0)
