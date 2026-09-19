# Reference (ground-truth) measurement procedure — blocker B2

**Scope:** defines how the reference values that P1 compares, and that P2/P3/P4 are
measured against, are produced. Closes the *methodological* half of B2 and states exactly
what remains.

**Changes nothing else:** no measurement algorithm, no `config/`, no P1-P7 threshold, no
Solution Lock. B3-B6 are untouched.

**STEP 4B** froze the two open human decisions: **M1** (§4.2, microscope edge criterion)
and **S3** (§3.2, resolved as **NO** — the fiducial frame is not scanned with the coupon).

**Verdict: `B2 = NOT CLOSED`** — the residual blockers in §11 are now equipment and
software, not undecided procedure.

---

## 1. Instrument audit

Only documented properties are listed. Anything the repository does not state is marked
**UNRESOLVED** rather than assumed.

| Instrument | What it can actually measure | Same measurand as the phone pipeline? | Documented resolution / limit | Can serve as reference? |
|---|---|---|---|---|
| **Flatbed scanner, 2400 dpi** (`P0_PROTOCOL.md` §0, §3) | a sampled greyscale image of the panel at 94.5 px/mm; a length only *after* an estimator extracts an ink boundary from it | **Yes, if and only if** the 50 % linearised-luminance estimator is run on the scan — which is what `P0_PROTOCOL.md` §3 step 3 instructs ("the same estimator") | 2400 dpi ⇒ 1 px = **0.0106 mm**. The stated reference uncertainty target is **≤ 0.01 mm**, i.e. *below one pixel*, so subpixel estimation is mandatory, not optional | **Yes — primary**, for every camera-measured glyph |
| **Measuring / toolmaker's microscope** (§0, §3) | the distance between two positions a human operator sets crosshairs to, on a magnified image | **No — a different realisation.** A human judges a *visually apparent* ink edge; that is not a 50 % crossing of a linearised luminance profile. The two coincide only approximately | Edge criterion, illumination, baseline realisation, repeats and aggregation are **frozen** by **M1** (§4.2). Still **UNRESOLVED**: magnification and stage reading resolution (**M2**), operator training (**M5**). `PHASE0_REVIEW.md` §15 records ~1-2 µm for a micrometer-stage toolmaker's microscope and ~0.01 mm for a USB microscope with a calibration slide | **Yes — independent cross-check only** (P1) |
| **Digital caliper**, 0.01 mm, with calibration record (§0) | external/internal distances between physical anvils | **No** | 0.01 mm resolution (documented) | **No** for glyphs — `P0_EXECUTION_PLAN.md` §2.3 already lists "caliper across a 3 mm printed glyph" as *never a reference*. Its documented role is frame survey and frame thickness |
| **Certified steel scale / glass graticule** (§0) | a certified length, used to calibrate the scanner's scale in both axes | n/a — it calibrates, it does not measure glyphs | **UNRESOLVED**: certificate class / stated uncertainty not specified | **No** directly; it is a prerequisite for the scanner path |

**Is another independent method needed?** Not by the current documents. The documented
design is two-tier: the scanner is the *primary* reference for every measured glyph, and
the microscope is the *independent* cross-check on a subset. §2 explains what each tier
does and does not test.

---

## 2. Measurand independence

Phone measurand (`config/measurand_policy_v1.json`):
`VISIBLE_PRINTED_INK_EXTENT_PERPENDICULAR_TO_BASELINE`, at
`boundary_fraction = 0.50` on `linearization = SRGB_EOTF`.

### Can scanner + microscope measure the same ink-boundary definition?

* **Scanner: yes, by construction** — but only because the protocol runs *the pipeline's
  own estimator* on the scan. The scan is, in the protocol's words, "just a very high-rho
  capture": ~94.5 px/mm versus ~16-18 px/mm for the phone, fronto-parallel, no lens
  distortion. Same definition, different sampling.
* **Microscope: no.** It realises a *visually judged* ink edge. Nothing in the repository
  defines a photometric 50 % criterion for an eyepiece measurement, and a human cannot
  apply one. This is not a defect to be papered over — it is precisely what P1 is for.

### Can the phone pipeline's own estimator be reused?

For the **scanner**, yes: `P0_PROTOCOL.md` §3 step 3 explicitly instructs it. For the
**microscope**, no — reuse would defeat the cross-check.

### If reused, does that create shared estimator bias?

**Yes, and it is quantified.** With the same estimator on both sides, any
estimator-*definitional* bias is common mode and cancels. The synthetic run already
measured such a bias: `RING_O` carried a **0.0054 mm** apex-fit error on ideal,
noise-free renders (`out/synthetic/analysis/analysis.json`, `E_MATH` by shape). Comparing
phone-with-estimator against scanner-with-estimator is therefore **blind** to that
component.

Consequence, which must appear in any result statement:

> **P2, P3 and P4 compare the phone pipeline against the same estimator running on a
> higher-resolution capture. They bound sampling-, blur-, perspective- and
> device-dependent error. They do not test whether the 50 % ink-boundary definition is
> itself correct. Only P1 does.**

### What must be independent?

1. **Algorithm chain:** at least one member of every cross-check pair must be produced by
   a procedure that does **not** execute the pipeline estimator. Enforced by
   `tools/validate_reference_table.py` (`PAIR_NOT_INDEPENDENT`,
   `MICROSCOPE_NOT_INDEPENDENT`).
2. **Observer:** per `P0_EXECUTION_PLAN.md` §8, whoever performs the microscope
   cross-check should not be the person who produced the scanner numbers for those
   glyphs, and must not see the scanner values first.
3. **What is *not* required to be independent:** the scanner tier. Its dependence is
   deliberate, documented and disclosed above.

---

## 3. Scanner procedure (primary reference)

### 3.1 Documented and therefore frozen

1. **Scale calibration** — calibrate the scanner's scale in **both axes** against the
   certified scale/graticule; record the scale factors and any non-uniformity across the
   platen (`P0_PROTOCOL.md` §3 step 1).
2. **Panel preparation** — the coupon is mounted flat on the rigid backing plate
   (§1/§5); scan it **flat** (§3 step 2).
3. **Scan settings** — 2400 dpi, **8-bit greyscale**, all enhancement off (§3 step 2).
4. **Measurement** — run the *same estimator* as the pipeline; record the procedure and
   the **software version used** (§3 step 3).
5. **Population** — all 400 glyph instances is the target; any reduction must be
   **pre-declared** (the protocol's own example: one shape per height per panel = 100
   glyphs) and recorded with the results. Never decided after seeing camera data (§3
   step 3).
6. **Uncertainty target** — ≤ 0.01 mm, about one third of the intended system
   uncertainty (§3 step 4).
7. **Recording** — one row per (glyph, method) into the append-only reference table, §6.

### 3.2 S3 — fiducial frame in the scan: **FROZEN (STEP 4B) as NO**

> **S3.** The coupon is scanned **without** the fiducial frame. Metric scale for the scan
> comes from the scanner's own calibrated dpi, verified against the certified length
> standard in both axes exactly as `P0_PROTOCOL.md` §3 step 1 already requires. That
> sentence stands unchanged and needs no reconciliation.

`B2_MINIMUM_SETUP.md` §5.2 previously flagged the opposite route — scanning the frame with
the coupon — as the most promising simplification, on the strength of `A-08` ("metric scale
comes from the surveyed fiducial, not the imaging device") and of §2.5 raising the option.
Working it through in detail **rejects it**, for a reason that is fatal rather than
inconvenient:

**The frame would have to sit on top of the print, and correcting for that requires a
scanner working distance that no document provides.** The frame is a physical overlay; its
markers are one frame-thickness closer to the imaging side than the ink. The pipeline
already handles this — `p0.uncertainty.thickness_correction(h_mm, thickness_mm, z_mm)`
applies a factor of `1 + d/Z`, and the `PLANARITY` gate limits `thickness_over_z` to
`0.01` — but **both need `Z`**, and for a scan `Z` is not measurable from the image
(`z_estimate_mm` just returns `f_px / rho`, so whatever focal length is asserted fixes it).
Asserting a scanner `Z` is inventing an equipment specification.

The exposure is not academic. Using the repository's own thick-frame certificate,
`config/frames/FRAME-SYN-0002-THICK.json`, `thickness_mm = 0.45`:

| Asserted `Z` | `thickness_over_z` | `PLANARITY` gate (limit 0.01) | Scale error carried on a 3 mm glyph |
|---|---|---|---|
| 200 mm (the phone's actual working distance) | 0.00225 | passes | 0.0068 mm — the value the synthetic runs actually record |
| 50 mm (a plausible folded-path flatbed guess) | 0.00900 | **passes** | **0.0270 mm — 90 % of P1's entire Go band, undetected** |

So a wrong guess at `Z` produces a reference value biased by most of the P1 Go band while
every gate reports green. Two escape routes were checked and both fail on the frozen
design:

* **Make the frame coplanar with the print (d = 0).** The frame window is 50 × 20 mm
  (`tools/make_configs.py`: `WINDOW`) and a coupon is 95 × 55 mm
  (`tools/make_coupons_svg.py`: `COUPON`), so the coupon cannot sit *inside* the window.
* **Print the frame onto the coupon sheet so both are one surface.** This contradicts the
  frame's stated requirement — `P0_PROTOCOL.md` §0: polyester film or laser-engraved
  acrylic, "dimensional stability matters more than print quality" — and would require
  changing the coupon layout, which is frozen (`P0_EXECUTION_PLAN.md` §1).

**What S3 = NO costs, stated plainly:**

* the certified length standard (steel scale / glass graticule with a certificate) stays
  **unconditionally required**. `B2_MINIMUM_SETUP.md` item 3b is withdrawn;
* **S4** (platen non-uniformity) is *not* softened. Scale now depends on the platen, so S4
  becomes more important, not less;
* **S1** and **S2** are not closed by reuse of `run_real_batch.py`.

**What S3 = NO gains:**

* the scanner tier stays independent of the frame-survey chain, so **P2/P3/P4 remain
  sensitive to frame-survey scale error** (≈ 0.0005-0.0006 mm on a 3 mm glyph per
  `PHASE0_VERDICTS.md` #14 and `P0_EXECUTION_PLAN.md` §13). That blindness is avoided
  rather than accepted;
* `P0_PROTOCOL.md` §3 step 1 is left exactly as frozen — no documentation reconciliation,
  no frozen-design change, and no asserted scanner optics anywhere in the chain.

**Reopening condition:** if a scanner's optical geometry is ever characterised traceably —
so that `Z`, or a demonstrated telecentricity, is *measured* rather than asserted — S3 may
be revisited. Until then it is closed as NO.

### 3.3 Still UNRESOLVED — required parameters the repository does not specify

None of these may be invented; each is a decision for the project owner.

| # | Missing parameter | Why it blocks execution |
|---|---|---|
| S1 | **Which software implements "the same estimator" on a scan.** Now *specified but unimplemented*: with S3 = NO, the scan is processed by building a pure-scale homography from the calibrated dpi and a zero-distortion `Camera`, which `B2_MINIMUM_SETUP.md` §4 verified is a mathematically **exact** representation of a fronto-parallel scan (ρ spread 0.000e+00 px/mm, anisotropy 1.000000). `p0.measure.measure_glyph` already accepts a caller-supplied `H`, so no measurement code changes. It is still not written, and there is no scan to validate it against | Without it there is no way to produce a single scanner reference value |
| S2 | **How the glyph is located in the scan** (the ROI). With no frame in the scan there is no fiducial and no ROI-selection path | Same class of problem as B3, but for scans; not solvable here |
| S4 | **How platen non-uniformity is applied** — recorded per §3 step 1, but no correction rule is given. S3 = NO makes this the load-bearing scale term | A recorded-but-unapplied correction is not a correction |
| S5 | **Repeat scans per panel**, and whether `n_repeats` aggregates repeats or repeated readings of one scan | Affects the stated `reference_u_mm` |
| S6 | **Baseline direction on a scan** — the measurand is perpendicular to the fitted baseline. `p0.measure.estimate_baseline_dir` exists and is the obvious candidate, but nothing states that it is to be used on a scan, and S3 = NO does not settle it | Perpendicularity is part of the measurand |

---

## 4. Microscope procedure (independent cross-check)

### 4.1 Documented and therefore frozen

* **Subset size:** `>= 15` glyphs (P1 criterion text), **spanning heights and fonts**
  (`P0_PROTOCOL.md` §3) — `P0_EXECUTION_PLAN.md` §2.3 adds *shapes*.
* **Statistic:** mean absolute scanner-vs-microscope difference = **P1**.
* **Independence:** must not execute the pipeline estimator (§2, §5).
* **Recording:** one row per glyph into the same append-only table, §6, with
  `measurement_procedure = MANUAL_VISUAL_CROSSHAIR`.
* **Glyph identity:** the same canonical `glyph_id` as the scanner row, so the pair is
  unambiguous (§10).

### 4.2 M1 — edge criterion: **FROZEN (STEP 4B)**

#### 4.2.1 The honest starting point: the microscope cannot reproduce the photometric rule

**Stated plainly, because it must not be papered over:** a human at an eyepiece has no
access to linearised luminance. The pipeline's boundary is the 50 % crossing of an
`SRGB_EOTF`-linearised profile (`config/measurand_policy_v1.json`,
`boundary_fraction: 0.50`). **No manual procedure can reproduce that**, and M1 does not
claim to. M1's job is to realise the *same physical ink edge* by a different route, so
that the difference between the two realisations is measurable — which is exactly what
**P1** is defined to measure.

#### 4.2.2 Why a *perceived-darkness* rule is rejected — on the repository's own numbers

The tempting rule is "put the crosshair where the tone looks half-dark". It is rejected,
because the repository already quantifies how expensive a misplaced boundary criterion is.
The pipeline computes `h_mm_sensitivity` at the policy's
`sensitivity_fractions: [0.4, 0.6]`, and `h_sensitivity_dev_mm` records how far the height
moves when the boundary fraction shifts by ±0.10. Over the **497** measured frames in
`out/synthetic/runs/*/result.json`:

| statistic | `h_sensitivity_dev_mm` (Δfraction = ±0.10) | implied slope d*h*/d*f* |
|---|---|---|
| min | 0.00866 mm | — |
| **median** | **0.02714 mm** | **0.2714 mm per unit fraction** |
| p95 | 0.05801 mm | — |
| max | 0.13078 mm | — |
| median over the 63 no-blur, no-sharpening frames | 0.02222 mm | 0.2222 mm per unit fraction |

Consequences, using only these numbers and the frozen P1 bands:

* a criterion sitting **Δ*f* = 0.10** away from 0.50 contributes **0.0271 mm** — almost
  the whole P1 Go band (0.03 mm) *before any real disagreement is measured*;
* standard lightness models place the *perceptually* mid-grey point far below half
  luminance, i.e. Δ*f* of order 0.2. At Δ*f* = 0.18 the contribution is **0.0489 mm**,
  which lands P1 in its **Conditional** band (0.03-0.06 mm) **by construction**;
* to keep the criterion's contribution under the protocol's own reference-uncertainty
  target of 0.01 mm (§3.1 item 6), |Δ*f*| must stay below **0.037**.

Two caveats, so these figures are not over-read: the lightness argument uses a standard
colorimetric model that is **not** in this repository, so it establishes only the
*direction and rough scale*; and the sensitivities were measured at ρ ≈ 18 px/mm with
phone blur, whereas a microscope resolves a narrower, purely physical ink transition, so
the same Δ*f* produces a *smaller* offset under the microscope. **No correction is derived
from any of this.** It is used only to reject a rule and to justify the one below.

#### 4.2.3 M1, frozen: symmetric transition-band bisection

> **M1.** Along a line perpendicular to the fitted baseline, the operator sets **two**
> crosshair positions at each edge of the glyph:
>
> * **O** — the outermost position at which the substrate shows **no ink tone at all**;
> * **I** — the innermost position at which the tone **stops deepening** (full ink
>   density; moving further inward darkens nothing).
>
> The boundary estimate for that edge is the arithmetic midpoint **(O + I) / 2**. The
> height is the separation of the two edge midpoints.

**Why this preserves measurand intent without photometry:** `P0_ASSUMPTIONS.md` **A-11**
states the working assumption that the transition is symmetric, and that this is precisely
what "preserves the 50 percent crossing". Under a symmetric transition the *geometric*
midpoint of the transition band **is** the 50 % crossing. So bisection targets Δ*f* = 0 by
construction, using only a judgement a human can actually make — *where does tone begin*
and *where does it stop changing* — instead of a judgement a human cannot make, namely
*where is tone exactly half*.

It also makes the rule insensitive to the thing that varies most between operators and
instruments: the *apparent width* of the transition band. Widening or narrowing the band
symmetrically does not move its midpoint — asserted by
`test_bisection_is_invariant_to_the_band_width`.

**Residual comparability limitation, which must be carried in any result statement:**
real dot gain is asymmetric (**A-10**: "real dot gain is anisotropic, substrate dependent
and not a constant offset"; **A-11**: real asymmetric effects shift the boundary). Where
the transition is asymmetric, the bisected midpoint and the photometric 50 % crossing do
**not** coincide, and the residual offset is not corrected and not individually knowable.
**That residual is what P1 reports.** P1 therefore remains a bound on realisation
disagreement, never a proof that either realisation is correct.

#### 4.2.4 Operating detail, frozen with M1

| Item | Frozen rule | Basis |
|---|---|---|
| **Illumination** | reflected / episcopic. Transmitted illumination is not permitted: opaque coupon stock makes it meaningless and it would image the substrate, not the ink | derived from the opaque-stock requirement (`P0_PROTOCOL.md` §0 coupons on print stock); flagged as derived, not quoted |
| **Baseline** | rotate the stage until the glyph baseline is parallel to the stage X axis; verify by traversing to two separated points on the baseline and confirming the Y reading repeats. Record the residual misalignment | resolves **M3**; the pipeline's analogue is `p0.measure.estimate_baseline_dir` |
| **Perpendicularity** | after alignment, the height is the **Y-axis** separation of the two edge midpoints | the measurand is perpendicular to the baseline (§2) |
| **Where to read — `FLAT_TOP`** (`BAR_I`, `H`, `T`) | on the flat top, at mid-stroke width, away from corners and serifs | `shape_classes` in `config/measurand_policy_v1.json` |
| **Where to read — `ROUND`** (`RING_O`) | at the single visually highest point (the apex), matching the pipeline's apex-window estimator (`apex_fit_window_frac: 0.35`). Note the pipeline side carries a documented **0.0054 mm** apex-fit bias on `RING_O` even on ideal renders, and P1 will see it | §2, `out/synthetic/analysis/analysis.json` |
| **Repeats** | **≥ 3 independent re-settings** per glyph: crosshairs backed fully off and re-set, never re-read from one setting | resolves **M4**; 3 is the floor at which a Type-A standard deviation exists, not an accuracy claim |
| **Aggregation** | `reference_h_mm` = mean of the per-repeat heights; `reference_u_mm` = *s*/√*n* (Type A) | resolves **M4**; `P0_PROTOCOL.md` §3 step 4 states the ≤ 0.01 mm target this must be reported against |
| **Recording** | all four positions of every re-setting go into `raw_readings` as `Obot/Ibot/Itop/Otop`, repeats separated by `;`, so the recorded value can be re-derived | §6; enforced by `tools/validate_reference_table.py` |

**Baseline-alignment tolerance, derived not decreed:** a residual misalignment θ makes the
Y separation under-read by *h*(1 − cos θ). On a 3 mm glyph that is 0.00046 mm at 1°,
0.00183 mm at 2°, 0.00411 mm at 3° and 0.01142 mm at 5°; on a 6 mm glyph it doubles.
Alignment to within a couple of degrees is therefore ample, and 5° is not. No gate is
created from this; the residual is recorded so its contribution is auditable.

#### 4.2.5 Ambiguity and failure

* **Ambiguous edge** — if **O** and **I** cannot be placed as two *distinct, repeatable*
  positions (band not resolvable, or so ragged that a midpoint is not meaningful), the
  operator does **not** guess a single edge. The row is recorded with
  `cross_check_status = UNUSABLE` and a mandatory note. The validator rejects `UNUSABLE`
  without a note.
* **Edge not identifiable at all** (glyph damaged, ink void, wrong glyph found) — same
  treatment: `UNUSABLE` plus the reason. The row is retained; it is never deleted.
* **Disagreement between repeats** — every reading is kept in `raw_readings`. A reading is
  never dropped to tighten the spread. If a re-setting is judged invalid (operator slip,
  wrong glyph), the correction is a **new row** that supersedes the old one by timestamp
  (§6); rows are never edited.
* **Per-glyph scanner-vs-microscope disagreement** stays governed by §9, and its
  threshold **D1 remains UNRESOLVED**. M1 does not close D1.

#### 4.2.6 M1 operator checklist

```
BEFORE THE FIRST GLYPH
[ ] Read M1 (§4.2.3) and confirm the two-crosshair rule is understood
[ ] Reflected (episcopic) illumination set; no transmitted light
[ ] Magnification and stage reading resolution recorded (M2 -- still your choice)
[ ] You have NOT seen any scanner value or any phone result for these glyphs (R6)
[ ] Instrument id + calibration certificate reference written down

PER GLYPH
[ ] Locate the glyph by panel_id + shape + nominal height + glyph_index; write glyph_id
[ ] Rotate the stage until the baseline is parallel to X; verify at two separated
    points that the Y reading repeats; record the residual
[ ] FLAT_TOP: read at mid-stroke on the flat top.  ROUND: read at the apex
[ ] BOTTOM edge: set O (last clean substrate), then I (tone stops deepening)
[ ] TOP edge: set I (tone stops deepening), then O (first clean substrate)
[ ] Write all four readings; height = midpoint(top) - midpoint(bottom)
[ ] Back the crosshairs fully off and repeat the whole reading >= 3 times
[ ] reference_h_mm = mean of the repeat heights; reference_u_mm = s/sqrt(n)
[ ] If O and I are not distinct and repeatable: cross_check_status = UNUSABLE + note
[ ] Never edit a written row; a correction is a new row

AFTER THE BATCH
[ ] python3 tools/validate_reference_table.py --table <csv> --agreement
[ ] Confirm 0 ERRORs and no MICROSCOPE_WITHOUT_RAW_READINGS warnings
```

### 4.3 Still UNRESOLVED after STEP 4B

| # | Missing parameter | Why it is not decided here |
|---|---|---|
| M2 | **Magnification and stage reading resolution** | Instrument-dependent, and no instrument is available. `B2_MINIMUM_SETUP.md` §2.3 gives the derived guide that a reading step *d* contributes about *d*/4 to P1 (0.01 mm step → 8.3 % of the Go band; 0.05 mm step → 41.7 %). `PHASE0_REVIEW.md` §15 records the two documented candidate classes: a micrometer-stage toolmaker's microscope at ~1-2 µm, or a USB microscope with a calibration slide at ~0.01 mm, the latter listed as "acceptable secondary". Choosing between them requires knowing what can be borrowed |
| M5 | **Operator training / inter-operator agreement** before the cross-check counts | Needs two people **and** the instrument in hand; it cannot be established on paper. M1 is now written, which is the prerequisite for training against it |

**M3 and M4 are resolved** by §4.2.4. **M1 is resolved** by §4.2.3.

---

## 5. Reference independence rule (enforced)

> **R1.** A `MICROSCOPE` row may never declare `measurement_procedure` =
> `PIPELINE_ESTIMATOR_ON_SCAN`.
>
> **R2.** For every glyph that has both methods, **at least one** row must use a
> non-pipeline procedure. A pair in which both sides ran the pipeline estimator cannot
> support P1 and is rejected.
>
> **R3.** A `SCANNER_2400DPI` row *may* use the pipeline estimator; when it does, every
> result statement must carry the disclosure in §2 ("P2/P3/P4 do not test the ink-boundary
> definition; only P1 does").
>
> **R4.** `measurement_procedure = UNRESOLVED` is rejected: a row whose procedure is
> undeclared is not a reference.
>
> **R5.** Observer independence and blinding per `P0_EXECUTION_PLAN.md` §8 — procedural,
> not machine-enforceable.
>
> **R6 (STEP 4B).** The microscope operator must not, while producing a reference value:
> (a) execute the pipeline estimator; (b) hold or consult any phone-derived height for
> those glyphs; or (c) be the person who produced the scanner rows for those glyphs.
> `P0_EXECUTION_PLAN.md` §8 states (c) as a **should**, so a glyph whose two methods share
> an operator is reported as a `WARN` (`SAME_OPERATOR_BOTH_METHODS`), not rejected —
> a single-person team is possible, but the sharing must be visible in the record.
> (a) and (b) are not machine-detectable; the mitigation is the recording order in
> `P0_EXECUTION_PLAN.md` §8 — microscope readings first, blind.

R1, R2, R4 and the reportable part of R6 are enforced by
`tools/validate_reference_table.py` and covered by `tests/test_reference_table.py`.
**M1 auditability** is enforced too: a microscope row's `raw_readings` must re-derive its
own `reference_h_mm` through the §4.2.3 bisection (`RAW_READINGS_INCONSISTENT`,
`N_REPEATS_MISMATCH` as errors; missing readings, unparseable readings and fewer than
three re-settings as warnings).

**How systematic bias is prevented from cancelling:** P1's two members are a *photometric
algorithmic* realisation and a *visual human* realisation of the same physical ink edge.
Their mean absolute difference therefore bounds how much the ink-boundary definition
itself moves between realisations. If both sides shared the estimator, that difference
would collapse toward the scanner's own repeatability and P1 would report agreement it
had not tested — R2 exists precisely to make that configuration impossible.

---

## 6. Ground-truth record schema

One append-only `reference_table.csv`. Rows are never edited; a correction is a **new
row** and the latest `measured_at` for a (glyph, method) pair is current. Superseded rows
are retained and reported.

| Field | Required | Meaning / constraint |
|---|---|---|
| `glyph_id` | yes | canonical `panel_id:glyph_shape:nominal_h_mm(2dp):glyph_index`, e.g. `P01:BAR_I:3.00:1`; validated against the component fields |
| `panel_id` | yes | printed coupon id, links to the run manifest |
| `glyph_shape` | yes | `BAR_I` / `H` / `T` / `RING_O` |
| `nominal_h_mm` | yes | print instruction only — **never** a reference value |
| `glyph_index` | yes | disambiguates repeated shapes at one height on one panel |
| `method` | yes | `SCANNER_2400DPI` \| `MICROSCOPE` |
| `measurement_procedure` | yes | `PIPELINE_ESTIMATOR_ON_SCAN` \| `MANUAL_VISUAL_CROSSHAIR` \| `UNRESOLVED` — the field the independence rule acts on |
| `reference_h_mm` | yes | the measured ink extent, positive |
| `unit` | yes | must be `mm`; no implicit conversion is performed |
| `reference_u_mm` | yes (may be empty → WARN) | stated uncertainty; the protocol's target is ≤ 0.01 mm |
| `instrument_id` | yes | which physical instrument |
| `instrument_cal_ref` | yes (may be empty → WARN) | calibration certificate reference; without it the value is not traceable |
| `operator` | yes | who measured — supports the §8 blinding rule |
| `measured_at` | yes | UTC timestamp; drives supersession |
| `n_repeats` | yes | how many readings the value aggregates. For `MICROSCOPE` rows M1 sets a floor of 3 independent re-settings (§4.2.4); below that is a `WARN` |
| `raw_readings` | yes (may be empty) | the individual readings, so the aggregate is auditable. For `MICROSCOPE` rows the frozen M1 form is `Obot/Ibot/Itop/Otop` per re-setting, repeats separated by `;`; the validator re-derives the height from it and **errors** if it does not reproduce `reference_h_mm` |
| `cross_check_status` | yes | `PENDING` \| `AGREED` \| `DISAGREED` \| `UNUSABLE` (§9) |
| `notes` | yes | free text; **mandatory** when status is `DISAGREED` or `UNUSABLE` |

This supersedes the shorter column list in `P0_EXECUTION_PLAN.md` §2.4. The five added
fields exist for stated requirements, not decoration: `glyph_id` (traceability, §10),
`unit` (unit consistency), `measurement_procedure` (independence enforcement, §5),
`instrument_cal_ref` (traceability of the instrument), `cross_check_status`
(disagreement handling, §9).

The analyser's own minimum requirement is deliberately left unchanged so P1 behaviour is
unchanged; the validator enforces the full schema and **must pass before** any camera run
is analysed.

---

## 7. Agreement check, computed before any phone result exists

P1 depends only on the reference table, so it can and must be settled first:

```bash
python3 tools/validate_reference_table.py \
    --table reference/reference_table.csv \
    --manifest manifests/pilot.json --agreement
```

* Pairing: group rows by `glyph_id`; take the current row per method (latest
  `measured_at`); a glyph contributes only if **both** methods are present.
* Statistic: mean absolute difference over contributing glyphs, plus median and max.
* Bands: read from `docs/P0_CRITERIA.md` at run time. The validator delegates to
  `analyse_physical.compute_p1`, so threshold **and** arithmetic keep one source of truth.
* If fewer than the criterion's minimum (15) glyphs are paired, P1 is `UNCOMPUTABLE` —
  never a pass.

**Anti-bias:** no phone data is read, so no phone result can influence the subset, the
pairing or the statistic. The reference table is committed before capture
(`P0_EXECUTION_PLAN.md` §6.3, §8).

---

## 8. Reference subset selection

* **Minimum, documented:** `>= 15` glyphs with both methods (P1 criterion text).
* **Spread, documented:** spanning heights, shapes and fonts.
* **Independence, documented:** selection is pre-registered and may never be decided
  after seeing camera data (`P0_PROTOCOL.md` §3, `P0_EXECUTION_PLAN.md` §6.3).

**UNRESOLVED — which specific glyphs.** The repository does not list them, and the choice
is entangled with the panel→measured-glyph assignment that is still open as **B5**
(`P0_EXECUTION_PLAN.md` §1.6). Two further sub-decisions are also unstated and are **not**
made here:

1. whether the cross-check subset must *include* the 20 camera-measured glyphs — which is
   what would let P1 bound the reference actually used by P2/P3/P4;
2. how the subset is distributed across the 4 fonts, 4 shapes and 5 heights.

Choosing any of this now would be a post-hoc selection dressed as a plan.

---

## 9. Handling disagreement

The documents specify only the **aggregate** rule: if the mean absolute
scanner-vs-microscope difference exceeds 0.06 mm, stop — there is no usable ground truth
and no accuracy claim may be made (`P0_PROTOCOL.md` §3, P1 No-go band).

**No per-glyph accept/reject threshold is documented, and none is invented here.** What is
frozen is the *recording* mechanism, so nothing can be discarded silently:

| Situation | `cross_check_status` | Effect |
|---|---|---|
| Cross-check not yet done | `PENDING` | glyph does not contribute to P1 |
| Both methods recorded and accepted | `AGREED` | contributes to P1 |
| Both methods recorded, judged to disagree | `DISAGREED` | **still contributes to P1** — the difference is the evidence; `notes` mandatory |
| Row cannot serve as a reference (damaged glyph, bad scan, aborted reading) | `UNUSABLE` | excluded, with a mandatory `notes` reason; the row is retained |

Rules: a disagreement is **never** resolved by deleting a row — a re-measurement is a new
row and the earlier one is retained as superseded history. `DISAGREED` and `UNUSABLE`
without a note are validation **errors**.

**UNRESOLVED (D1):** the per-glyph threshold at which a pair is called `DISAGREED`, and
whether a `DISAGREED` glyph is re-measured, escalated to a third reading, or simply
reported. Only the aggregate 0.06 mm rule exists today.

---

## 10. Physical traceability

```
panel_id ──► glyph_id = panel:shape:nominal(2dp):index
                 │
                 ├── reference_table.csv rows: SCANNER_2400DPI + MICROSCOPE
                 │        (each with instrument, operator, timestamp, procedure)
                 │
                 └── manifests/pilot.json run entry
                          panel_id + glyph_label + nominal_h_mm  →  run_id
                                   │
                                   └── out/pilot/runs/<run_id>/result.json
                                            reference_h_mm carried into results.csv
                                            as true_h_mm, consumed by P2/P3/P4/P7
```

The validator checks this linkage when given a manifest: every nominal run's
`(panel_id, glyph_label, nominal_h_mm)` must have a reference row
(`NO_REFERENCE_FOR_RUN`), stress runs are exempt, and reference rows for panels the
manifest never uses are flagged (`REFERENCE_PANEL_NOT_IN_MANIFEST`). Every P1 pair is
therefore auditable back to two instruments, two operators and two timestamps.

---

## 11. B2 blockers

| Blocker | Why it matters | Current status | Required decision / action |
|---|---|---|---|
| **B2-1 Scanner reference values cannot be produced** | The scanner is the primary reference for every camera-measured glyph, so P2/P3/P4 have no `reference_h_mm` without it. `P0_PROTOCOL.md` §3 step 3 requires *the same estimator* on the scan; no tool measures a scan (S1) and the ROI is undefined (S2) | **OPEN, but narrowed (STEP 4B).** **S3 is decided (NO, §3.2)**, so the route is fixed: dpi-derived pure-scale homography, verified exact, no measurement-code change. Still unimplemented, with no scanner or scan to validate against, and **S4 is now the load-bearing scale term** because scale comes from the platen | Write the scan-measurement path against S3 = NO; decide S4, S5, S6. Measurement code must not change |
| **B2-2 Microscope edge criterion undefined** | P1 is the *only* check on the ink-boundary definition. Without a stated visual criterion two operators measure different quantities and P1 becomes uninterpretable | **CLOSED for the criterion (STEP 4B).** **M1 is frozen** (§4.2.3, symmetric transition-band bisection), **M3 and M4 resolved** (§4.2.4), and M1 compliance is machine-audited. Residual: **M2** (magnification / reading resolution) and **M5** (operator training), both instrument-dependent | Choose M2 once an instrument is identified; run M5 training against the now-written M1 |
| **B2-3 Instrument availability unverified** | P1 cannot be computed at all without a measuring microscope; the scanner path additionally needs a certified scale/graticule | **OPEN, and tightened by S3 = NO** — the certified length standard is now unconditionally required, so there is no equipment-free fallback for scanner scale. Overlaps B6 but gates P1 specifically. `P0_EXECUTION_PLAN.md` §13 records that a missing microscope means P1 is uncomputable and therefore *no accuracy claim may be made* | Complete the §13 inventory with real answers; agree substitutes or accept the stated consequence |

**Not a B2 blocker (resolved by this document):** whether the reference may reuse the
pipeline estimator (§2, R1-R6); the microscope edge criterion, baseline realisation,
repeats and aggregation (**M1/M3/M4**, §4.2); the fiducial-frame-in-scan strategy
(**S3 = NO**, §3.2); the record schema and its validation (§6, implemented); how agreement
is computed before phone data exists (§7, implemented); disagreement recording (§9);
traceability (§10).

**Dependency, not owned by B2:** the concrete cross-check subset (§8) needs the B5
panel→glyph assignment.

**Pre-capture gate (STEP 4C):** `B2_SETUP_VERIFICATION.md` turns B2-1/B2-2/B2-3 into a
lab-visit checklist and a machine-checkable gate,
`python3 tools/verify_b2_setup.py --evidence reference/b2_setup.json` →
`B2_SETUP_VERIFIED = YES | NO`. A blank or placeholder answer, a missing calibration
record, or an unresolved decision all produce `NO`. It verifies *setup*, not measurements,
and it does not close any blocker by itself.

---

## 12. What was implemented

| Item | Status |
|---|---|
| `tools/validate_reference_table.py` | schema, unit, enumeration, provenance, duplicate/supersession, independence and linkage validation; **M1 auditability** (`parse_m1_readings` re-derives the height from the recorded crosshair positions) and **R6** operator reporting; reports P1 agreement by delegating to `analyse_physical.compute_p1` |
| `tests/test_reference_table.py` | **47 tests** covering schema, units, required fields, duplicates, supersession, independence, disagreement recording, traceability linkage, determinism, and (STEP 4B) the M1 bisection rule, its band-width invariance, raw-reading consistency and R6 |
| Manual data-entry path | the schema in §6 is fillable by hand today; the validator gates it, and for microscope rows it now checks that the written value follows from the written readings |
| M1 operator checklist | §4.2.6 |
| Scanner image processing | **deliberately not implemented** — see B2-1 |

No measurement code, no `config/`, no P1-P7 threshold and no synthetic artefact was
changed.
