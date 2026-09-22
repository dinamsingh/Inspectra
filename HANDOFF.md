# NiyamDrishti — full project handoff / context transfer

**Purpose of this file.** Give any AI assistant or new engineer the complete state of this
project in one read, so work can continue without re-deriving anything. Everything below
was verified against the repository, not recalled.

**Last verified:** branch `niyamdrishti-phase0`, HEAD `f88f2d2`, working tree clean,
352 tests passing.

---

## 0. TL;DR — read this first

- **Project:** NiyamDrishti — an offline-first Legal Metrology field-inspection assistant
  for packaged commodities, for **Smart India Hackathon 2026, problem statement SIH26034**
  (Ministry of Consumer Affairs, Food & Public Distribution / Department of Consumer
  Affairs). **§2 states the problem statement, why it is hard, and the
  requirement-by-requirement mapping to our approach — read it before §3 onward.**
- **The one insight the project rests on:** a declaration can be read perfectly by OCR and
  still be non-compliant because it is **printed too small**. Size is a *physical* question,
  not a textual one — so the hard part of this PS is calibrated measurement plus the honesty
  to refuse when the evidence cannot support it.
- **What exists today:** a complete, reproducible, dependency-free **measurement engine**
  (Phase 0 proof of concept) + a 76-run synthetic benchmark + 352 automated tests + a fully
  pre-registered physical-experiment design + 6 readiness audits + a screening-ready
  SIH deck.
- **What does not exist:** the Android app, and **any physical measurement whatsoever**.
  No lab work has been done. No coupon has been printed. No instrument is owned.
- **Blocker state:** B1 ✅ CLOSED · B2 ❌ OPEN · B3 ✅ CLOSED · B4 ❌ OPEN (spec resolved)
  · B5 ✅ CLOSED · B6 ❌ OPEN (spec resolved). `PHYSICAL_EXPERIMENT_READY = NO`.
- **The three remaining blockers are 100 % physical.** Every specification is written and
  machine-checked. B2/B4/B6 close only with lab access, not with code.
- **Working philosophy that must not be broken:** *Don't guess.* Never fabricate a result,
  never present a target as an achievement, never let synthetic data look physical, never
  weaken a threshold to make something pass.

---

## 1. Repository

```
https://github.com/dinamsingh/Setu        (private)
branch: niyamdrishti-phase0
```

Sandbox working clone during the session: `/projects/sandbox/b2`.
**Note:** `/tmp` is ephemeral between tool calls in that sandbox — work under
`/projects/sandbox/`.

Git identity used for commits:
`git -c user.name="Kiro" -c user.email="kiro@users.noreply.github.com" commit`.
Repo creation via `gh api user/repos` returns **HTTP 403** in that environment; pushing to
the existing repo works. Use `gh api repos/{owner}/{repo}/pulls` for PRs — `gh pr create`
fails there.

### Tree

```
/
├── SOLUTION_LOCK_V2.md          strategy freeze, 27 numbered decisions, scope + gates G0–G14
├── PHASE0_REVIEW.md             adversarial optics/error-budget review of Phase 0
├── PHASE0_VERDICTS.md           59 decisions graded A/B/C/D
├── PHASE0_SPEC.md               the Phase-0 spec that came out of the review
├── README.md
├── HANDOFF.md                   ← this file
├── sih2026/                     SIH deck + claims ledger + generators
└── phase0/
    ├── p0/          13 modules — the measurement engine (pure stdlib)
    ├── tools/       19 CLI tools — runners, analysers, validators, generators
    ├── tests/       8 test files — 352 tests
    ├── docs/        13 frozen documents — protocol, criteria, audits
    ├── config/      measurand / gate / uncertainty policies, camera + frame certs
    ├── fixtures/    printable coupons + the pre-registered map/selection + a stand-in
    └── out/         synthetic/ — 76 runs + analysis output (committed evidence)
```

---

## 2. The problem statement — and how NiyamDrishti answers it

### 2.1 The official PS, verbatim

> **SIH26034** — *Software System to check compliance of Packaged Commodities under Legal
> Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.*
>
> Organisation: **Ministry of Consumer Affairs, Food & Public Distribution — Department of
> Consumer Affairs.** Category: Software.

### 2.2 What the PS is actually asking for

Six asks, separated because they have very different difficulty:

1. **Model the Rules** — LMPC 2011 governs mandatory declarations on a pre-packaged
   commodity: name and address of the packer, net quantity, retail sale price (MRP),
   month/year of manufacture or packing, consumer-care contact, country of origin where
   applicable — and, importantly, **requirements on how those declarations are printed**
   (size and legibility), not merely that they exist.
2. **Check compliance** — decide whether a given package satisfies those requirements.
3. **By scanning products** — a physical package in the field, not a PDF artwork file.
4. **Images** — the evidence is camera imagery, with all its glare, blur and perspective.
5. **Labels** — text has to be located, read and parsed into typed values.
6. **Implicit, and the hard part:** a declaration can be *present and readable by OCR* and
   still be **non-compliant because it is printed too small**. That question is **physical**,
   not textual.

### 2.3 Why this is hard — the field problem

Every difficulty below is taken from the project's own frozen analysis
(`SOLUTION_LOCK_V2.md`, `PHASE0_REVIEW.md`), not from invented field statistics:

| The trap | Why a naive build falls into it |
|---|---|
| **Letter size is not an OCR question** | Pixel OCR reads "500 g" perfectly whether it is printed 6 mm tall or 1 mm tall. A text-only system therefore *cannot see* the most common size violation, and will report the package as fine. Physical size is unsolved by OCR — this is the single insight the whole project is built on |
| **"OCR found nothing" ≠ "the declaration is absent"** | The face may never have been captured, or captured unreadably. Turning silence into an absence finding manufactures a violation. So **capture completeness is kept a separate fact from declaration completeness** |
| **The same field appears on more than one surface** | A carton face and a stuck-on label can carry different MRPs. Silently taking the higher-confidence or the latest value invents a fact; both must be preserved as a contradiction |
| **The Rules change** | An inspection dated last year must be evaluable under the rule text in force *then*, not under today's text |
| **Field reality** | No connectivity in shops and godowns; glare on glossy stock; and most real packaging is curved or flexible, where a single-view physical measurement is provably unreliable (A-06) |
| **A wrong accusation has a cost** | A confident false finding against a compliant packer is a worse failure than declining to decide. This is why abstention is a designed output, not an error path |

### 2.4 Requirement → approach → status

| PS ask | How NiyamDrishti answers it | Status today |
|---|---|---|
| Model the Rules | A **signed, versioned rule pack selected by inspection date**, evaluated deterministically with three/four-valued logic (`TRUE / FALSE / UNKNOWN / NOT_APPLICABLE`) — never a default assumption when a fact is unknown | **DESIGNED** |
| Check compliance | Emits a **screening state and candidate findings**, each with its evidence; the **officer** records the legal determination. Applicability pre-check raises `REQUIRES_OFFICER_REVIEW` rather than guessing | **DESIGNED** |
| Scan products | **Guided six-face capture** with per-surface coverage states: `CAPTURED_READABLE` / `CAPTURED_UNREADABLE` / `NOT_ACCESSIBLE` / `NOT_APPLICABLE`, each with a reason | **DESIGNED** |
| Images | Every image gets a quality result, a hash and metadata; crops are retained as evidence. Image-quality, geometry and segmentation **gates already exist and are tested** in the engine | **PARTLY BUILT** (gates built and benchmarked; capture UI designed) |
| Labels | Offline OCR produces raw spans, alternatives and confidences; a **deterministic typed grammar** parses MRP, net quantity, dates and responsible entity. *OCR output is an observation, never a fact*; low confidence on a critical field yields `UNKNOWN_OCR` or review, **not absence** | **DESIGNED** |
| **Printed size compliance** | The **calibrated measurement path**: a printed co-planar four-marker fiducial frame, homography rectification, a sub-pixel 50 % linearised-luminance ink boundary, an uncertainty interval, a guard-band decision — **or an explicit abstention** | **ENGINE BUILT + synthetically validated; physical validation pending** |
| Cross-surface conflicts | Contradiction graph: conflicting values are both kept and surfaced | **DESIGNED** |
| Evidence and audit | Finding → source crop → raw + normalised observation → rule version → engine version, hash-linked; immutable report versions | **DESIGNED** |
| Field operation | Capture-to-draft-report **fully offline**; sync optional and idempotent | **DESIGNED** |

**Read the status column carefully.** The part that is *built and measured* is the hardest
and most differentiating part — the physical measurement engine. The surrounding app
(capture UI, OCR, rule pack, report) is specified but not implemented. Nothing in the deck
or in any communication may imply otherwise.

### 2.5 What is deliberately NOT solved

From the frozen hard exclusions:

- **Actual net quantity** — we screen the *declared* value on the label; verifying the true
  contents needs a weighing instrument and a sampling workflow. Out of scope.
- **Curved, moulded, flexible, embossed or creased surfaces** — physical measurement is
  blocked and abstains; OCR may still run.
- **Whole-package "declaration absent" conclusions** when required faces are incomplete or
  unreadable.
- **Automated penalty or adjudication**, marketplace crawling, medical-device rule
  adjudication.
- **Font point size, nominal design size, OCR-box height** — the system reports *visible
  printed-ink extent perpendicular to the fitted baseline*, and only for explicitly selected
  eligible glyphs. Whether that is the correct reading of the statutory "character height"
  is **open question G0**, to be confirmed with the administering authority.

### 2.6 The product, concretely

An Android assistant for a Legal Metrology inspection of a packaged commodity. The officer
works through:

```
CAPTURE → IDENTIFY → EXTRACT → CHECK → MEASURE → EVIDENCE → REVIEW → REPORT
```

- capture the package faces; OCR extracts the declarations;
- a **signed, versioned rule pack selected by inspection date** is evaluated
  deterministically (three/four-valued logic);
- for **character-height** declarations there is a calibrated measurement path: a printed
  **co-planar four-marker fiducial frame** turns a phone photo into a millimetre estimate
  with an uncertainty interval;
- every candidate finding links to its **source crop → raw + normalised observation → rule
  version → engine version**;
- everything is **offline-first**; sync is optional and idempotent.

### The non-negotiable positioning

| Say this | Never say this |
|---|---|
| screening assistance | automated legal verdict |
| candidate finding | automatic violation determination |
| evidence-linked | court-admissible / legally defensible |
| rule-version aware | automatically updated law |
| physical size screening under controlled conditions | works for every package |

**AI/CV assists observation and extraction. The officer makes the legal determination.**
Out of scope, explicitly: curved, flexible, embossed, moulded, creased or unknown
non-planar surfaces.

### The differentiator (phrase as documented design, never as "no one else has this")

1. Evidence-bounded physical character-height screening
2. Measurement only when conditions support it
3. Uncertainty reporting
4. Explicit abstention when measurement is not trustworthy
5. Pre-registered face/glyph coverage
6. Cross-face contradiction preservation
7. Evidence-linked findings
8. Offline-first field workflow
9. Versioned, reproducible rule and evidence lineage

---

## 3. The measurement engine (what actually works today)

Pure Python, **no third-party numerical stack** (no numpy, no OpenCV) — because the sandbox
had no network, which turned out to be an asset: the same arithmetic ports to a device.

Pipeline per frame (`p0/pipeline.py: process_frame`):

```
detect 4-marker fiducial  →  fit homography  →  rectify
  →  estimate baseline direction
  →  sample scanlines, find sub-pixel 50 % linearised-luminance crossings
  →  fit a model to top and bottom edge clusters, take fitted extremes
  →  frame-thickness correction (1 + d/Z)
  →  uncertainty budget  →  guard-band decision  OR  abstain
```

Key config (`phase0/config/`, **frozen — do not edit**):

| File | Contents that matter |
|---|---|
| `measurand_policy_v1.json` | `measurand: VISIBLE_PRINTED_INK_EXTENT_PERPENDICULAR_TO_BASELINE`, `boundary_fraction 0.50`, `linearization SRGB_EOTF`, `estimator FITTED_EXTREME_MODEL`, `apex_fit_window_frac 0.35`, `scanlines 24`, `sensitivity_fractions [0.4, 0.6]`, `shape_classes {FLAT_TOP: BAR_I,H,T…; ROUND: RING_O,O,0…}` |
| `gate_policy_v1.json` (`policy_id GP-v2`) | `min_rho_px_per_mm 10.0`, `max_view_tilt_deg 30.0`, `max_reproj_rms_px 0.25`, `max_reproj_max_px 0.60`, `max_lomo_rel_spread 0.005`, `max_thickness_over_z 0.01`, `min_hull_margin_mm 8.0`, `min_scanline_fraction 0.5`, `max_sensitivity_dev_frac 0.05`, `min_control_points 12`, `max_jacobian_ratio 3.0`, `min_snr 20.0`, `min_michelson_contrast 0.3` |
| `uncertainty_model_v1.json` | `UM-v1-uncalibrated`, `k_lower = k_upper = 1.645`, `calibrated: false`, `residual_tilt_bound_deg 3.0` |

Abstention prefix: `PHYSICAL_SIZE_NOT_ESTABLISHED_` + stage
(`p0/gates.py: STAGES = PROFILE, FIDUCIAL, IMAGE_QUALITY, GEOMETRY, PLANARITY,
SEGMENTATION, BURST, UNCERTAINTY`).

Fiducial scheme is custom (`NDFID-1`) rather than ArUco/ChArUco, because cv2.aruco was
unavailable — see assumption A-03.

---

## 4. Verified numbers — the ONLY figures that may be quoted

### Synthetic benchmark (`phase0/out/synthetic/analysis/analysis.json`)

`n_rows: 76`, `overall: PASS`, 10 of 10 criteria pass.

| Criterion | Result |
|---|---|
| C1 arithmetic | `max|err| = 0.00797 mm ≤ 0.010` |
| C2 accuracy | `bias +0.0005 (≤0.030)`, `p95|err| 0.0054 (≤0.060)` |
| C3 repeatability | `median burst SD 0.0025 mm (≤0.030)` |
| C4 coverage | `1.000 on n=17 (≥0.90)` — "k is NOMINAL, not validated" |
| C5 estimator | `model-fit MAE 0.0018 vs max-minus-min 0.0027` |
| C6 linearisation | `linear err 0.0004 vs gamma-glyph −0.0441` |
| C7 unsafe detection | `abstained 11/11` |
| C8 decision safety | `false-clear 0 of 4 undersize; false-accuse 0 of 4 compliant` |
| C9 undetectable | `|err| up to 0.1847 mm — needs fixture control, not gates` |
| C11 measure rate | `1.00 on SAFE (≥0.80)` |

**Every one of these is SYNTHETIC-ONLY and must be labelled as such.**

### Out-of-plane evidence (assumption A-06, measured — the most important finding)

Read directly from `out/synthetic/runs/*/result.json`:

| run | local print tilt | undeclared offset | error | reproj RMS | LOMO | view tilt | status |
|---|---|---|---|---|---|---|---|
| `E_THICKNESS-declared` | 0° | −0.45 declared | **+0.0007** | 0.057 | 0.00008 | 0.228° | MEASURED |
| `N_NONPLANAR_TILT-10` | 10° | 0 | **−0.0456** | 0.060 | 0.00008 | 0.294° | MEASURED |
| `N_NONPLANAR_TILT-20` | 20° | 0 | **−0.1847** | 0.087 | 0.00008 | 0.090° | MEASURED |
| `N_PLANE_OFFSET_UNDECLARED-1.5` | 0° | 1.50 mm | **+0.0224** | 0.084 | 0.00023 | 0.324° | MEASURED |
| `N_PLANE_OFFSET_UNDECLARED-5.0` | 0° | 5.00 mm | **+0.0802** | 0.074 | 0.00018 | 0.447° | MEASURED |

**Interpretation, and it is load-bearing for the whole project:** a single view can look
geometrically impeccable — every gate green with room to spare — while the print sits out of
plane and the height is wrong by up to 0.18 mm. Closed form: `err = −h(1 − cos α)`, which
reproduces the measurements to 9×10⁻⁴. Therefore **flatness is a mechanical acceptance, not
a software gate**. Note also row 1: a *declared* offset corrects to +0.0007 mm — the problem
is never the offset, it is the offset nobody recorded.

### Other verified facts

- **352 automated tests** pass: `test_p0` 39 · `test_physical_analyzer` 29 ·
  `test_reference_table` 47 · `test_b2_setup_gate` 47 · `test_glyph_roi_map` 60 ·
  `test_flatness_b4` 39 · `test_glyph_selection` 49 · `test_inventory_b6` 42.
- Re-runs are **bit-identical** (`analysis.json` re-derives identically).
- Runtime ≈ **1.3 s per frame at 12 MP**, single-threaded; PNG read 1.3–2.1 s.
- `glyph_map.json`: **400** glyph instances, hash `db548c1f1c94…`
- `glyph_selection.json`: **20** panels, hash `1a1b1dabea14…`, P1 subset n = 20
- Frame geometry: outer 100×60 mm, markers 10 mm at (±40, ±22), window **50×20 mm**
- Coupon: **95×55 mm**, heights 1.2/2.0/3.0/4.0/6.0 mm, shapes BAR_I/H/T/RING_O,
  4 fonts, 20 panels → **400 glyph instances**
- `RING_O` apex-fit bias on ideal renders: **0.0054 mm**

---

## 5. Physical acceptance criteria (frozen, pre-registered, NOT yet met)

`phase0/docs/P0_CRITERIA.md` — thresholds are **constants**; if one fails, the response is
to narrow the claim or fix the engineering, **never** to move the threshold.

| ID | Criterion | Go | Conditional | No-go |
|---|---|---|---|---|
| P1 | reference cross-method agreement (scanner vs microscope, ≥15 glyphs) | ≤0.03 mm | 0.03–0.06 | >0.06 → **no accuracy claim is possible** |
| P2 | residual SD after one global bias correction (3 mm class) | ≤0.08 mm | 0.08–0.15 | >0.15 |
| P3 | repeatability SD (same panel/device/operator) | ≤0.05 mm | 0.05–0.10 | >0.10 |
| P4 | inter-device bias after global correction | ≤0.05 mm | 0.05–0.12 | >0.12 → per-device claim only |
| P5 | gate acceptance in nominal conditions | ≥0.70 | 0.50–0.70 | <0.50 → redesign fixture/protocol |
| P6 | unsafe-condition acceptance (stress block) | ≤0.02 | 0.02–0.05 | >0.05 → abstention unsafe |
| P7 | empirical interval coverage | **REPORT_ONLY** — never pass/fail | — | no No-go |

**Hard stops:** C1 fails → maths is wrong, fix before physical work. P1 fails → no accuracy
claim at all. P2 or P6 fails → downgrade the claim. P5 fails → change the protocol.

**Prohibited responses:** loosening a gate so more runs pass · relabelling an
`UNSAFE_DETECTABLE` fixture as diagnostic without evidence · dropping abstained runs from a
denominator without reporting the abstention rate · **reporting a target as an achieved
result.**

### Values that look like criteria but are not

- `min_rho_px_per_mm 10.0` is a gate **floor**; the capture target is ≥16 px/mm (A-17).
- `max_view_tilt_deg 30.0` gates **view obliqueness** — a *different quantity* from local
  print-plane tilt, which is not observable from one view (A-06).
- The interval-width gate is **disabled** (`max_interval_width_mm: null`) until the
  uncertainty model is calibrated.

---

## 6. Experiment design (frozen)

- **Nominal matrix:** 20 panels × 2 devices × 2 operators × 3 repeats = **240 runs**,
  × 7 frames = 1 680 frames.
- **Repeats are the angle block**, not replicates: R1 = 0°, R2 = 12°, R3 = 25°. Anything
  treating R1–R3 as pure replicates is wrong.
- **Stress block:** 8 classes × 8 = **64 runs**, feeding P6 only, no accuracy expectation:
  defocus, motion blur, glare, occluded marker, wrong frame serial, low contrast, bowed
  panel, frame not flush.
- **Calibration captures:** ≥12 frame views per device, excluded from accuracy statistics.
- **One glyph per run** (A-14) → only **20 of 400** instances are camera-measured.
- Blinding: the capturing operator must not know `reference_h_mm`; the microscope operator
  must not have produced or seen the scanner values (rule R6).

---

## 7. Assumptions register (`phase0/docs/P0_ASSUMPTIONS.md`)

The ones that come up constantly:

| ID | Assumption | Why it matters |
|---|---|---|
| A-01 | pure-stdlib implementation | no numpy/OpenCV anywhere |
| A-02 | input is 8-bit greyscale PNG | real captures must be converted **without sharpening or tone mapping** |
| A-03 | custom NDFID-1 fiducial, not ArUco | cv2.aruco unavailable |
| A-05 | non-planarity modelled as a tilted/offset plane | true curvature, creases and dents untested |
| **A-06** | **out-of-plane print is NOT detectable from a single view — measured** | the reason flatness is mechanical |
| A-07 | `k = 1.645` is **nominal**, model ships uncalibrated | no "validated interval" claim is permitted |
| A-09 | the measurand is **not** the legal measurand | every output is an ink-extent estimate against a *configured engineering threshold*, never statutory compliance. Solution Lock gate **G0** is unverified |
| A-13 | operator and device variability untested | covered by the matrix, not yet run |
| A-14 | one glyph per run | the reason only 20 of 400 are measured |
| A-17 | the ρ gate floor is not the capture target | 10 px/mm floor vs ≥16 px/mm target |

---

## 8. Blocker board — the heart of the project

| Blocker | Specification | Physical | One-line state |
|---|---|---|---|
| **B1** analyser for P1–P7 | ✅ | — | **CLOSED** (STEP 3/3C) |
| **B2** independent reference measurement | ✅ RESOLVED | ❌ | **OPEN** — no reference value can be produced |
| **B3** glyph/ROI location | ✅ | ✅ | **CLOSED** (STEP 5) |
| **B4** fixture flatness | ✅ RESOLVED | ❌ | **OPEN** — nothing measured |
| **B5** panel→glyph assignment | ✅ | ✅ | **CLOSED** (STEP 7) |
| **B6** equipment inventory | ✅ RESOLVED | ❌ | **OPEN** — not one item confirmed |

### B1 — CLOSED

`tools/analyse_physical.py` computes P1–P6 from the frozen bands **parsed out of
`P0_CRITERIA.md` at run time** (single source of truth), and `analyse_results.py` routes
physical datasets to it. Before this, running the analyser on a physical dataset produced
all-`nan` plus a misleading `OVERALL: FAIL`.

**P7 was frozen as REPORT_ONLY (Option C).** Why: the original wording — "CI includes
nominal and lower bound ≥0.90" — named no numeric nominal (0.90 two-sided and 0.95
one-sided are both defensible readings of `k = 1.645`) and under the 0.90 reading the two
clauses were **mutually exclusive: 0 solutions across 125 249 (k, n) combinations**. See
`P7_DECISION_MEMO.md`. P7 now reports observed coverage k/n, a Wilson 95 % CI, n and
interval width, with status `REPORT_ONLY`, and can never emit a pass/fail.

### B2 — OPEN (this is the critical-path blocker)

Resolved by specification:
- **Estimator independence decided.** The `SCANNER_2400DPI` tier **may** reuse the pipeline
  estimator (rule R1 — at 94.5 px/mm it is a different *sampling regime*, not a different
  measurand definition). The `MICROSCOPE` tier **may not** (R2). Enforced as errors.
- **Consequence disclosed, not hidden:** because the scanner tier shares the estimator,
  **P2/P3/P4 are blind to estimator-definitional bias** (0.0054 mm on `RING_O`). **Only P1**
  tests the ink-boundary definition — and even then it bounds *realisation disagreement*,
  not correctness.
- **M1 frozen (STEP 4B) — the microscope edge criterion.** Stated plainly: a human at an
  eyepiece **cannot** reproduce the 50 % linearised-luminance boundary. M1 is therefore
  **symmetric transition-band bisection**: at each edge the operator sets two crosshairs —
  **O** (outermost position with no ink tone) and **I** (innermost position where tone stops
  deepening) — and the boundary is **(O+I)/2**. Justified by **A-11**: under a symmetric
  transition the geometric midpoint *is* the 50 % crossing, so the rule targets Δf = 0 using
  a judgement a human can actually make.
  - A *perceived-darkness* rule was **rejected on repo evidence**: `h_sensitivity_dev_mm`
    over 497 frames has median **0.02714 mm** for a ±0.10 boundary-fraction shift (slope
    ≈0.27 mm per unit fraction), so a perceptual midpoint (Δf ≈ 0.18) would contribute
    **0.049 mm** and land P1 in its Conditional band by construction.
  - Also frozen: reflected/episcopic illumination; **M3** baseline by stage rotation
    verified at two separated points; **M4** ≥3 independent re-settings with `u = s/√n`.
  - Still open: **M2** (magnification / reading resolution) and **M5** (operator training).
- **S3 decided (STEP 4B): NO** — the fiducial frame is **not** scanned with the coupon.
  This **reversed** the earlier STEP 4A recommendation, on evidence: a frame laid on the
  print sits one thickness above it, and `thickness_correction` applies `1 + d/Z` while the
  `PLANARITY` gate limits `thickness_over_z` to 0.01 — **both need Z, and for a scan Z is
  not measurable** (`z_estimate_mm` is just `f_px/rho`, so asserting a focal length asserts
  Z). With the repo's own `FRAME-SYN-0002-THICK` (0.45 mm): at an asserted Z = 50 mm the
  gate **passes** while the reference carries **0.0270 mm** of scale bias — 90 % of P1's Go
  band, undetected. Coplanar escapes fail on the frozen geometry (95×55 coupon cannot sit
  inside a 50×20 window).
  - Consequences: the **certified length standard is now unconditional**; **S4** (platen
    non-uniformity) is *promoted* to the load-bearing scale term; `P0_PROTOCOL.md` §3 step 1
    stands unchanged.
- **Enforcement built:** `tools/validate_reference_table.py` (18-field append-only schema,
  independence rules, M1 auditability — it re-derives the height from the recorded
  `Obot/Ibot/Itop/Otop` readings and errors if it does not match) and
  `tools/verify_b2_setup.py` (**63 checks, 58 mandatory**; blank / `TBD` / `UNSPECIFIED` /
  unresolved decision → `B2_SETUP_VERIFIED = NO`).

Residual B2 blockers: **B2-1** no scanner reference value can be produced (route specified —
dpi-derived pure-scale homography, verified exactly representable — but unwritten, and
S2/S4/S5/S6 are undecided) · **B2-2** M2 and M5 need an instrument in hand · **B2-3**
availability unverified.

### B3 — CLOSED

The audit had framed B3 as "`roi_mm` cannot be determined". Inspection showed the opposite
and worse: `run_real_batch.py --scaffold` wrote `roi_mm: [0.0, 0.0, 1.5, 3.2]` — a
**plausible box at the centre of the frame window** — plus `glyph_label: "TODO"`. Unedited
it neither crashed nor warned; it measured whatever sat there.

Now `roi_mm` is **computed, never typed**:
- `fixtures/physical/coupons/glyph_map.json` pre-registers all **400** instances in
  panel-local mm, **derived** (not authored) from `tools/make_coupons_svg.py`'s own row/
  column stepping and `p0.render.glyph_bbox_mm` — the same function the synthetic suite
  already uses to build `roi_mm`.
- Panel→fiducial transform is measured per mounting from **two** caliper readings of the
  coupon's top edge (two points, because a rotation θ displaces a glyph at lever arm r by
  r·θ and the smallest glyph's whole budget is 0.108 mm); the measured corner span
  doubles as a scale/orientation check against 95.0 mm.
- **ROI precision derived from the code:** `roi_tolerance_mm = min(0.5·w, 0.225·h)` from
  `half_t = 0.4·w`, `span_n = 0.725·h` and `min_scanline_fraction 0.5`. Worst glyph
  (`BAR_I` @1.2 mm) = **0.108 mm**.
- **Measured behaviour:** offsets inside the budget MEASURE (error ≤0.003 mm); beyond it the
  pipeline **ABSTAINS** (`scanline_fraction`, `snr`, `SEGMENTATION_INSUFFICIENT_SCANLINES`,
  `SEGMENTATION_NO_CONTRAST`). A misplaced ROI never returns a confident wrong height.
- A hand nudge is an **ERROR** (`ROI_ADJUSTED_BY_HAND`) even inside the budget.

### B4 — specification RESOLVED, blocker OPEN

The acceptance was already in the repo, unstated: `residual_tilt_bound_deg = 3.0` becomes
`u_tilt = h(1−cos 3°)/√3 = 0.0024 mm` on a 3.06 mm glyph and flows into **every interval the
pipeline has ever emitted**. Nothing verified it, and it does not degrade gracefully — the
measured 10° error is **19.2×** that `u_tilt`.

- **Rule:** local print-plane tilt ≤ **3.0°** anywhere in the measurement window.
- **Gap conversion, derived from A-05** (parabolic bow, max slope 4s/L):
  `max_gap = tan(3.0°)·L/4` → **0.655 mm over the 50 mm span**, **0.262 mm over 20 mm**
  (the short span is **binding**). Plus the A-06 frame flush rock/gap check and a verified
  backing plate. Measured **after** clamping.
- Thresholds that are **NOT** flatness limits, and must never be reused as such:
  `max_view_tilt_deg` (view obliqueness), `max_thickness_over_z` (the *declared* thickness),
  reprojection RMS (F5.3 warns against reading it as planarity), LOMO, and Solution Lock's
  superseded 0.10 mm absolute gate.
- `tools/validate_flatness.py` **derives** PASS/FAIL/UNVERIFIED from the evidence, rejects a
  self-declared pass (`STATUS_CONTRADICTS_EVIDENCE`), rejects a loosened acceptance, rejects
  an instrument too coarse to resolve its own limit, and cross-checks the manifest.
- Silent path found and closed: `run_real_batch.py` fed the `PLANARITY` gate from
  `r.get("declared_flat", True)` — **default true** — and the scaffold wrote `True` too.
  An operator who never thought about flatness got a passing planarity gate. Now `null`,
  and the runner exits unless the flag is stated.

### B5 — CLOSED

20 of 400 instances are camera-measured; the choice decides whether P2's 3 mm class has data
at all (the analyser's own `UNCOMPUTABLE` message names B5). Assignment generated by a
closed-form rule, not picked panel by panel:

```
f = (i−1) mod 4 ;  p = (i−1) div 4 ;  c = (p+f) mod 5
nominal_h = HEIGHTS[c] ;  glyph_shape = SHAPES[(f+c) mod 4]
```

Result is a **complete 5×4 factorial, one panel per cell**: 4 panels per height, 5 per
shape, 5 per font, both shape classes (FLAT_TOP 15 / ROUND 5), all 20 (height, shape) pairs
distinct, all 20 (font, height) pairs distinct, every sheet carrying 4 distinct heights.
P2's 3 mm class = **P03, P06, P09, P20** → 48 observations. Nine balance invariants are
asserted by tests, not prose.

- A weighted 8-3-3-3-3 alternative favouring P2 was **considered and rejected**: it drops
  the hardest height (1.2 mm) to 3 panels and presumes, before data exists, where the
  answer lies.
- **Stated limitation:** those 48 observations are 4 panels × 12 runs, so for the
  **between-panel** component the effective sample is **4**, not 48 (~41 % relative SE).
  Inherited from the frozen 20-panel, one-glyph design; no allocation removes it.
- **Also closes C9:** the P1 cross-check subset **is** the 20 camera-measured glyphs —
  20 ≥ 15, spanning everything — because P1 must bound the references P2/P3/P4 consume.

### B6 — specification RESOLVED, blocker OPEN

`tools/validate_inventory.py`: **20 catalogued items, 14 mandatory**, each with purpose,
blockers served, access classification and required evidence →
`B6_INVENTORY_VERIFIED = YES|NO`.

- **14 mandatory:** flatbed scanner (2400 dpi optical) · certified length standard ·
  measuring microscope · calibrated caliper · straightedge · gap gauge · rigid flat backing
  plate · fiducial frame stock · print stock · printer at true 100 % · **two** phones ·
  copy stand · diffuse lighting · image conversion tool.
- **§13's classification corrected:** the microscope is filed under PREFERRED there while
  the same table says "P1 depends on it" and the MISSING row says that without it no
  accuracy claim may be made. The stronger statement is binding → **MANDATORY**. Also, the
  straightedge and gap gauge B4 needs were **never listed** in §13.
- **Explicitly not to be bought:** CMM / optical comparator (the caliper survey already
  contributes ~0.0006 mm on a 3 mm glyph; `PHASE0_VERDICTS` #14 downgraded it), dial
  indicator, RAW-capable phone, top glass platen.
- **One phone is a FAILURE, not a silent downgrade** — with one, P4 and verdict #24 become
  uncomputable and the claim narrows to per-device, which is a design change.
- **No second source of truth:** the inventory records *existence and paperwork*;
  `verify_b2_setup.py` records reference-tier *capability*; `validate_flatness.py` records
  the B4 *measurements*. IDs are cross-checked between them.
- **Packaged products are SAMPLES, not equipment** — biscuit, room freshener, peanut butter,
  creatine have no catalogue entry and recording one is rejected. They cannot be P0
  validation data (they break the nominal matrix, the flatness requirement and B5). They
  *are* useful for Solution Lock gate **G0** and a later realism dataset.

---

## 9. Still-open decisions (free to make, need no equipment)

| ID | Decision | Notes |
|---|---|---|
| **S2** | how the glyph ROI is located in a scan | related to B3 but separate: no frame in the scan |
| **S4** | platen non-uniformity correction rule | **equipment-dependent**; since S3 = NO this is the load-bearing scale term, and the repo's only scale-consistency detector (`leave_one_group_out_scale` + `max_lomo_rel_spread`) needs markers, which the scan has none of |
| **S5** | repeat scans per panel, and what `n_repeats` aggregates | determines the stated `reference_u_mm` |
| **S6** | baseline direction on a scan | `estimate_baseline_dir` exists; needs a decision to use it |
| **M2** | microscope magnification / reading resolution | derived guide: a reading step d contributes ≈ d/4 to P1, so 0.05 mm steps eat 41.7 % of the 0.03 mm Go band |
| **M5** | operator training + inter-operator agreement | needs the instrument and a second person |
| **D1** | per-glyph `DISAGREED` threshold | only the aggregate 0.06 mm rule exists |
| **C6** | reference population: all 400 or a pre-declared reduction | must be fixed before capture |
| **G0** | what the rule actually means by character height | Solution Lock gate; the measurand is documented as a **proxy** pending confirmation with the administering authority |

---

## 10. Tool inventory — what each CLI does

| Tool | Purpose | Verdict line |
|---|---|---|
| `run_experiment.py` | render + run the synthetic suite | — |
| `run_real_batch.py` | run the pipeline over real captures from a manifest | refuses: missing/stub `roi_mm`, `TODO` glyph label, unstated `declared_flat`, missing/wrong `selection_hash`, unselected glyph |
| `analyse_results.py` | synthetic criteria C1–C11; routes physical datasets onward | `OVERALL: PASS/FAIL` |
| `analyse_physical.py` | physical P1–P6 + REPORT_ONLY P7, bands parsed from `P0_CRITERIA.md` | per-criterion status |
| `validate_reference_table.py` | 18-field ground-truth schema, independence R1–R6, M1 auditability, P1 pre-check | `VERDICT: ACCEPTED/REJECTED` |
| `verify_b2_setup.py` | B2 pre-capture equipment/software gate, 63 checks | `B2_SETUP_VERIFIED = YES/NO` |
| `make_glyph_map.py` | derive the 400-glyph map; `--check` re-derives | hash |
| `validate_roi_map.py` | compute `roi_mm` from map + registration; `--fill` | `VERDICT: ACCEPTED/REJECTED` |
| `validate_flatness.py` | B4 flatness register, derives PASS/FAIL/UNVERIFIED | `B4_FLATNESS_VERIFIED = YES/NO` |
| `make_glyph_selection.py` | derive the 20-panel selection; `--check` | hash |
| `validate_selection.py` | enforce the assignment against a manifest | `VERDICT: ACCEPTED/REJECTED` |
| `validate_inventory.py` | B6 equipment inventory gate | `B6_INVENTORY_VERIFIED = YES/NO` |
| `survey_frame.py` | caliper survey → frame certificate | — |
| `make_frame_svg.py` / `make_coupons_svg.py` / `make_configs.py` / `calibrate_camera.py` / `experiments.py` | printable fiducial frame, printable coupons, config generation, camera profile, experiment specs | — |

### Commands that should always work

```bash
cd phase0
python3 -m unittest discover -s tests                      # 352 tests, OK
python3 tools/analyse_results.py --in out/synthetic --out /tmp/a      # OVERALL: PASS
python3 tools/analyse_physical.py --in fixtures/standin_physical --out /tmp/b
python3 tools/validate_reference_table.py --table fixtures/standin_physical/reference_table.csv --agreement
python3 tools/make_glyph_map.py --check fixtures/physical/coupons/glyph_map.json
python3 tools/make_glyph_selection.py --check fixtures/physical/coupons/glyph_selection.json
python3 tools/validate_selection.py
python3 tools/verify_b2_setup.py --template /tmp/b2.json && python3 tools/verify_b2_setup.py --evidence /tmp/b2.json   # NO
python3 tools/validate_flatness.py --template /tmp/f.json && python3 tools/validate_flatness.py --register /tmp/f.json # NO
python3 tools/validate_inventory.py --template /tmp/i.json && python3 tools/validate_inventory.py --inventory /tmp/i.json # NO
```

**Regression invariants for any future change:** 352 tests pass · `out/synthetic/analysis/
analysis.json` re-derives **bit-identically** with `overall: PASS` · the stand-in P1–P7
output is unchanged · the two hashes are unchanged.

---

## 11. The SIH 2026 deck (`sih2026/`)

Built on the **official template**: exactly **6 slides** including the title, section
headings and idea pointers unchanged, points and diagrams rather than paragraphs, the
template's own "Important Instructions" slide deleted as it instructs, submit as PDF.

| File | What |
|---|---|
| `NiyamDrishti_SIH2026_Idea.pptx` | editable, 475 native shapes, 6 vector diagrams, no flattened images, 2 fonts |
| `NiyamDrishti_SIH2026_Idea.pdf` | the upload artefact |
| `preview/slide1..6.png` | rasterisations used for visual QA |
| `OUTLINE.md` · `CLAIMS_LEDGER.md` · `SOURCES.md` · `EVALUATOR_AUDIT.md` · `README.md` | outline + template audit, every claim with source and status, sources, adversarial review |
| `deck/deckkit.py` · `build_deck.py` · `preview.py` | generators |

**Why hand-rolled:** the sandbox had no `python-pptx`, no LibreOffice, no image converter
and no network. Both PPTX (raw OOXML) and PDF are emitted from **one layout model**, and
text is wrapped once with Adobe base-14 metrics with each wrapped line emitted as its own
paragraph — so PowerPoint cannot re-wrap differently from the PDF preview.
Rebuild: `python3 sih2026/deck/build_deck.py` (exits non-zero on any overflow).

**Three fields to fill before upload:** Theme, Team ID, Team Name (slide 1). The PS ID is
written `SIH26034` following the 2025 format (`SIH25108`) — confirm on the portal. The
top-right mark is a **text wordmark**; paste the official logo PNG over it if wanted.

**Slide map:** 1 TITLE PAGE (metadata + package-face diagram with MEASURED/ABSTAINED) ·
2 IDEA TITLE (proposed solution, 3 pointers + 8-step workflow + "Don't guess." + boundary) ·
3 TECHNICAL APPROACH (technologies + hero pipeline + 3-card validation status) ·
4 FEASIBILITY AND VIABILITY (feasibility + pre-committed stop conditions + 6 risks) ·
5 IMPACT AND BENEFITS (officer impact + deliberate limits + evidence chain + benefits) ·
6 RESEARCH AND REFERENCES (6 refs + the open G0 question + our evidence + repo).

---

## 12. Rules any successor must follow

### Claim policy (non-negotiable)

**Never claim:** first · only · unique · best · most advanced · 100 % accurate · zero false
positives · legally defensible · court admissible · tamper-proof · fully legally validated ·
government integrated · AI makes the final legal decision.

**Never fabricate:** physical accuracy results · scanner-vs-microscope numbers · physical
P1–P7 PASS results · laboratory validation numbers · real-world error percentages ·
calibration certificates · equipment availability · physical experiment completion. Do not
fake screenshots implying any of these.

**Always label** synthetic figures as *synthetic / controlled benchmark*. Use: "controlled
benchmark validated", "physical validation protocol pre-registered", "laboratory validation
pending", "designed for controlled physical validation". Pending status should be **precise,
not apologetic** — one card, not a theme.

### Working style the user expects

- **Hinglish** output (English technical terms, Hindi connective prose). Markdown tables,
  headings, concrete numbers.
- **Be adversarial** — against the project *and* against your own earlier recommendations.
  S3 was recommended in STEP 4A and **reversed in STEP 4B** on evidence; that reversal was
  the right move and was documented in place rather than deleted.
- **Derive, never invent.** Coordinates came from the coupon generator; tolerances from
  `measure.py` and the gate policy; the flatness acceptance from the uncertainty model.
  If the documents do not state it, mark it **UNRESOLVED** rather than choosing.
- **Prefer a machine-checked gate over a written promise.** Every audit produced a tool with
  a one-line verdict and tests, and every gate is **reachable** (a test constructs a
  hypothetical satisfied state and asserts YES) — because the P7 memo caught a criterion
  that could never be satisfied.
- **Protected paths** unless a demonstrated inconsistency forces it: `phase0/p0/`,
  `phase0/config/`, `P0_CRITERIA.md`, `SOLUTION_LOCK_V2.md`, `phase0/out/` (synthetic
  artefacts). Verify with `git diff --name-only HEAD -- <paths>` → empty.
- Each step ends with: files changed · tests · git diff summary · protected-path
  verification · an explicit verdict line.
- The user is in a browser with a read-only file explorer — **push to the branch** so they
  can download, and surface command output in chat.
- Do not create the final SIH PPT unprompted (it has now been created on request).

---

## 13. Commit history — what each step did

| Commit | Step | What |
|---|---|---|
| `3252adf` | — | P0-min proof of concept: 13 modules, 9 tools, 39 tests, 76-run suite → `OVERALL: PASS`. Found/fixed a half-pixel convention bug, a bootstrap cluster-selection bug and a shape-dependent blur proxy |
| `a61e749` | consistency audit | 14 documentation-vs-code inconsistencies patched (ρ 12 vs 10 vs 16, stale module names, 60 vs 400 glyphs, test count) |
| `ca219ee` | STEP 2 | execution-readiness audit → `PHYSICAL_EXPERIMENT_READY = NO`, blockers B1–B6 defined |
| `5c7215d` | STEP 3 | physical P1–P7 analyser; B1 not yet closed because P7 was unspecifiable |
| `aedf4be` | STEP 3B | P7 decision memo — proved the original P7 self-blocking (0 solutions in 125 249 combos) |
| `4a40c22` | STEP 3C | P7 frozen as REPORT_ONLY; **B1 CLOSED** |
| `e4dfbd1` | STEP 4 | reference procedure + 18-field enforced schema; B2 partly closed |
| `e4258fd` | STEP 4A | B2 equipment feasibility audit (docs only); found the S3 idea |
| `d143c2e` | STEP 4B | **M1 frozen**, **S3 = NO** (reversing 4A on evidence) |
| `f27d085` | STEP 4C | B2 pre-capture verification spec + setup gate |
| `c8aa98f` | STEP 5 | **B3 CLOSED** — pre-registered glyph/ROI map |
| `7c0f316` | STEP 6 | B4 specification RESOLVED; closed the default-true `declared_flat` hole |
| `1e175c3` | STEP 7 | **B5 CLOSED** — balanced 5×4 factorial; C9 closed with it |
| `9fc9d87` | STEP 8 | B6 specification RESOLVED — 14-item inventory + gate |
| `f88f2d2` | deck | SIH 2026 idea-submission deck, screening-ready |

---

## 14. What to do next — pick one

### Track A — zero cost, zero equipment (recommended first)
Close the remaining **paper** decisions so a lab visit is not wasted:
**M2** (reading resolution, once an instrument class is chosen), **S2** (scan ROI rule),
**S5** (repeat scans), **S6** (baseline on a scan), **D1** (per-glyph disagreement),
**C6** (reference population). Each is a short decision memo plus a validator constant.
Then write the **scan-measurement tool** (S1) — the route is already fixed and verified:
a dpi-derived pure-scale homography with a zero-distortion `Camera`, no change to
`p0/measure.py`. It cannot be validated until a real scan exists, so gate it behind a
dry-run requirement.

### Track B — the physical critical path
Arrange **rank 1** equipment first: 2400 dpi optical flatbed scanner, certified length
standard with a certificate, measuring microscope. Then rank 2 (straightedge, gap gauge,
backing plate). **Do not buy rank 3 before rank 1 access is confirmed** — a missing
microscope changes what the pilot can claim at all. Fill
`reference/equipment_inventory.json`, `reference/b2_setup.json` and
`reference/flatness_register.json` and drive the three gates to YES.

### Track C — the product
Start the Android client: capture flow, on-device OCR, the rule-pack evaluator, the evidence
store and the report generator. The measurement engine is the part that already exists and
should be **ported, not rewritten** — it is deliberately dependency-free for that reason.

### Track D — the legal question
**G0**: confirm with the Department of Consumer Affairs what the Rules mean by character
height — which glyphs, which faces, and whether ink extent is the right reading. Until then
the measurand stays a documented proxy with a configurable threshold. The real packaged
products on hand are genuinely useful here.

---

## 15. One-paragraph summary to paste into a new chat

> I am building **NiyamDrishti** for **SIH 2026, PS SIH26034** (Legal Metrology packaged-
> commodity compliance screening). Repo `github.com/dinamsingh/Setu`, branch
> `niyamdrishti-phase0`, HEAD `f88f2d2`. A Phase-0 measurement proof of concept exists:
> pure-stdlib engine, 76-run synthetic benchmark with 10/10 pre-registered criteria PASS,
> 352 tests, and a fully pre-registered physical-experiment design. **No physical
> measurement has been done and no measurement equipment is owned.** Blockers: B1 CLOSED,
> B2 OPEN, B3 CLOSED, B4 OPEN (spec resolved), B5 CLOSED, B6 OPEN (spec resolved) —
> the three open ones are purely physical. Read `HANDOFF.md` at the repo root for the full
> context — **§2 is the problem statement and how we solve it**, §8 is the blocker board —
> then `phase0/docs/P0_EXECUTION_PLAN.md` §12 for the blocker table. House rules:
> reply in Hinglish, be adversarial, derive rather than invent, mark anything the documents
> do not state as UNRESOLVED, never claim first/only/unique/best or legal-grade, never
> present synthetic results as physical, and never move a threshold to make something pass.
