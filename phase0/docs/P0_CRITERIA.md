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
| P7 | Empirical interval coverage | CI includes nominal and lower bound >= 0.90 | widen interval and re-report | cannot be achieved -> report a band, not a confidence interval |

**Conditional** means proceed with a narrower claim (per device, per font class,
wider interval, higher abstention).  **No-go** means do not build the Android
measurement feature and do not put a millimetre claim in any presentation.

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
