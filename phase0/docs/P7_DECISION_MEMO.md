# P7 specification — decision memo (STEP 3B)

**Purpose.** Give the project owner everything needed to fix the meaning of P7 *before*
any physical capture, so the criterion is never adjusted after seeing results.

**Status of this file.** Factual clarification only. It **changes no criterion, no
threshold, no configuration and no code**, and it deliberately **does not choose**
between the options in §8. `P0_CRITERIA.md` is untouched.

**Verdict: `P7_SPECIFICATION = RESOLVED` (STEP 3C) — Option C chosen.** The analysis in
§§1-8 stands as the record of *why*; §9 records the decision that was taken on it.

---

## 1. Exact current wording

`phase0/docs/P0_CRITERIA.md` line 33:

```
| P7 | Empirical interval coverage | CI includes nominal and lower bound >= 0.90 |
     widen interval and re-report | cannot be achieved -> report a band, not a
     confidence interval |
```

Columns are `ID | Criterion | Go | Conditional | No-go`.

### Provenance of the wording

| Source | Statement |
|---|---|
| `SOLUTION_LOCK_V2.md` line 1083 | "Empirical interval coverage \| **nominal 95%**; exact/cluster-bootstrap 95% CI must include **95%** and lower bound **≥90%** \| Report mean width" |
| `SOLUTION_LOCK_V2.md` line 414 | "**Nominal 95%** interval ka acceptance tabhi jab sealed test par two-sided 95% confidence bound empirical coverage ko **90–98% band** ke andar support kare; otherwise interval wording 'engineering uncertainty band' hoga." |

P7's Go cell is a compressed copy of line 1083, with the word `95%` replaced by the
word `nominal` and the band formulation of line 414 dropped. **The number that made the
sentence well defined was removed when it was copied.** That is the origin of the
problem.

---

## 2. Exact meaning of each term, with its source

### "covered" — unambiguous
`phase0/p0/results.py` line 63:

```python
covered = int(m["lower_mm"] <= true_h <= m["upper_mm"])
```

A run is covered when the reference value lies inside the **closed two-sided interval**
`[lower_mm, upper_mm]`. Both bounds must hold simultaneously. There is no one-sided
variant of `covered` anywhere in the codebase.

### The interval — unambiguous
`phase0/p0/uncertainty.py` lines 103–104, with `config/uncertainty_model_v1.json`:

```python
"lower_mm": h_corr - kl * u_c        # kl = k_lower = 1.645
"upper_mm": h_corr + ku * u_c        # ku = k_upper = 1.645
```

### "nominal" — **ambiguous; this is the defect**
Two different, individually correct figures exist for the same `k = 1.645`:

| Figure | Value | Source | What it describes |
|---|---|---|---|
| one-sided | `Φ(1.645) = 0.9500` | `P0_ASSUMPTIONS.md` A-07: "`k_lower = k_upper = 1.645` gives ~95 percent one sided coverage" | each single bound, separately |
| two-sided | `2Φ(1.645) − 1 = 0.9000` | `P0_CRITERIA.md` C4 rationale: "`k = 1.645` one sided each side is a **~90 percent two sided region** under normality"; and `PHASE0_REVIEW.md` line 236: "state karo ki `[L,U]` ek **90% two-sided region** hai" | the interval as a whole |

Both are arithmetically exact (verified: `2Φ(1.645)−1 = 0.9000`, `Φ(1.645) = 0.9500`).
Because `covered` tests the interval **as a whole**, the figure that matches the
statistic is **0.90**. The figure inherited from the V2 wording is **0.95**. P7 does not
say which one it means.

### "CI includes nominal"
`CI` is a confidence interval `[L, U]` for the *true coverage probability* `p`, estimated
from the observed proportion `k/n`. The current analyser uses a Wilson score interval at
95 %, explicitly recorded in its own output as
`"ci_method": "Wilson score interval, observations treated as independent (not clustered by panel)"`.
"Includes nominal" strictly means `L <= nominal <= U`.

### "lower bound >= 0.90"
`L >= 0.90`, i.e. the CI for the coverage probability must not extend below 0.90. Note
this is a **floor on the CI of the statistic**, not a floor on the statistic itself, and
it is therefore **sample-size dependent**.

---

## 3. The contradiction, stated precisely

There is **no contradiction between C4 and A-07**. They describe two different
properties of the same interval and both are correct: each bound is a 95 % one-sided
bound, and the pair is a 90 % two-sided region.

The contradiction is **inside P7**, and it has two independent parts:

1. **Referent.** P7 compares a two-sided statistic (`covered`) against an unnamed
   "nominal". The document offers 0.90 (matching the statistic) and 0.95 (matching the
   V2 ancestry). Choosing 0.95 means testing the interval against a target its
   construction was never intended to meet, since `k = 1.645` produces 0.90 two-sided.
2. **Self-blocking.** Under the referent that matches the statistic (0.90), the two
   clauses cannot both hold. Proof in §6.

---

## 4–5. Smallest interpretations consistent with the existing documents

No new science is introduced below; each row is a different way of reading the same
sentence.

### I1 — nominal = 0.90, both clauses, strict reading
* **Maths:** `L <= 0.90 <= U` **and** `L >= 0.90` ⟹ `L = 0.90` exactly.
* **Computable?** Formally yes, practically never satisfied (§6).
* **Protocol support:** yes, no split needed.
* **Doc change:** none.
* **Criteria change:** none — but the criterion is unusable, so this is not a viable option.

### I2 — nominal = 0.90, "includes" read as "not entirely below nominal"
* **Maths:** `U >= 0.90` **and** `L >= 0.90`. Since `L <= U`, this reduces to a single
  condition: **`L >= 0.90`**.
* **Computable?** **Yes, today**, from `lower_mm`, `upper_mm`, `true_h_mm` already in the
  schema. No schema change, no new field.
* **Protocol support:** yes.
* **Doc change:** P7's Go cell must be restated as the single surviving condition, with a
  note that the other clause is implied.
* **Criteria change:** the *numbers* do not move. Whether this counts as a change of
  substance is a judgement: it removes an upper check that was never satisfiable anyway.
* **Behaviour:** a one-sided calibration floor. Under-coverage fails; **over-coverage
  passes** (a conservative, too-wide interval is accepted). Requires `n >= 35` before
  even perfect coverage can pass (§6).

### I3 — nominal = 0.95, both clauses (the V2 ancestry)
* **Maths:** `L <= 0.95 <= U` **and** `L >= 0.90`.
* **Computable?** **Yes, today.** No schema change.
* **Protocol support:** yes, but only coherent if one accepts either (a) that P7
  deliberately demands the interval be more conservative than its own 0.90 construction,
  or (b) that `k` should become ≈1.96 so that nominal two-sided *is* 0.95 — and (b) is a
  **configuration change** that would also invalidate the committed synthetic result set.
* **Doc change:** P7 must state `nominal = 0.95` explicitly; C4's rationale and A-07
  should gain a cross-reference so the two figures are not read as interchangeable.
* **Criteria change:** no number moves, but the criterion becomes materially stricter
  than I2 and becomes **two-sided**: it rejects over-coverage as miscalibration.
* **Behaviour trap:** the two clauses pull in opposite directions as `n` grows (§6).

### I4 — P7 is a reporting obligation, not a pass/fail gate
* **Evidence:** P7's Conditional cell is an *action* ("widen interval and re-report") and
  its No-go cell is an *action* ("report a band, not a confidence interval") — neither is
  a threshold, unlike P1–P6 whose cells are all numeric bands. `A-07` states `k` is
  nominal and unvalidated and that the model "ships explicitly uncalibrated". The
  interval-width gate is already disabled for the same reason (`P0_CRITERIA.md` lines
  49–50). `PHASE0_VERDICTS.md` #38 keeps "coverage factor `k` from data ... freeze on
  development set, evaluate on sealed set", i.e. calibration is expected *after* the
  pilot.
* **Maths:** none. Report `k/n`, its CI, and the interval width; then take one of the two
  documented actions.
* **Computable?** **Yes, today**, fully.
* **Protocol support:** yes, and this is the only reading that is consistent with the
  uncertainty model shipping uncalibrated.
* **Doc change:** P7 restated as a reporting requirement, most naturally by moving it
  into the existing "Values that look like criteria but are not" section.
* **Criteria change:** **yes** — the gating set becomes P1–P6 and coverage becomes a
  reported quantity.

---

## 6. Is "CI includes nominal and lower bound >= 0.90" self-blocking?

**Under nominal = 0.90: yes, provably.**

The two clauses require `L <= 0.90` and `L >= 0.90` simultaneously, i.e. `L = 0.90`
exactly. `L` is a Wilson bound, a function of the integers `(k, n)`; hitting 0.90 exactly
is a measure-zero coincidence.

Exhaustive check over every `n` from 2 to 500 and every `k` from 0 to `n`
(125 249 combinations), using the analyser's own `wilson()`:

```
solutions satisfying BOTH  L <= 0.90 <= U  and  L >= 0.90 :  0
```

**Under nominal = 0.95: not self-blocking, but it contains a sample-size trap.** The two
clauses move in opposite directions as `n` grows:

| observed | `(k, n)` | Wilson 95 % CI | `L >= 0.90` | includes 0.95 | I3 verdict |
|---|---|---|---|---|---|
| 0.696 | (16, 23) | [0.4913, 0.8440] | no | no | fail |
| 1.000 | (23, 23) | [0.8569, 1.0000] | **no** | yes | fail — *perfect coverage, small n* |
| 0.900 | (216, 240) | [0.8555, 0.9319] | no | no | fail |
| 0.950 | (228, 240) | [0.9147, 0.9712] | yes | yes | **pass** |
| 1.000 | (240, 240) | [0.9842, 1.0000] | yes | **no** | fail — *perfect coverage, large n* |

So under I3 both a perfect small sample and a perfect large sample fail, and only
coverage close to 0.95 passes. That is a legitimate calibration test, but it must be
chosen knowingly.

**Smallest `n` at which perfect coverage can satisfy the 0.90 floor at all: `n = 35`**
(`L = 0.9011`). Any evaluation population below 35 runs cannot pass the floor under I2 or
I3 no matter how good the intervals are.

---

## 7. Can the protocol's cluster bootstrap and dev/held-back split produce the statistic?

`P0_PROTOCOL.md` lines 154–155: *"Empirical interval coverage; fit `k` on the development
split only and report coverage on the held-back split."*

| Requirement | Schema support | Verdict |
|---|---|---|
| **Cluster bootstrap by panel** | `panel_id` is present in physical result rows (appended by `run_real_batch.py`) but is **not** in the canonical `CSV_COLUMNS` list in `p0/results.py`; the repository has a deterministic `Rng` for a reproducible bootstrap | **Feasible**, but needs a pre-registered decision: cluster key, resample count, seed, and interval definition. With ~20 panels the cluster CI is coarse. The analyser currently records that it does *not* cluster. |
| **Development / held-back split** | **No split field exists** — not in `manifest_used.json`, not in `REQUIRED`, not in the manifest fields listed in `P0_EXECUTION_PLAN.md` §7.3, not in `CSV_COLUMNS` | **Not computable today.** A split label must be added to the manifest and assigned **before capture**; assigning it afterwards would be post-hoc selection, which §6.3 of the execution plan forbids. |
| **"fit `k`" then evaluate coverage** | `h_mm` **and** `u_c_mm` are both persisted, so bounds can be re-derived as `h ± k·u_c` for any `k` | **Feasible**, but the re-derived `covered` would differ from the committed `covered` column, so any such result must state which `k` produced it. Note this is calibration, and A-07 places it *after* the pilot. |
| **Split size** | — | If coverage is evaluated on a held-back split only, §6 implies that split must contain **≥ 35 evaluable runs** for the 0.90 floor to be reachable. |

**Conclusion for §7:** the cluster bootstrap is implementable without new science; the
development/held-back split is **not** implementable under the current schema and is an
additional pre-registration decision, separate from the wording decision in §8.

---

## 8. Options — presented, not chosen

### OPTION A — adopt I2: nominal = 0.90, Go reduces to `Wilson L >= 0.90`
* **Evidence:** matches how `covered` is actually computed (`results.py` line 63) and how
  the interval is actually built (`k = 1.645` ⟹ 0.90 two-sided, stated in C4 and in
  `PHASE0_REVIEW.md` line 236).
* **Consequences:** computable today with no schema change; one-sided floor;
  over-coverage accepted; needs `n >= 35`; P7's Go cell must be reworded; the unsatisfiable
  clause disappears.
* **Risk:** a too-wide (over-conservative) interval passes P7, so interval *width* is not
  policed by this criterion — and the width gate is currently disabled, so nothing else
  polices it either.

### OPTION B — adopt I3: nominal = 0.95, keep both clauses
* **Evidence:** the direct ancestor of the wording, `SOLUTION_LOCK_V2.md` line 1083.
* **Consequences:** computable today with no schema change; two-sided calibration test
  that rejects both under- and over-coverage; the `n`-dependent trap in §6 means perfect
  coverage fails at both small and large `n`; either accept that P7 is stricter than the
  interval's own construction, or change `k` to ≈1.96 — and changing `k` is a
  configuration change that would invalidate the committed synthetic result set.
* **Risk:** a good, conservative measurement system can fail P7 for reasons that have
  nothing to do with measurement quality.

### OPTION C — adopt I4: P7 becomes a reporting obligation, gating set becomes P1–P6
* **Evidence:** P7's own Conditional and No-go cells are actions rather than thresholds,
  unlike every other P-criterion; `A-07` says `k` is nominal and uncalibrated;
  `P0_CRITERIA.md` lines 49–50 already disable the interval-width gate for the same
  reason; `PHASE0_VERDICTS.md` #38 expects `k` to be fitted after the pilot.
* **Consequences:** computable today; nothing can be mis-accepted; the pilot reports
  coverage, its CI and interval width, and takes one of the two documented actions.
* **Risk:** the pilot then carries **no** pass/fail check on interval calibration, so the
  guard-band decision states rest on an unvalidated `k` until a later stage. This must be
  said explicitly in any claim.

### Orthogonal decision, required under all three options
Whether to (a) keep the independent Wilson interval the analyser already computes, or
(b) add the pre-registered cluster bootstrap, and whether (c) a development/held-back
split is used at all — which needs a new manifest field committed before capture (§7).

---

## 9. Final — decision taken (STEP 3C)

```
P7_SPECIFICATION = RESOLVED
Chosen option    = C  (P7 is reporting / calibration, not an acceptance gate)
```

### Why Option C

Options A and B both force a *pass/fail acceptance* out of a quantity the pilot is not
equipped to judge. The evidence in §4 (row I4) and §8 (Option C) is decisive:

* P7's own Conditional and No-go cells were **actions** ("widen interval and re-report",
  "report a band"), not numeric bands — unlike P1-P6, whose cells are all thresholds.
  The wording never described a gate.
* `A-07` states `k = 1.645` is **nominal and uncalibrated** and the model "ships
  explicitly uncalibrated". Turning uncalibrated coverage into a pass/fail gate would
  assert exactly the calibration the model does not have.
* The interval-width gate is **already disabled** for the same reason
  (`P0_CRITERIA.md` "Values that look like criteria but are not").
* `PHASE0_VERDICTS.md` #38 expects `k` to be fitted on a development set and evaluated on
  a sealed set — i.e. calibration is a **later** step, not this pilot's P7.
* Under the referent that matches the two-sided `covered` statistic (0.90), the old
  wording was provably unsatisfiable (§6: 0 of 125,249 (k, n) combinations); under 0.95
  it tested the interval against a target its own `k` cannot produce. Neither is a sound
  gate.

### What P7 now measures

Observed two-sided interval coverage `k/n` over the identified nominal population
(measured nominal runs that carry a reference value and both interval bounds), reported
with its Wilson 95 % CI, the sample count `n`, `k`, and the interval mean/median width.
The analyser emits status **`REPORT_ONLY`** (or `UNCOMPUTABLE` if there is nothing to
report). It can never emit `PASS`, `CONDITIONAL` or `FAIL`.

### What P7 does NOT establish

P7 does **not** produce a physical-accuracy pass/fail for this pilot; the accuracy gates
are **P1-P6**. It does **not** validate or calibrate the uncertainty model, and no output
may describe the model as "validated" or "calibrated".

### Why k stays uncalibrated

`k_lower = k_upper = 1.645` is preserved unchanged. It remains nominal; this pilot only
*collects* empirical coverage as calibration evidence. Fitting `k` on a development split
and evaluating on a sealed split (`P0_PROTOCOL.md` §6, `PHASE0_VERDICTS.md` #38) is a
distinct, later calibration step that this reporting-only P7 does not perform, so no
development / held-back split is introduced now.

### Consequence for the pilot

Blocker **B1 is CLOSED**: P1-P6 are computed and tested against the frozen bands, and P7
is now explicit, testable and pre-registered as reporting-only. The one honest cost,
stated plainly: **the pilot carries no pass/fail check on interval calibration**; any
claim must say the guard-band decision rests on an unvalidated `k` until a later
calibration stage.
