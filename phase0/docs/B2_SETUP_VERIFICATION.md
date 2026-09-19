# B2 pre-capture verification spec — "when we reach the lab, what exactly must be verified"

**Purpose:** turn the remaining B2 blockers into checks a student can perform on the day,
and into one machine-checkable gate.

**Starting state:** none of the reference equipment is owned. No physical experiment has
started. `M1` is frozen, `S3 = NO`.

**Changes nothing:** no measurement algorithm, no `config/`, no P1-P7 threshold, no
`k = 1.645`, no Solution Lock, no synthetic artefact. B3-B6 untouched. **No equipment
specification is invented** — every number below is quoted from `P0_PROTOCOL.md`,
`P0_CRITERIA.md`, `P0_ASSUMPTIONS.md`, `P0_EXECUTION_PLAN.md`, `PHASE0_REVIEW.md` or
`config/`, and anything the documents do not state is marked UNRESOLVED.

**Verdict: `B2_PRECAPTURE_READY = NO`, `B2 = OPEN`** (§9).

---

## 1. Scanner — B2-1 verification

Every numeric value is documented: 2400 dpi and 8-bit greyscale from `P0_PROTOCOL.md` §0
and §3 step 2; both-axis calibration and platen non-uniformity from §3 step 1; the
≤ 0.01 mm uncertainty target from §3 step 4; lossless input from **A-02**; `frame_in_scan`
from the frozen **S3 = NO**.

| # | Check | Verify exactly this | Level |
|---|---|---|---|
| S-1 | **Optical 2400 dpi capability** | the **sensor's optical** resolution from the driver or nameplate, ≥ 2400 dpi. An "interpolated"/"enhanced" figure does not count — interpolation adds no information and can smooth the ink edge. Reference: at 600 dpi one pixel is 0.042333 mm, **larger than P1's whole 0.03 mm Go band**; at 1200 dpi the 0.01 mm target is 0.47 px | **REQUIRED** |
| S-2 | **Actual scan mode used** | the scan is *taken* at ≥ 2400 dpi, not taken lower and upsampled, nor taken higher and downsampled. Record `dpi_used_for_scan` separately from the capability | **REQUIRED** |
| S-3 | **Greyscale, bit depth** | greyscale mode, ≥ 8 bits. Colour is not forbidden by the documents but adds a channel-mixing step that A-02 does not define | **REQUIRED** |
| S-4 | **Enhancement / sharpening off** | each option switched off is **named**: unsharp/sharpening, descreen, dust-and-scratch removal, auto tone/level/exposure, colour restoration, backlight correction. "All off" with nothing named is not evidence. A-02: any sharpening or tone mapping moves the boundary | **REQUIRED** |
| S-5 | **File format** | a lossless format out of the scanner (`PNG`, `TIFF`, `BMP`, `PPM`, `PGM`). **JPEG fails.** Then the conversion to 8-bit grey PNG is verified not to sharpen or tone map, and the command is recorded (A-02) | **REQUIRED** |
| S-6 | **No resampling or rescaling** | explicitly false, in the driver and in any conversion step | **REQUIRED** |
| S-7 | **Scale calibration** | the scanner's scale measured against the certified standard **in the same session**, with the calibration reference recorded (`P0_PROTOCOL.md` §3 step 1). A calibration from another visit does not describe today's scan | **REQUIRED** |
| S-8 | **Both-axis calibration** | `scale_factor_x` **and** `scale_factor_y` recorded separately. Flatbed carriage-direction scale commonly differs from sensor-direction scale, which is why §3 step 1 says *both axes*. Anisotropy is representable (`fx ≠ fy`) and the `max_jacobian_ratio: 3.0` gate tolerates it easily | **REQUIRED** |
| S-9 | **Platen consistency (S4)** | non-uniformity across the platen **recorded**, and the positions at which panels are placed recorded. See §4 — recording is all the protocol asks for, and it is *not* a correction | **REQUIRED** to record; the correction rule is **UNRESOLVED** |
| S-10 | **Session consistency** | one physical unit for **all** panels, in one calibrated session. A second session on a different scanner splits the reference population across two uncalibrated scales; that discontinuity is common-mode within each subset and **invisible** in the data | **REQUIRED** |
| S-11 | **Instrument identity + calibration record** | `instrument_id` naming one unit, and `instrument_cal_ref` for the reference table. A borrowed scanner is fine; an anonymous one is not | **REQUIRED** |
| S-12 | **`frame_in_scan = false`** | the fiducial frame is **not** on the coupon during the scan (**S3 = NO**, `P0_REFERENCE_PROCEDURE.md` §3.2) | **REQUIRED** |
| S-13 | Repeat scans per panel | how many, and whether `n_repeats` aggregates repeat scans or repeated readings of one scan | **REQUIRED**, and **UNRESOLVED (S5)** |
| S-14 | Lid pressure / coupon flatness on the platen | the coupon lies flat against the platen glass with the lid closed | **PREFERRED** — the platen supplies flatness; no numeric requirement is documented for the scan |
| S-15 | Warm-up and a second calibration read at the end of the session | detects drift within the session | **PREFERRED** — no documented requirement, but it is free |
| S-16 | Scanner make/model beyond the id | helps a later reader judge the optics | **OPTIONAL** |

**What cannot be verified without the scanner:** S-1 through S-15 all need the unit in
hand. Nothing in this group can be closed in advance; what this step does is remove any
ambiguity about *what* is being checked.

---

## 2. Microscope — B2-2 verification

**Acceptance is tied to the frozen protocol, not to how impressive an instrument sounds.**
The binding requirements are: it must produce a *stage reading*, it must permit the frozen
**M1** procedure, and it must be traceable.

| # | Check | Verify exactly this | Level |
|---|---|---|---|
| M-1 | **Microscope type** | one of the classes the documents actually name — measuring microscope, toolmaker's microscope, or USB microscope with a calibration slide (`P0_PROTOCOL.md` §0, `PHASE0_REVIEW.md` §15). §15 lists the USB route as "**acceptable secondary**", so it passes with that flag attached | **REQUIRED** |
| M-2 | **It measures, not just magnifies** | an **X-Y stage with a position readout**. A magnifier or a camera-only microscope cannot produce a reference value at all, however sharp the image looks | **REQUIRED** |
| M-3 | **Stage rotation** | the stage can be rotated, because **M3** realises perpendicularity by rotating until the baseline is parallel to X (`P0_REFERENCE_PROCEDURE.md` §4.2.4) | **REQUIRED** |
| M-4 | **Measurement resolution / readability** | the stage **reading step**, as a number. `PHASE0_REVIEW.md` §15 records ~1-2 µm for a micrometer-stage toolmaker's microscope and ~0.01 mm for a USB microscope with a calibration slide. Derived consequence, reported not enforced: a reading step *d* contributes about *d*/4 to a mean absolute difference, so 0.01 mm → 8.3 % of P1's Go band and 0.05 mm → **41.7 %**. **No limit is invented here** — this is decision **M2** | **REQUIRED** to state; the acceptable value is **UNRESOLVED (M2)** |
| M-5 | **Certified scale / graticule for the microscope's own scale** | whatever the instrument's calibration rests on, referenced. For the USB class `PHASE0_REVIEW.md` §15 explicitly names a calibration slide; for a micrometer stage it is the instrument certificate | **REQUIRED** |
| M-6 | **Magnification and illumination** | magnification recorded; illumination **reflected / episcopic**. Transmitted light images the substrate, not the ink (`P0_REFERENCE_PROCEDURE.md` §4.2.4) | **REQUIRED** |
| M-7 | **Operator qualification / training (M5)** | the operator has read **M1** (§4.2.3), has the §4.2.6 checklist to hand, and has been trained against it before the first counted reading | **REQUIRED**, and **UNRESOLVED until performed (M5)** |
| M-8 | **M1 bisection procedure** | two crosshairs per edge — **O** (last clean substrate) and **I** (tone stops deepening) — boundary = (O + I)/2, height = separation of the two edge midpoints. Read at mid-stroke on the flat top for `FLAT_TOP`, at the apex for `ROUND` | **REQUIRED** |
| M-9 | **Repeatability procedure** | **≥ 3 independent re-settings** per glyph — crosshairs backed fully off and re-set, never re-read from one setting. `reference_h_mm` = mean; `reference_u_mm` = *s*/√*n* (**M4**) | **REQUIRED** |
| M-10 | **Raw-reading recording** | `raw_readings` in the frozen form `Obot/Ibot/Itop/Otop`, repeats separated by `;`, so `tools/validate_reference_table.py` can re-derive the recorded value. A mismatch is an **error**, not a warning | **REQUIRED** |
| M-11 | **Ambiguity handling** | the operator knows that an unresolvable band means `cross_check_status = UNUSABLE` **plus a note**, never a guessed single edge | **REQUIRED** |
| M-12 | **Inter-operator agreement** | a second operator reads a few of the same glyphs, blind | **PREFERRED** — it is M5's second half and quantifies the human spread in the M1 judgement |
| M-13 | Photograph of the eyepiece view for a couple of glyphs | makes the O/I judgement reviewable later | **OPTIONAL** |

**Explicitly not acceptance criteria:** stated magnification on its own, "digital
microscope with 1000×", camera megapixels, or screen zoom. None of these produce a stage
reading, and M1 needs positions.

---

## 3. Calibrated length standard — B2-3 evidence

**No certification scheme, authority or certificate format is prescribed here.** What is
required is that the certificate *exists*, is *transcribed*, and is *traceable in its own
words*. The field set mirrors the repository's own certificate precedent —
`config/frames/*.json` carries `issued_at`, `expires_at`, a stated uncertainty and a
`certificate_hash`, and `tools/survey_frame.py` records the instrument as
"make, model, cal date".

| # | Evidence | Verify exactly this | Level |
|---|---|---|---|
| C-1 | **The standard** | a certified steel scale **or** glass graticule (`P0_PROTOCOL.md` §0). An uncertified ruler is **NOT ACCEPTABLE** | **REQUIRED** |
| C-2 | **Identity** | `standard_id` naming the physical item | **REQUIRED** |
| C-3 | **Certificate reference** | the certificate number / reference, transcribed. This is what goes into `instrument_cal_ref` in the reference table | **REQUIRED** |
| C-4 | **Issue date** | as printed on the certificate | **REQUIRED** |
| C-5 | **Validity / expiry** | as printed, **if the certificate states one**. The repository's frame certificates carry `expires_at`, so an expiry is expected where it exists; no expiry period is invented | **PREFERRED** (REQUIRED if the certificate states one) |
| C-6 | **Traceability information** | what the certificate says it traces to, quoted rather than paraphrased | **REQUIRED** |
| C-7 | **Stated uncertainty** | the certificate's own uncertainty figure, transcribed as a number in mm. Reported against the documented ≤ 0.01 mm reference target (`P0_PROTOCOL.md` §3 step 4) — the scanner tier cannot be better than its own scale reference | **REQUIRED** to state; an advisory flag fires if it is not below 0.01 mm |
| C-8 | **Both-axis scale verification** | the standard was actually used along **both** scanner axes, at the platen positions used for the panels | **REQUIRED** |
| C-9 | Photograph of the certificate alongside the item | protects against a certificate/item mix-up | **PREFERRED** |

---

## 4. S4 — platen non-uniformity: **EQUIPMENT-DEPENDENT, UNRESOLVED**

### 4.1 What the S4 problem actually is

A flatbed's mm-per-pixel is not perfectly constant across the glass: it varies with
position along the carriage travel and across the sensor bar. Since **S3 = NO**, the scan's
metric scale comes from the platen and the calibrated dpi — so this variation lands
*directly* on every `reference_h_mm`. `P0_PROTOCOL.md` §3 step 1 requires it to be
"record[ed]" and stops there.

### 4.2 What the repository can and cannot do about it

| Question | Answer, from the current repository |
|---|---|
| Can a single homography absorb it? | **No.** A *uniform* scale, including an anisotropic one (`fx ≠ fy`), is exactly representable — `B2_MINIMUM_SETUP.md` §4 measured ρ spread `0.000e+00 px/mm` and anisotropy `1.000000` for a fronto-parallel view. A **spatially varying** scale is not representable by one homography |
| Is there an existing detector for scale inconsistency? | Yes — `p0.geometry.leave_one_group_out_scale` and the `max_lomo_rel_spread: 0.005` gate. **But it needs fiducial markers**, and under S3 = NO there are none in the scan. **So the repository's only scale-consistency detector does not apply to the scan path.** This is a direct cost of S3 = NO and is stated rather than hidden |
| Does the protocol contain a verification *method*? | **No.** §3 step 1 is a recording instruction. It names no positions, no statistic and no limit |
| What can be measured before the experiment? | **Nothing.** Every input needs the physical scanner |
| What software correction exists? | **None**, and none is written here: a correction rule has to be decided before it can be implemented |

### 4.3 Context for the decision — **not** a threshold

Two documented numbers bound how much room there is, offered so the owner can decide S4
rather than to decide it for them:

* the reference-uncertainty target is **≤ 0.01 mm** (`P0_PROTOCOL.md` §3 step 4). On the
  3 mm class that P2 is computed on, 0.01 mm is **0.333 %** of scale;
* the existing scale-consistency gate allows a leave-one-out spread of **0.5 %**
  (`max_lomo_rel_spread`), which on a 3 mm glyph is **0.015 mm** — *looser* than the
  reference target implies, and in any case unavailable here (§4.2).

**No acceptance threshold is created.** What S4 needs is: the positions at which the
standard is read across the platen, the statistic computed from those readings, the
correction (or the decision not to correct), and the disposition if the variation is large.

### 4.4 Status

```
S4 = UNRESOLVED and EQUIPMENT-DEPENDENT
```

It cannot be closed, verified or usefully coded before scanner access. The pre-capture gate
therefore returns **NO** while `S4_platen_rule` is unresolved, and the lab checklist records
the platen readings so that the rule can be decided from real data rather than guessed.

---

## 5. B2 lab-visit checklist

One page, usable by a student with this document and nothing else. Fill the evidence file as
you go: `python3 tools/verify_b2_setup.py --template reference/b2_setup.json`.

| CHECK | WHAT TO VERIFY | PASS CONDITION |
|---|---|---|
| **Scanner — resolution** | driver/nameplate optical dpi, and the dpi the scan is actually taken at | both ≥ **2400 dpi optical**; the word "interpolated" appears nowhere |
| **Scanner — mode** | greyscale, bit depth | greyscale, **≥ 8-bit** |
| **Scanner — enhancement** | open every driver tab; list each option you switch off | sharpening, descreen, dust removal, auto tone and colour restoration all **off and named** |
| **Scanner — output** | saved file format; then the conversion to 8-bit grey PNG | lossless out (**not JPEG**); conversion verified not to sharpen; command written down |
| **Scanner — no resample** | driver output size vs dpi × physical size | no rescale anywhere in the chain |
| **Scanner — scale** | read the certified standard on the platen, **both axes**, at the positions the panels will occupy | `scale_factor_x` and `scale_factor_y` both written down, with the calibration reference |
| **Scanner — platen (S4)** | read the standard at several positions across the platen; write every reading down | readings recorded **and** the panel positions recorded. *Recording is the pass condition; the correction rule is still open* |
| **Scanner — session** | is this the unit that will scan **all 20 panels**, today, after this calibration? | one unit, one session, `instrument_id` written down |
| **Scanner — S3** | the fiducial frame is **off** the coupon during the scan | frame not in the scan |
| **Microscope — it measures** | X-Y stage with a position readout; stage rotates | both present; a magnifier-only instrument **fails** |
| **Microscope — reading step** | the smallest stage increment you can actually read | a number, in mm, written down (M2) |
| **Microscope — illumination** | reflected (from above), not transmitted | reflected |
| **Microscope — traceability** | instrument certificate or calibration slide reference | reference written down |
| **Microscope — operator** | operator has read M1 §4.2.3 and holds the §4.2.6 checklist | yes, before the first counted reading |
| **Microscope — procedure** | two crosshairs per edge (O then I), midpoint, ≥ 3 full re-settings | `Obot/Ibot/Itop/Otop` written for every repeat |
| **Microscope — blinding** | has this operator seen any scanner value for these glyphs? | **no** — take microscope readings first |
| **Graticule / steel scale** | certificate exists; transcribe reference, issue date, expiry, traceability, stated uncertainty | all five transcribed; **an uncertified ruler fails** |
| **Caliper** | resolution and calibration record | ≤ **0.01 mm** and a calibration record; **never used on a glyph** |
| **Printer** | measure the frame's **100.000 mm check bar** | within **1 %** of 100 mm, else fix the printer first |
| **Coupon stock** | what the coupons are printed on; how many panels | dimensionally stable stock; **20 panels** |
| **Instrument records** | for every instrument: id + calibration reference | no anonymous instruments, no missing certificates |
| **Software readiness** | scan-measurement tool exists and has been dry-run; validator returns ACCEPTED; reference table committed before any capture | all four true **before** the calibrated session starts |
| **Final gate** | `python3 tools/verify_b2_setup.py --evidence reference/b2_setup.json` | prints `B2_SETUP_VERIFIED = YES` and exits 0 |

**Order matters.** Microscope readings first (blinding), then the scanner calibration and
the scans. Software must already work: discovering in the lab that a scan cannot be
processed wastes the access, and the temptation then is to improvise — which is exactly how
a *visual* criterion silently replaces the protocol's photometric one.

---

## 6. Borrowing / access plan

No web search, no assumption of availability.

| Item | Classification | Note |
|---|---|---|
| Flatbed scanner, 2400 dpi optical | **CAN BE BORROWED** | library, office, reprographics, print shop. Check optical dpi before relying on it |
| Measuring / toolmaker's microscope | **SPECIALIST LAB ACCESS** | mechanical-metrology, tool-room or QC lab. Needs an X-Y stage with readout, not a magnifier |
| Certified steel scale / glass graticule | **SPECIALIST LAB ACCESS** + **MUST HAVE CALIBRATION RECORD** | metrology lab, or a biology lab's stage micrometer if it carries a certificate |
| Calibrated digital caliper | **CAN BE BORROWED** + **MUST HAVE CALIBRATION RECORD** | any workshop; the record is the part people forget |
| USB microscope with calibration slide | **CAN BE PURCHASED CHEAPLY** | `PHASE0_REVIEW.md` §15 calls it "acceptable secondary". Only useful if it has a **measuring stage with a readout** — most do not |
| Printer at true 100 % | **CAN BE BORROWED** | verify with the check bar; never trust "fit to page" |
| Coupon and frame stock (film, acrylic, float glass) | **CAN BE PURCHASED CHEAPLY** | stability matters more than print quality |
| CMM / optical comparator | **not needed** | `P0_EXECUTION_PLAN.md` §13 already argues the caliper survey contributes only ~0.0005-0.0006 mm on a 3 mm glyph |
| M1 edge criterion | **already written** | `P0_REFERENCE_PROCEDURE.md` §4.2.3 — free, and done |
| Trained operator (M5) | **NOT SAFE TO SUBSTITUTE** | training is against a written criterion; it cannot be borrowed |
| An uncertified ruler in place of the standard | **NOT SAFE TO SUBSTITUTE** | a scale error is a common multiplicative bias on every reference value: no scatter, no failing gate, just a confident wrong answer |
| A caliper across a 3 mm glyph | **NOT SAFE TO SUBSTITUTE** | `P0_EXECUTION_PLAN.md` §2.3: never a reference |
| A second scanner in place of the microscope | **NOT SAFE TO SUBSTITUTE** | same photometric realisation; rule R2 rejects the pair |
| `panels.json` nominal heights | **NOT SAFE TO SUBSTITUTE** | explicitly prohibited (§2.2) |

**Nothing here requires purchase beyond consumables.** The two items needing lab access
usually live in the *same* metrology lab, so this is two visits.

---

## 7. The pre-capture gate

```bash
python3 tools/verify_b2_setup.py --template reference/b2_setup.json   # blank, all null
python3 tools/verify_b2_setup.py --evidence reference/b2_setup.json   # verdict
```

Output ends with exactly one line: `B2_SETUP_VERIFIED = YES` or `= NO`. Exit code 0 / 1,
or 2 if the file cannot be read. `--json-out` writes the machine-readable result.

**How it refuses to assume:**

* **63 checks** — 58 MANDATORY, 5 ADVISORY. One MANDATORY failure ⇒ `NO`.
* **Blank means NO.** `null`, `""`, `TBD`, `TODO`, `N/A`, `unknown`, `UNSPECIFIED`,
  `pending`, `-`, `?` all read as *not evidence*. (`UNSPECIFIED` is included because
  `tools/survey_frame.py` uses it as its own "not answered" default.)
* **A string is not a boolean.** `"yes"` fails a boolean check; only `true` passes.
  `frame_in_scan` and `used_for_glyph_reference` must be explicitly `false`, not absent.
* **A missing instrument or a missing calibration record is a MANDATORY failure**, never a
  silent pass.
* **"All enhancement off" must name what was disabled**, or it does not count.
* **Open decisions block.** Each of `S2_roi_rule`, `S4_platen_rule`, `S5_repeats_rule`,
  `S6_baseline_rule`, `M2_magnification_and_reading_resolution`, `M5_operator_training`,
  `C6_reference_population`, `C9_cross_check_subset`, `D1_disagreement_rule` must read
  `RESOLVED: <pointer>`. `"probably fine"` fails.
* **The four settled decisions ride along** (`M1`, `M3`, `M4`, `S3`) pre-filled, so the
  record is complete and the reader can see what a resolved entry looks like.
* **The gate is reachable.** `test_a_fully_verified_setup_returns_yes` constructs a
  hypothetical fully-equipped setup and asserts `YES`. This matters: the P7 memo caught a
  criterion that could never be satisfied, and a gate that can only ever say NO is a bug,
  not a safety feature. The test asserts nothing about what exists.
* **Advisories never block.** Coarse reading step, shared operator, missing expiry, a
  "secondary-class" microscope and real-products-as-sample are reported, not fatal.

**Today, on a blank file: 58 of 58 MANDATORY checks fail → `B2_SETUP_VERIFIED = NO`.** That
is the correct and honest answer.

---

## 8. Implementation gap before the lab visit

| # | Gap | Needed before the visit? | Action |
|---|---|---|---|
| G-1 | Pre-capture gate | yes | **done** — `tools/verify_b2_setup.py`, 47 tests |
| G-2 | Scan-measurement path (**S1**) | **yes** — without it the scans cannot become reference values | **not written, deliberately.** The route is fixed (dpi-derived pure-scale homography, zero-distortion `Camera`, no change to `p0/measure.py`), but **S2** (ROI), **S4** (platen rule) and **S6** (baseline) are still undecided, so writing it now means encoding assumptions. That is exactly what this step is forbidden to do |
| G-3 | ROI determination for scans (**S2**) | yes | decision first, then a few lines of code |
| G-4 | Lossless → 8-bit grey PNG conversion, verified (**A-02**) | yes | needs one real scan file to verify against; recorded as gate evidence |
| G-5 | Platen correction (**S4**) | yes | **EQUIPMENT-DEPENDENT** (§4). Decide from real platen readings |
| G-6 | Reference-table validator | no | **already done** (STEP 4), including M1 auditability |
| G-7 | P1-P7 analyser | no | **already done** (B1 CLOSED) |
| G-8 | `reference/` directory in the repository | no | created on first use; the gate's `--template` writes into it |

**Nothing else in the repository needs to change before the visit.** The blocking gap is
G-2/G-3/G-5, and all three are *decisions* first, code second.

---

## 9. Verdict

```
B2_PRECAPTURE_READY = NO
B2 = OPEN
```

The checklist is complete and the gate exists, but "ready to execute" is a claim about
equipment and software, and both are still missing.

**Exact remaining blockers:**

| Blocker | Class | Status |
|---|---|---|
| **B2-1** scanner reference values | equipment + software | scanner not available; the scan-measurement path (S1) is specified but unwritten because S2/S4/S6 are undecided |
| **B2-2** microscope tier | equipment + human | M1/M3/M4 frozen; **M2** (reading resolution) needs an instrument; **M5** (training) needs the instrument and a second person |
| **B2-3** availability | equipment | scanner, microscope, certified standard and calibrated caliper all unverified. The certified standard is now unconditional (S3 = NO) |
| **S2** scan ROI rule | decision | open |
| **S4** platen non-uniformity | decision, **equipment-dependent** | open; §4 |
| **S5** repeat scans | decision | open |
| **S6** baseline on a scan | decision | open; `estimate_baseline_dir` is the candidate |
| **D1** per-glyph disagreement rule | decision | open; only the aggregate 0.06 mm rule exists |
| **C6** reference population | decision | open; must be pre-declared |
| **C9** cross-check subset | decision | open; depends on **B5** |

**B2 may be closed only when the reference setup has been physically verified** — meaning
`B2_SETUP_VERIFIED = YES` on a real evidence file, `validate_reference_table.py` returning
`ACCEPTED` on a real table, and P1 computed from that table before any camera capture is
analysed.
