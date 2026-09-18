# B2 practical equipment feasibility audit — minimum viable reference setup

**Question this document answers:** what is the *smallest real-world arrangement* that can
produce an independent reference value for
`VISIBLE_PRINTED_INK_EXTENT_PERPENDICULAR_TO_BASELINE`, without weakening P0's
scientific validity.

**Starting state:** real packaged products are available; **no measurement equipment is
available**. Physical capture has not started.

**Changes nothing:** no measurement algorithm, no `config/`, no P0 criterion or threshold,
no `k = 1.645`, no Solution Lock. B3-B6 untouched. No equipment specification is invented;
every spec below is quoted from an existing document, and anything the documents do not
state is marked UNRESOLVED.

**Verdict: `B2_READY_TO_EXECUTE = NO`** (§10).

---

## 0. A correction that must come first: the products are not the sample

Real packaged products **cannot** substitute for the P0 sample, and this is not a
preference:

| P0 requires | Real product gives | Source |
|---|---|---|
| 20 flat coupons, 5 nominal heights x 4 shapes x 4 fonts, 400 glyph instances | uncontrolled, unknown print, one or two heights | `P0_PROTOCOL.md` §0, `P0_EXECUTION_PLAN.md` §1.2 |
| flat print plane on a rigid backing; residual tilt bounded | curved / flexible / embossed surfaces | `P0_EXECUTION_PLAN.md` §5, A-05 |
| out-of-plane print **provably undetectable** from a single view, so flatness must be mechanical | curvature is the normal case on a pack | A-06; measured 20° local tilt → **0.1847 mm** error with all gates passing |
| a pre-registered panel→glyph assignment | no panel identity at all | B5 |

So the products **do not reduce the B2 equipment requirement at all**. What they are
genuinely useful for, and which is *not* B2:

* answering Solution Lock gate **G0** — what the controlling rule actually means by
  character height (A-09 says our measurand is a proxy, not the legal measurand);
* a later realism / robustness dataset;
* choosing plausible nominal heights.

Consequence: **printed coupons are an upstream prerequisite of B2.** Without them there is
nothing for the reference instrument to measure.

---

## 1. Every equipment item B2 genuinely requires, classified

Classification is for **B2 only** (producing reference values). Several items are required
elsewhere in the experiment and are still marked "not necessary for B2" — that is about
scope, not about whether you eventually need them.

| Item | Documented spec | Class for B2 | Required by protocol? |
|---|---|---|---|
| **Printed coupons** on dimensionally stable stock | `tools/make_coupons_svg.py`, 20 panels (`P0_PROTOCOL.md` §0) | **REQUIRED FOR VALIDATION** (prerequisite) | yes, §0 |
| **Printer at true 100 % scale** | verified against the frame's 100 mm check bar | **REQUIRED FOR VALIDATION** (prerequisite, one-time) | yes, `P0_EXECUTION_PLAN.md` §13, `P0_PROTOCOL.md` §1 step 1 |
| **Flatbed scanner, 2400 dpi optical, 8-bit grey, enhancement off** | `P0_PROTOCOL.md` §0, §3 | **REQUIRED FOR VALIDATION** | yes, explicitly |
| **Certified length standard** — steel scale or glass graticule **with certificate** | `P0_PROTOCOL.md` §0, §3 step 1 | **REQUIRED FOR VALIDATION** (see §5 for the one documented route that removes it) | yes, explicitly |
| **Measuring / toolmaker's microscope** | `P0_PROTOCOL.md` §0, §3 cross-check | **REQUIRED ONLY FOR P1** — but P1 gates every accuracy claim | yes for P1; `P0_EXECUTION_PLAN.md` §13 lists it as PREFERRED for the experiment while stating "P1 depends on it" |
| **Calibrated digital caliper, 0.01 mm, with record** | `P0_PROTOCOL.md` §0 | **NOT ACTUALLY NECESSARY for B2** — explicitly "never a reference" for a 3 mm glyph (`P0_EXECUTION_PLAN.md` §2.3). Required for frame survey (B3/B4) and the 100 % print check | yes, but for a different job |
| **Rigid flat backing plate** | float glass / ground plate ≥150×100 mm | **PREFERRED for B2** — during a scan, flatness is supplied by the platen glass under lid pressure. REQUIRED for camera capture | §3 step 2 says "scan each coupon flat"; the plate is specified for capture (§1, §5) |
| **Fiducial frame** (polyester film / acrylic) | `tools/make_frame_svg.py`, outer 100×60 mm | **OPTIONAL for B2, and decision-contingent** — needed only if decision **S3** is answered "scan the frame lying on the coupon" (then see §5) | S3 is open (`P0_REFERENCE_PROCEDURE.md` §3.2) |
| **Lossless image conversion** to 8-bit grey PNG, no resampling/sharpening | A-02 | **REQUIRED FOR VALIDATION** (software, not equipment) | yes, A-02 |
| Two phones, copy stand/tripod, diffuse lighting, crossed polarisers, second print stock, clamps/vacuum plate | `P0_EXECUTION_PLAN.md` §13 | **NOT ACTUALLY NECESSARY for B2** — these are camera-capture items | not for B2 |
| CMM / optical comparator, dial indicator, DNG-capable phone | `P0_EXECUTION_PLAN.md` §13 OPTIONAL | **OPTIONAL** — §13 already argues the caliper survey contributes only ~0.0006 mm on a 3 mm glyph | no |

**Irreducible B2 equipment set: scanner + certified length standard + measuring
microscope, plus printed coupons.** Everything else in `P0_PROTOCOL.md` §0 belongs to
capture, not to reference.

---

## 2. Per-item justification

### 2.1 Flatbed scanner, 2400 dpi **optical**

* **Why needed:** it is the *primary* reference for **every** camera-measured glyph.
  Without it `reference_h_mm` does not exist, so **P2, P3, P4** and the reporting-only
  **P7** have nothing to compare against, and the scanner half of **P1** is missing.
* **Exact measurement supported:** a 94.488 px/mm greyscale sampling of the panel, from
  which the 50 % linearised-luminance ink boundary is extracted by the estimator.
* **Protocol explicitly requires it?** Yes — `P0_PROTOCOL.md` §0 and §3 ("Primary: flatbed
  scanner at 2400 dpi (94.5 px/mm)").
* **Manual procedure allowed instead?** **No.** §3 step 3 says "measure each glyph with the
  same estimator". The reference uncertainty target is ≤ 0.01 mm = **0.945 px** at
  2400 dpi, so subpixel estimation is mandatory and a human cannot supply it. This is why
  scanner image processing is a *software* blocker (§7 A1), not a manual workaround.
* **Scientific risk if the dpi is substituted:**

  | Scanner | 1 pixel | Verdict |
  |---|---|---|
  | 600 dpi | **0.042333 mm** | one pixel is **larger than P1's entire Go band (0.03 mm)**. Unusable |
  | 1200 dpi | 0.021167 mm | the ≤ 0.01 mm target becomes 0.47 px — the target is no longer credible |
  | 2400 dpi | 0.010583 mm | the documented configuration; target = 0.945 px |
  | 4800 dpi *interpolated* | — | interpolation adds no information and can smooth the ink edge; only **optical** resolution counts |

  Because the documents specify 2400 dpi, any lower figure is a **protocol change**, which
  this audit is not permitted to make. See §6.

### 2.2 Certified length standard (steel scale or glass graticule, with certificate)

* **Why needed:** `P0_PROTOCOL.md` §3 step 1 requires the scanner's scale to be calibrated
  **in both axes** against a certified standard, with platen non-uniformity recorded.
* **Exact measurement supported:** the mm-per-pixel scale of every scanner reference value
  — i.e. a multiplicative factor on `reference_h_mm`.
* **Protocol explicitly requires it?** Yes, §0 and §3 step 1.
* **Manual procedure allowed instead?** The *reading* of the standard is manual; the
  **standard itself** cannot be replaced by an uncertified ruler.
* **Scientific risk if substituted:** this is the **most dangerous** substitution in the
  whole of B2. A scanner scale error is a *common multiplicative bias on every reference
  value*, identical across all glyphs. It therefore does **not** show up as scatter, does
  not trip P3 or P5, and P1 would not catch it either unless the microscope disagrees
  enough to cross 0.03 mm. It would appear as a clean, confident, wrong accuracy result.
  Flatbed carriage-direction scale commonly differs from sensor-direction scale, which is
  exactly why the protocol says *both axes*.
* **Modelling note:** anisotropic scale is representable (`fx ≠ fy`, §4). **Platen
  non-uniformity is not** — that needs correction rule **S4**, still open.

### 2.3 Measuring / toolmaker's microscope

* **Why needed:** it is the **only** independent realisation of the measurand. Per
  `P0_REFERENCE_PROCEDURE.md` §2, the scanner tier reuses the pipeline estimator, so
  P2/P3/P4 are blind to estimator-definitional bias (measured at **0.0054 mm** on `RING_O`
  on ideal renders). Only P1 tests the ink-boundary definition itself.
* **Exact measurement supported:** **P1** — mean absolute scanner-vs-microscope difference
  over ≥ 15 glyphs spanning heights, shapes and fonts.
* **Protocol explicitly requires it?** Yes for P1 (`P0_PROTOCOL.md` §3). Note the
  inconsistency of emphasis: `P0_EXECUTION_PLAN.md` §13 files it under **PREFERRED** while
  the same row says "P1 depends on it", and §13's MISSING table states that without it
  "**P1 becomes uncomputable → no accuracy claim may be made**". Treat the stronger
  statement as binding.
* **Manual procedure allowed instead?** **Yes — manual is the required mode.** The
  documented procedure *is* a human crosshair reading
  (`measurement_procedure = MANUAL_VISUAL_CROSSHAIR`), and rule **R1** forbids a microscope
  row from running the pipeline estimator. No software is needed for this tier at all.
* **Scientific risk if dropped:** not a degraded claim — **no accuracy claim at all**
  (`P0_CRITERIA.md` line 92, `P0_PROTOCOL.md` §3 P1 No-go).
* **Reading-resolution consequence (derived, NOT a specification):** the documents give no
  microscope resolution (**M2**). Arithmetically, a reading step `d` contributes about
  `d/4` to a mean absolute difference:

  | Reading step `d` | Contribution to P1 | Share of the 0.03 mm Go band |
  |---|---|---|
  | 0.001 mm | 0.00025 mm | 0.8 % |
  | 0.01 mm | 0.0025 mm | 8.3 % |
  | 0.02 mm | 0.005 mm | 16.7 % |
  | 0.05 mm | 0.0125 mm | **41.7 %** |

  A 0.05 mm-step instrument would spend nearly half of P1's Go band on its own
  quantisation before any real disagreement is measured. This is a *consequence* of the
  frozen P1 band, offered to inform decision **M2** — it is **not** an equipment spec and
  needs owner sign-off.

### 2.4 Printed coupons and a true-100 % printer

* **Why needed:** B2 must measure a physical artefact carrying known nominal heights,
  multiple shapes and multiple fonts. `panels.json` nominal heights are a **print
  instruction only** and may never be used as reference values
  (`P0_EXECUTION_PLAN.md` §2.2).
* **Manual instead?** The 100 % verification is manual (caliper on the 100 mm check bar,
  `P0_PROTOCOL.md` §1 step 1).
* **Risk if substituted:** printing at, say, 96 % does **not** invalidate B2 (the reference
  is measured, not assumed) but it shifts the real heights away from the nominal matrix,
  which can push the 3 mm class — the class **P2** is computed on — off its intended value.

---

## 3. Minimum viable setup

Everything below is necessary; nothing else is.

```
PHYSICAL
  1. Printed coupons, flat, dimensionally stable stock          (prerequisite)
  2. Flatbed scanner, 2400 dpi OPTICAL, 8-bit grey, enhancement off
  3. Scale traceability, one of:
       3a. certified steel scale / glass graticule WITH certificate   [documented default]
       3b. the caliper-surveyed fiducial frame scanned with the coupon [S3 route, §5 —
           requires reconciling §3 step 1 first]
  4. Measuring / toolmaker's microscope + a trained operator    (P1 only; without it,
                                                                 no accuracy claim)
  5. Calibrated digital caliper                                 (NOT a glyph reference;
                                                                 needed for 3b and for the
                                                                 100 % print check)

SOFTWARE (no equipment, and must exist BEFORE the instruments are touched — §9)
  6. a scan-measurement path   (S1/S2, §7 A1-A2)
  7. lossless scanner output → 8-bit grey PNG, no resampling/sharpening (A-02)

WRITTEN DECISION (no equipment, no code)
  8. M1 — the microscope operator's edge criterion
```

Not needed for B2: phones, copy stand, lighting, polarisers, second print stock, clamps,
CMM, optical comparator, dial indicator.

---

## 4. Feasibility check performed: is a scan representable at all?

The concern behind S1 was that `p0.measure.measure_glyph` needs a homography and a
fiducial while a flatbed scan has neither. **Checked, read-only, no file changed:** a
fronto-parallel zero-distortion pinhole view is *mathematically exactly* a uniform scale,
so a scan is exactly representable in the existing camera model:

```
target                     94.488189 px/mm
rho at plane centre        94.488189 px/mm   (geometric mean, min, anisotropy 1.000000)
rho at (20,10) mm          94.488189 px/mm
rho spread across plane    0.000e+00 px/mm
view tilt                  0.000000 deg
H row 3 (perspective)      [0.000e+00, 0.000e+00, 1.000e+03]
```

**Therefore:**

* S1 is a **software-wiring** blocker, **not** a modelling or equipment problem. No change
  to `p0/measure.py` is implied — `measure_glyph(img, cam, H, Hinv, roi_mm, …)` already
  accepts a caller-supplied `H`.
* Anisotropic scanner scale is representable as `fx ≠ fy`, which is what §3 step 1's
  "both axes" calibration feeds.
* **Platen non-uniformity is NOT representable** by a single homography — it needs the
  still-undecided **S4** correction rule.
* This does **not** close S1. There is still no scanner, no scan, and no ROI (S2), so any
  such tool would be written against no test article. That was the STEP 4 reason for not
  writing it, and it stands.

---

## 5. Can the documented scanner + microscope arrangement be simplified?

### 5.1 The microscope tier cannot be simplified away

Removing it does not simplify P1 — it **deletes** P1, and with it every accuracy claim.
Replacing it with anything that runs the pipeline estimator violates **R1/R2** and is
rejected by `tools/validate_reference_table.py`. Not simplifiable.

### 5.2 The scanner tier can be simplified — via decision S3, at a measurable cost

`P0_REFERENCE_PROCEDURE.md` §3.2 **S3** already raises, and leaves open, the option of
scanning the coupon **with the fiducial frame lying on it**. Taking that option:

**Gains**

| Gain | Detail |
|---|---|
| No new measurement code | the scan becomes an ordinary very-high-`rho` fronto-parallel capture; the existing `tools/run_real_batch.py` + `p0.measure` path applies. Closes **S1** |
| **S6** dissolves | baseline direction comes from the existing `estimate_baseline_dir`, not a new rule |
| Metric scale no longer depends on the scanner | per **A-08**, scale comes from the *surveyed fiducial*, not the imaging device. The certified graticule stops being a scale dependency (item 3a → 3b), leaving the caliper, which is required anyway |
| **S4** softens | if scale comes from the frame inside the same scan, platen scale non-uniformity is absorbed by the local homography instead of needing a platen map |
| One ROI solution serves twice | S2 becomes the *same* problem as B3 rather than a second one |

**Costs — stated, not hidden**

1. The scanner reference then shares the fiducial-detection and homography chain with the
   phone path, so **P2/P3/P4 additionally become blind to frame-survey scale error**, on
   top of the already-disclosed estimator blindness. Magnitude is bounded and small:
   `P0_EXECUTION_PLAN.md` §13 records the caliper survey contributing **~0.0006 mm on a
   3 mm glyph** — about **11 %** of the estimator bias already accepted (0.0054 mm), and
   **2 %** of P1's Go band.
2. It needs the fiducial frame to physically exist (film/acrylic) and to lie flush on the
   coupon under the scanner lid without bowing.
3. `P0_PROTOCOL.md` §3 step 1 still *literally* demands graticule calibration of the
   scanner scale. Choosing S3 means **reconciling that sentence** — a human decision
   (§8 C7), not something this audit may declare.

### 5.3 What this simplification does **not** touch

**P1 is completely unchanged** under S3: same statistic (mean absolute
scanner-vs-microscope difference), same bands (≤ 0.03 / 0.03-0.06 / > 0.06 mm), same
minimum of 15 paired glyphs, same `compute_p1` code path, same independence rules R1-R5.
The simplification is confined to *how the scanner value is produced*, not to what P1
compares. No criterion, threshold or `k` is affected.

---

## 6. Substitutes — status from the existing documents only

No substitute instrument is invented here. Status is assigned strictly on what the
documents already say.

| Proposed substitute | Status | Basis |
|---|---|---|
| **1200 / 600 dpi scanner** instead of 2400 dpi | **NOT ACCEPTABLE** | `P0_PROTOCOL.md` §0/§3 specify 2400 dpi and a ≤ 0.01 mm target. At 600 dpi one pixel (0.0423 mm) exceeds P1's whole Go band. Relaxing the dpi is a frozen-protocol change |
| **Trusting the scanner's nameplate dpi** instead of a certified standard | **NOT ACCEPTABLE** | §3 step 1 requires calibration against a certified standard in both axes |
| **Caliper-surveyed fiducial frame** as the scan's scale reference (S3 route) | **CONDITIONALLY ACCEPTABLE** | The option is raised by the documents themselves (§2.5, S3) and is consistent with **A-08**. Conditions: the frame exists and stays flat in the scan; §3 step 1 is reconciled; the ~0.0006 mm blindness in §5.2 is disclosed in every result statement |
| **Digital caliper across a 3 mm glyph** | **NOT ACCEPTABLE** | `P0_EXECUTION_PLAN.md` §2.3 lists it as "never a reference"; it cannot realise an ink-boundary measurand |
| **`panels.json` nominal heights** as ground truth | **NOT ACCEPTABLE** | §2.2 and `P0_PROTOCOL.md` §3 both prohibit it explicitly |
| **A second scanner / second scan at a different dpi** in place of the microscope | **NOT ACCEPTABLE** | It is the same photometric realisation; if it runs the estimator, **R2** rejects the pair, and if it does not, nothing defines what it measures. It is also not representable — `method` is enumerated `SCANNER_2400DPI \| MICROSCOPE` |
| **Some other independently calibrated optical method** in place of the microscope | **CONDITIONALLY ACCEPTABLE** | This is `P0_EXECUTION_PLAN.md` §13's own wording: "a second, independently calibrated optical method … (needs agreement)". Conditions: it must not execute the pipeline estimator (R1/R2), it needs a written edge criterion (M1-equivalent), and `method` plus the validator enum must be extended — a small, deliberate change, **not made here** |
| **Recording P1 as "not evaluated"** and proceeding | **CONDITIONALLY ACCEPTABLE, and expensive** | §13 offers it: "explicitly record P1 as not evaluated and **drop every accuracy claim**". Then P2/P3/P4 are uninterpretable and P0 produces only a capture-feasibility result |
| **Real packaged products** in place of printed coupons | **NOT ACCEPTABLE** | §0 above: breaks §1.2's nominal matrix, §5's flatness requirement and B5 |
| **CMM / optical comparator** in place of the microscope | **CONDITIONALLY ACCEPTABLE** | §13 already lists a CMM as OPTIONAL for the survey; as a *P1* partner it is the "second independently calibrated optical method" case above, with the same conditions |

---

## 7. A. Software blockers (no equipment needed, can be done now)

| # | Blocker | Maps to | Notes |
|---|---|---|---|
| A1 | No scan-measurement entry point | **S1** | §4 proves the model supports it. Two routes: wire `p0.measure` with a scale-only `H` + zero-distortion `Camera`, **or** take the S3 route and reuse `run_real_batch.py` with no new measurement code |
| A2 | Glyph ROI in a scan is undetermined | **S2** | Same class as **B3**; one solution serves both. Not solved here |
| A3 | Scanner output → 8-bit grey PNG without resampling or sharpening | **A-02** | The reader accepts 8-bit grey PNG only; a TIFF/JPEG path must be verified not to sharpen |
| A4 | Platen non-uniformity correction rule then code | **S4** | Rule is a human decision (C4); the code after it is small |
| A5 | Baseline direction on a scan | **S6** | `estimate_baseline_dir` exists; dissolves entirely under S3 |
| A6 | `method` / procedure enums would need extending for any agreed substitute instrument | §6 | Deliberately **not** pre-extended — an unused enum value invites a silent substitution |

**None of A1-A6 requires owning or borrowing anything.** They are the part that can
progress today, and §9 argues they *must* progress before any instrument is touched.

## 7. B. Equipment blockers (cannot be solved in software)

| # | Blocker | Blocks |
|---|---|---|
| B-i | 2400 dpi optical flatbed scanner | every reference value → P2/P3/P4/P7 and P1's scanner side |
| B-ii | Certified length standard with certificate (unless S3 + reconciliation) | scanner scale traceability; `instrument_cal_ref` |
| B-iii | Measuring microscope + trained operator | **P1**, therefore every accuracy claim |
| B-iv | Printed coupons + true-100 % printer | there is otherwise nothing to measure |
| B-v | Calibrated caliper | the 100 % print check and (under S3) the frame survey that carries scale |

## 7. C. Human procedure decisions (no equipment, no code, free to make today)

| # | Decision | Why it is the cheapest progress available |
|---|---|---|
| C1 | **M1 — microscope edge criterion** | The single hardest B2 item, and it costs nothing but agreement. Without it two operators measure different quantities and P1 is uninterpretable |
| C2 | M2 magnification / illumination / stage resolution | §2.3's table informs it; the decision is still the owner's |
| C3 | M3 perpendicularity on the stage; M4 repeats → `reference_u_mm`; M5 operator training | all procedural |
| C4 | **S3 — scan the frame with the coupon, or not** | unlocks the most (§5.2); changes S1, S2, S4, S6 and the graticule dependency |
| C5 | S5 repeat scans, and what `n_repeats` aggregates | determines the stated `reference_u_mm` |
| C6 | Reference population: all 400 glyphs or a **pre-declared** reduction | must be fixed before capture (`P0_PROTOCOL.md` §3 step 3) |
| C7 | Reconciling §3 step 1's graticule sentence if C4 = "with frame" | documentation consistency |
| C8 | **D1** — per-glyph `DISAGREED` threshold, and what follows | only the aggregate 0.06 mm rule exists today |
| C9 | Cross-check subset: which ≥15 glyphs, and whether it includes the 20 camera-measured ones | entangled with **B5**; must not be chosen after seeing camera data |
| C10 | Operator independence / blinding roster (§8) | e.g. microscope first and blind, or a different person |

---

## 8. B2 minimum setup checklist — one page

Truly required items only. Tick each; B2 stays OPEN until all are ticked **and verified**.

```
PREREQUISITE ARTEFACT
[ ] Coupons printed from tools/make_coupons_svg.py, 20 panels, stable stock, flat
[ ] 100 mm check bar verified with a calibrated caliper (print scale within 1 %)

SCANNER PATH  (produces reference_h_mm for every camera-measured glyph)
[ ] Flatbed scanner, 2400 dpi OPTICAL (not interpolated), 8-bit grey, ALL enhancement off
[ ] instrument_id recorded; one scanner only, for all panels
[ ] Scale traceability chosen and recorded, ONE of:
      [ ] 3a certified steel scale / glass graticule + certificate reference
      [ ] 3b fiducial frame scanned with the coupon (S3) + §3-step-1 reconciliation
[ ] Both-axis scale factors measured and recorded
[ ] Platen non-uniformity recorded AND a correction rule decided (S4)
[ ] Scan-measurement software exists and has been dry-run end to end (A1, A2, A3)
[ ] reference_u_mm achieved and stated; protocol target <= 0.01 mm
[ ] Reference population pre-declared (all 400, or a declared reduction) (C6)

MICROSCOPE PATH  (P1 only — without it, no accuracy claim is permitted)
[ ] Measuring / toolmaker's microscope available; instrument_id + calibration ref recorded
[ ] M1 edge criterion WRITTEN DOWN before the first reading
[ ] M2 magnification / illumination / reading resolution recorded
[ ] M3 perpendicularity method; M4 repeats -> reference_u_mm; M5 operator trained
[ ] >= 15 glyphs, spanning heights, shapes and fonts, pre-registered (C9, needs B5)
[ ] Operator independence + blinding respected (C10): the microscope operator has not
    produced and has not seen the scanner values for those glyphs

RECORDING AND GATING
[ ] reference_table.csv filled to the 18-field schema (P0_REFERENCE_PROCEDURE.md §6)
[ ] python3 tools/validate_reference_table.py --table ... --agreement  ->  ACCEPTED
[ ] P1 computed from the reference table ALONE, before any phone data exists
[ ] Table committed before the first camera capture
[ ] D1 recorded (C8); every DISAGREED / UNUSABLE row carries a note

NOT required for B2: phones, copy stand, lighting, polarisers, CMM, dial indicator,
second print stock, clamps.
```

---

## 9. Acquisition / borrowing plan

| Item | Likely route | Notes |
|---|---|---|
| **Flatbed scanner, 2400 dpi optical** | **can likely be borrowed** — college library, office, print shop, document-digitisation or reprographics unit | Verify **optical** resolution on the nameplate/driver, not the marketing figure; confirm enhancement/auto-tone can be switched off and 8-bit grey obtained |
| **Certified steel scale / glass graticule** | **needs a specialist lab** and **must be certified/calibrated** | Metrology / mechanical-measurement lab; a biology-microscopy lab often has a stage micrometer with a certificate. The certificate reference goes into `instrument_cal_ref`; an uncertified ruler is NOT ACCEPTABLE (§6) |
| **Measuring / toolmaker's microscope** | **needs a specialist lab** | Mechanical-engineering metrology lab, production/tool-room lab, or a QC lab. Also needs a person who can be trained to the M1 criterion |
| **Calibrated digital caliper** | **can likely be borrowed**, but **must have a calibration record** | Any mechanical lab / workshop |
| **Printer at true 100 %** | **can likely be borrowed / commercial** | Verify with the 100 mm check bar; do not trust "fit to page" |
| **Coupon and frame stock** (polyester film, acrylic, float glass) | **purchase, cheap** | Dimensional stability matters more than print quality (`P0_PROTOCOL.md` §0) |
| **The M1 edge criterion** | **cannot be borrowed or substituted** | It is a definition. It is also free |
| **A reference that shares the pipeline estimator on both sides of P1** | **cannot be substituted safely** | R2 rejects it; it would report agreement it never tested |

**Practical bundling:** items 2 (graticule), 3 (microscope) and 4 (caliper) usually live in
the **same** mechanical-metrology lab, and the scanner is usually elsewhere. That is two
visits, not five.

---

## 10. Can B2 be closed without owning the equipment?

**Yes — ownership is not necessary. Access is.** Nothing in the documents requires that
the instruments be owned; what they require is *identity, traceability and independence*,
all of which a borrowed instrument can satisfy:

* `instrument_id` and `instrument_cal_ref` are per-row fields — a borrowed instrument with
  a certificate records exactly as well as an owned one.
* P1 needs ≥ 15 glyphs, which is a few hours of microscope time, not a standing
  arrangement.

**Four conditions make borrowing safe, and all four are easy to violate:**

1. **One scanner, one session, all panels.** Returning later to a *different* scanner
   splits the reference population across two uncalibrated scales. That discontinuity is a
   common-mode bias inside each subset and is **invisible** in the data. If a second
   session is unavoidable, it must be the same physical unit and must be re-calibrated
   against the standard, with both calibrations recorded.
2. **Calibrate in the same session, at the platen positions actually used.** A graticule
   reading taken on a different visit does not describe today's scan.
3. **Software first.** All of §7 A1-A3 must be working *before* the visit. Discovering in
   the lab that a scan cannot be processed wastes the access, and the temptation then is to
   improvise — which is precisely how a visual criterion silently replaces the photometric
   one.
4. **Blinding survives the visit.** If one person does both instruments in one afternoon,
   observer independence (§2 point 2, `P0_EXECUTION_PLAN.md` §8) is lost. Simplest fix:
   microscope readings first, then the scanner — or two people.

**Is one college/lab visit realistic?** For the *microscope* tier, yes — ≥ 15 glyphs plus
M4 repeats is a single session, provided M1 is written beforehand. For the *scanner* tier,
a visit is only useful if A1-A3 already work and the scale standard is available in the
same session; otherwise the visit produces images that cannot become reference values. So:
**plausible in two visits, but only after the software and M1 exist.** The order is
software and decisions first, instruments second.

---

## 11. Remaining decisions, and what must be physically arranged

**Decide (free, today):** C1 **M1**, C4 **S3** — these two unlock the most. Then C2, C3,
C5, C6, C7, C8, C10. C9 waits on B5.

**Build (free, today):** A1, A2 (couples to B3), A3; then A4, A5 once C4/S4 land.

**Physically arrange:** coupons printed and verified at 100 %; a 2400 dpi optical flatbed;
a certified length standard **or** the surveyed fiducial frame under S3; a measuring
microscope with a trained operator; a calibrated caliper.

## 12. Verdict

```
B2_READY_TO_EXECUTE = NO
B2 = OPEN
```

No instrument is available, three of the nine checklist blocks cannot be started, and the
two decisions that cost nothing (M1, S3) are still open. Nothing in this audit changed a
criterion, a threshold, `k = 1.645`, the measurement algorithm or the Solution Lock, and
no equipment was assumed to exist.

**B2 remains OPEN until an actual reference setup is available and verified** — verified
meaning: the checklist in §8 is fully ticked, `validate_reference_table.py` returns
`ACCEPTED` on a real table, and P1 has been computed from that table before any phone
capture is analysed.
