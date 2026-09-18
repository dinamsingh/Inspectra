# P0-min PASS / FAIL criteria (pre-registered)

These criteria are constants in `tools/analyse_results.py` (`CRIT`).  They were
fixed before the experiment was run and must not be changed in response to
results.  If a criterion fails, the response is to narrow the claim or fix the
engineering -- never to move the threshold.

## Synthetic stage (runs today)

| ID | Criterion | Threshold | Why this number |
|---|---|---|---|
| C1 | Arithmetic exactness on ideal renders (`E_MATH`) | max abs error <= 0.010 mm | With zero blur/noise/spread the only error source is the pipeline's own maths; 0.010 mm is ~1/6 pixel at 18 px/mm |
| C2 | Accuracy on nominal SAFE conditions | abs bias <= 0.030 mm AND P95 abs error <= 0.060 mm | One fifth of the review's physical MAE target (0.15 mm); synthetic data has no ink/ISP physics so it must be much tighter |
| C3 | Burst repeatability | median burst SD <= 0.030 mm | Same reasoning as C2 |
| C4 | Interval coverage | >= 0.90 of SAFE runs contain truth | `k = 1.645` one sided each side is a ~90 percent two sided region under normality |
| C5 | Estimator choice is justified | fitted-extreme MAE < max-minus-min MAE | Falsifiable test of the decision to abandon `max - min` |
| C6 | Linearisation matters | abs(error) with gamma-space threshold > abs(error) with linear | Falsifiable test of the sRGB EOTF decision |
| C7 | Defects the gates target are caught | abstention rate = 1.00 on `UNSAFE_DETECTABLE` | A single silent acceptance invalidates the abstention claim |
| C8 | Decision safety | zero false clears among truly undersized panels | The unsafe direction for an enforcement tool |
| C9 | Undetectable defects documented | informational; error must be reported | Proves these need fixture control, not gates |
| C11 | Usable measure rate on SAFE | >= 0.80 | Gates that abstain on everything are useless even if "safe" |

## Physical stage (requires the 20-panel pilot; NOT yet run)

| ID | Criterion | Go | Conditional | No-go |
|---|---|---|---|---|
| P1 | Reference cross-method agreement (scanner vs microscope, >= 15 glyphs) | <= 0.03 mm | 0.03-0.06 mm | > 0.06 mm -> no accuracy claim is possible |
| P2 | Residual SD after one global bias correction (3 mm class) | <= 0.08 mm | 0.08-0.15 mm | > 0.15 mm |
| P3 | Repeatability SD (same panel, device, operator) | <= 0.05 mm | 0.05-0.10 mm | > 0.10 mm |
| P4 | Inter-device bias after global correction | <= 0.05 mm | 0.05-0.12 mm | > 0.12 mm -> per-device claim only |
| P5 | Gate acceptance in nominal conditions | >= 0.70 | 0.50-0.70 | < 0.50 -> redesign fixture/protocol |
| P6 | Unsafe-condition acceptance (stress block) | <= 0.02 | 0.02-0.05 | > 0.05 -> abstention unsafe |
| P7 | Empirical interval coverage (REPORTING / CALIBRATION, not a pass/fail gate) | REPORT_ONLY: report observed two-sided coverage k/n, its Wilson 95% CI [L, U], and n, for the identified nominal population | report interval mean/median width alongside | (no No-go: P7 never fails the pilot) |

### P7 is a reporting / calibration criterion, not an acceptance gate (RESOLVED, Option C)

P7 was frozen as **reporting-only** by the STEP 3C decision (see
`P7_DECISION_MEMO.md` §9 and `P0_EXECUTION_PLAN.md` §10). It exists to *report*
empirical interval coverage as calibration evidence for the uncertainty model, and it
**does not produce a PASS / FAIL for physical accuracy in this pilot**. The pilot's
accuracy acceptance gates are **P1-P6 only**.

Frozen definition:

* **statistic:** `observed_coverage = k / n`, where a run is *covered* when
  `lower_mm <= reference_h_mm <= upper_mm` (the existing two-sided `covered`,
  `p0/results.py`).
* **interval on the statistic:** Wilson score 95% CI `[L, U]` on `k / n`, observations
  treated as independent (not clustered) - the method the analyser already computes and
  labels. No development / held-back split is used for this reporting-only P7; the split
  in `P0_PROTOCOL.md` §6 belongs to a later *calibration* step, not to this pilot's P7.
* **also reported:** `n` (sample count), the identified nominal population, `k`
  (n covered), and the interval mean/median width.
* **status vocabulary:** `REPORT_ONLY` when the coverage evidence is produced;
  `UNCOMPUTABLE` only when there is no evaluable run at all. P7 can never be `PASS`,
  `CONDITIONAL` or `FAIL`.

Uncertainty-model status (unchanged, preserved verbatim from `A-07`): the interval uses
`k_lower = k_upper = 1.645`; this `k` is **nominal and currently uncalibrated**. P7
collects empirical coverage as calibration evidence; **this pilot does not establish a
validated or calibrated confidence interval**, and no output may describe the model as
"validated" or "calibrated".

Why the earlier wording was wrong: "CI includes nominal and lower bound >= 0.90" named
no numeric "nominal" (0.90 two-sided vs 0.95 one-sided are both defensible readings of
the same `k = 1.645`), and under the 0.90 reading the two clauses were mutually
exclusive (`P7_DECISION_MEMO.md` §6: 0 solutions across 125,249 (k, n) combinations).

**Conditional** means proceed with a narrower claim (per device, per font class,
wider interval, higher abstention).  **No-go** means do not build the Android
measurement feature and do not put a millimetre claim in any presentation.

## Values that look like criteria but are not

Added by the consistency audit, because these three are commonly misread:

* **`min_rho_px_per_mm = 10.0`** is a pre-registered gate **floor**, not the capture
  target. The target is `>= 16 px/mm` (`P0_PROTOCOL.md` §4). See `P0_ASSUMPTIONS.md` A-17.
* **`max_view_tilt_deg = 30.0`** gates *view obliqueness*, which is observable from the
  homography. It is **not** the local print-plane tilt limit; that is not observable
  from one view (A-06) and is carried as `residual_tilt_bound_deg = 3.0` in the
  uncertainty model plus a fixture requirement.
* **The interval-width gate is disabled** (`max_interval_width_mm = null`) until the
  uncertainty model is calibrated. It is reported as `evaluated: false`, never as a pass.

`gate_policy_v1.json` deliberately carries `policy_id: "GP-v2"` -- file path is the
slot, `policy_id` is the revision (A-18).

## Hard stops

1. C1 fails -> the pipeline maths is wrong; fix before any physical work.
2. P1 fails -> there is no usable ground truth; no accuracy claim at all.
3. P2 or P6 fails -> the measurement claim must be downgraded.
4. P5 fails -> the capture protocol, not the threshold, must change.

## Prohibited responses to a failure

* Loosening a gate so that more runs pass.
* Re-labelling an `UNSAFE_DETECTABLE` fixture as diagnostic *without* evidence
  that the condition does not actually corrupt the measurement.  (This did happen
  once and is documented: see `out/synthetic_v1` and the halftone pitch sweep.)
* Dropping abstained runs from an accuracy denominator without reporting the
  abstention rate alongside.
* Reporting a target as an achieved result.
