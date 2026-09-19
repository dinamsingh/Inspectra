# P0-min physical experiment — execution-readiness audit and frozen plan

**Audit target:** branch `niyamdrishti-phase0` @ `a61e749`
**Scope:** turn `P0_PROTOCOL.md` into an unambiguous execution plan and decide whether
data collection may begin.  Nothing in the measurement algorithm, thresholds,
acceptance criteria, `config/`, `tests/` or the Solution Lock was changed.

**Verdict: `PHYSICAL_EXPERIMENT_READY = NO`** — six blockers, listed in §12.

Legend: **FROZEN** = fixed by this audit, execute exactly as written ·
**C** = genuinely unresolved, a value must be decided by the team, not invented here ·
**BLOCKER** = must be closed before the first capture.

---

## 1. Physical sample design — FROZEN (except §1.6)

### 1.1 Vocabulary (frozen; these words are used with no other meaning)

| Term | Definition |
|---|---|
| **panel** | One printed coupon, `P01`..`P20`, permanently marked, mounted flat on the backing plate.  A panel is never re-printed or re-mounted mid-experiment; if it is, it becomes a new panel id. |
| **glyph instance** | One printed shape at one nominal height on one panel.  The generated sheets contain 4 shapes x 5 heights x 20 panels = **400 glyph instances**. |
| **measured glyph** | The *single* glyph instance per panel that the camera measures.  The pipeline measures one glyph per run (`P0_ASSUMPTIONS.md` A-14), so only **20** of the 400 instances are ever camera-measured. |
| **frame** | One image inside a burst.  A frame is never an accuracy observation on its own. |
| **burst** | Exactly **7 frames** captured without moving panel, frame or camera. |
| **run** | One burst processed as one unit → exactly one `result.json` and one `results.csv` row.  Identified by `(panel, device, operator, repeat, condition)`. |
| **observation** | The aggregated, bias-corrected height of one run (`measurement.h_mm`).  **1 run = 1 observation.**  240 nominal observations means 240 runs, not 240 frames. |

### 1.2 Nominal matrix (frozen)

```
20 panels x 2 devices x 2 operators x 3 repeats = 240 runs = 240 observations
240 runs x 7 frames                             = 1 680 frames
```

### 1.3 Repeat = angle block (frozen, from `P0_PROTOCOL.md` §4)

| repeat | view tilt |
|---|---|
| `R1` | 0 deg |
| `R2` | 12 deg |
| `R3` | 25 deg |

Repeats are **not** independent replicates of one condition; they are the angle block.
Within-cell repeatability therefore comes from the 7-frame burst, and the
`R1/R2/R3` spread carries the angle effect.  Any analysis that treats R1..R3 as pure
replicates is wrong.

### 1.4 Stress block (frozen at 64 runs)

Eight classes x 8 runs = **64 runs = 448 frames**.  Classes, exactly as already
specified in `P0_PROTOCOL.md` §4: defocus, motion blur, specular glare on the glyph,
partially occluded marker, wrong frame serial, low-contrast print, bowed (unclamped)
panel, frame not flush (shim under one edge).  These runs carry **no accuracy
expectation**; they feed P6 only.

### 1.5 Calibration captures (frozen)

`>= 12` frame views per device per camera profile = **>= 24 images**, excluded from all
accuracy statistics.

### 1.6 Panel → measured-glyph assignment — **C / BLOCKER B5**

Only 20 glyph instances are camera-measured, so the assignment decides which heights
and shapes the accuracy statistics actually cover — including whether P2's "3 mm class"
has any data at all.  This audit does **not** choose it.

Constraint that the assignment must satisfy (frozen): the map must be written down and
committed **before the first capture**, must cover all 5 nominal heights and both shape
classes (`FLAT_TOP`, `ROUND`), and must not be changed afterwards.

---

## 2. Ground-truth procedure — partly FROZEN, see BLOCKER B2

### 2.1 Measurand correspondence (frozen)

The reference must realise the *same* measurand as the pipeline: visible printed-ink
extent perpendicular to the fitted baseline, at the **50 % linearised-luminance**
boundary (`config/measurand_policy_v1.json`, `linearization: SRGB_EOTF`,
`boundary_fraction: 0.50`).  A reference that measures anything else (nominal cap
height, a caliper reading across ink, an edge-detector maximum) is not a reference for
this experiment.

### 2.2 Prohibition on nominal artwork dimensions (frozen)

`fixtures/physical/coupons/panels.json` carries `nominal_heights_mm` **only as a print
instruction**.  Printer scaling and ink spread change the real extent, so:

* `reference_h_mm` in the run manifest must come from an instrument, never from
  `panels.json`;
* `nominal_h_mm` is recorded separately and is never substituted for
  `reference_h_mm`;
* `P0_CRITERIA.md` already lists "nominal artwork height as ground truth" as a
  prohibited response — this is the operational form of that rule.

### 2.3 Instruments (frozen roles)

| Role | Instrument | Use |
|---|---|---|
| Primary reference | flatbed scanner, 2400 dpi (94.5 px/mm), enhancement off, 8-bit grey | every measured glyph; also the pre-declared wider set if measured |
| Independent cross-check | measuring / toolmaker's microscope | `>= 15` glyphs spanning heights, shapes and fonts → **P1** |
| Scale calibration | certified steel scale or glass graticule | calibrates the scanner in both axes; non-uniformity across the platen recorded |
| Frame survey | calibrated digital caliper + certificate | frame spans, marker side, frame thickness → `tools/survey_frame.py` |
| Never a reference | caliper across a 3 mm printed glyph | cannot realise the ink-boundary measurand |

### 2.4 Recording (frozen)

One append-only `reference/reference_table.csv`, written **before** any camera capture
is processed.  The authoritative column list is **`P0_REFERENCE_PROCEDURE.md` §6** (18
fields) and is machine-checked by `tools/validate_reference_table.py`; the earlier
13-column sketch in this document is superseded by it.  The added fields carry
identity and provenance (`glyph_id`, `unit`, `instrument_cal_ref`), independence
(`measurement_procedure` ∈ `PIPELINE_ESTIMATOR_ON_SCAN` | `MANUAL_VISUAL_CROSSHAIR` |
`UNRESOLVED`) and cross-check state (`cross_check_status` ∈ `PENDING` | `AGREED` |
`DISAGREED` | `UNUSABLE`).

`method` ∈ `SCANNER_2400DPI` | `MICROSCOPE`.  Rows are never edited; a correction is a
new row that supersedes an earlier one by timestamp, and the validator reports
`SUPERSEDED_ROWS` so the supersession is visible rather than silent.

### 2.5 Estimator independence — RESOLVED; measurement implementation still **C / BLOCKER B2**

**Resolved (STEP 4, `P0_REFERENCE_PROCEDURE.md` §2, §5):** the scanner tier **may**
reuse the pipeline's own estimator (rule R1), because at 94.5 px/mm the scan is a
different sampling regime, not a different measurand definition; but the microscope tier
**must not** (rule R2) — reuse there is an `ERROR`
(`MICROSCOPE_NOT_INDEPENDENT`), and a glyph whose scanner *and* microscope rows both
reuse the estimator is also an `ERROR` (`PAIR_NOT_INDEPENDENT`).  Both rules are
enforced by `tools/validate_reference_table.py`.

The consequence is disclosed, not hidden: because the scanner tier shares the pipeline
estimator, **P2/P3/P4 are blind to estimator-definitional bias** (measured at
0.0054 mm on `RING_O` on ideal renders).  Only **P1** — the microscope cross-check —
tests the ink-boundary definition itself.  P1's stated meaning is therefore narrower
than "the reference is correct".

**Also resolved (STEP 4B):** the microscope edge criterion **M1** is frozen as symmetric
transition-band bisection — two crosshairs per edge, boundary = their midpoint — with
**M3** (baseline by stage rotation, verified at two points) and **M4** (≥ 3 independent
re-settings, `u = s/√n`) settled, an operator checklist written, and M1 compliance
machine-audited from the recorded readings (`P0_REFERENCE_PROCEDURE.md` §4.2).  It is
stated there that the microscope **cannot** reproduce the photometric 50 % rule, and that
the residual offset is exactly what P1 reports.

**And S3 is decided: NO** — the fiducial frame is **not** scanned with the coupon.
Correcting for a frame sitting one thickness above the print needs a scanner working
distance that no document provides, and a wrong guess *passes* the `PLANARITY` gate while
carrying up to 90 % of P1's Go band as scale bias (§3.2 there).  Consequences: the
certified length standard is **unconditionally required**, `P0_PROTOCOL.md` §3 step 1
stands exactly as frozen, and **S4** (platen non-uniformity) becomes the load-bearing
scanner scale term.

**Still unresolved and still B2:** there is no implemented tool that measures a scan, and
the scanner's own scale-calibration inputs do not exist in the repository
(`P0_REFERENCE_PROCEDURE.md` §3.3 S1, S2, S4-S6; §4.3 M2, M5).  Scanner image
processing was deliberately **not** written in STEP 4: with no calibration input and no
scan to validate against, a hand-rolled reader would silently substitute a *visual*
criterion for the protocol's photometric 50 % one.  What exists instead is the schema
plus a validated manual-entry path (§12 of that document).  See B2-1/B2-2/B2-3 in §12
below.

---

## 3. Camera setup — FROZEN

| Item | Setting | Recorded per run |
|---|---|---|
| Physical camera id | **pinned** to the main rear module; the profile's `physical_camera_id` must match.  Any silent switch to a macro / ultra-wide module invalidates the profile (`P0_ASSUMPTIONS.md` A-08 context, `P0_PROTOCOL.md` §2) | yes |
| Resolution | fixed per profile, no digital zoom, no crop | yes |
| Autofocus | **locked** at the working distance before the burst; never re-focused inside a burst | yes |
| Exposure / white balance | **locked** (AE-L, AWB-L) before the burst | yes |
| HDR / night / scene / beauty / "AI" enhance | **OFF** | yes, as a checklist flag |
| OIS / EIS | **off if the app allows**; if it cannot be disabled, record `ois_state = ON` or `UNKNOWN` and let the burst spread absorb it (verdict #22) | yes |
| Working distance | chosen so sampling density at the glyph is **>= 16 px/mm** (`P0_PROTOCOL.md` §4); the gate floor of 10.0 px/mm is *not* the target (A-17) | yes, measured |
| Mounting | copy stand or tripod; panel, frame and camera do not move within a burst | yes |
| Lighting | two diffuse sources ~45 deg, no specular path into the lens; crossed polarisers optional on glossy stock | yes, described |
| Backing | rigid flat plate; coupon mounted flat; fiducial frame flush on the printed surface | yes, plus the flatness check of §5 |
| Capture format | as captured, then converted to **8-bit greyscale PNG** (A-02); the exact conversion command is recorded per run and must not apply sharpening or tone mapping | yes, verbatim command |

**Measured, not assumed:** at 4000 x 3000 the pipeline costs ~1.3 s per frame, so
240 + 64 runs ≈ 0.7 h single-threaded; 12 MP PNG reading costs 1.3 s (filter 0) to
2.1 s (adaptive filter).  Runtime is **not** a blocker.

---

## 4. Capture conditions — FROZEN

| Block | Condition | Runs | Feeds |
|---|---|---|---|
| Nominal | tilt 0 / 12 / 25 deg (= `R1/R2/R3`), in-focus, diffuse light, clamped panel, frame flush | 240 | P2, P3, P4, P5, P7 |
| Stress: view tilt | beyond the nominal block (the synthetic sweep abstained at 30 deg and lost detection at 40 deg) | 8 | P6 |
| Stress: distance | working distance pushed until sampling density falls below the nominal target | 8 | P6 |
| Stress: blur | defocus | 8 | P6 |
| Stress: motion | hand-held motion during exposure | 8 | P6 |
| Stress: glare | specular highlight placed on the measured glyph | 8 | P6 |
| Stress: fiducial | one marker partially occluded; and a deliberately wrong frame serial | 8 | P6 |
| Stress: print/ink | low-contrast print | 8 | P6 |
| Stress: planarity | bowed (unclamped) panel; frame not flush (shim under one edge) | 8 | P6 |

Print/ink variation across the nominal block is carried by the coupon design itself
(4 fonts, 5 heights, the stock actually used).  **C:** the protocol's bill of materials
lists two stocks (matte / semi-gloss) but the coupon generator does not encode stock per
panel; which panels are printed on which stock must be recorded in the panel register
before printing.

---

## 5. Fixture / planar-print requirement — partly FROZEN, see BLOCKER B4

### 5.1 What software can verify (frozen)

* view obliqueness of the fiducial plane — `max_view_tilt_deg = 30.0`;
* consistency of the projective fit — `max_reproj_rms_px = 0.25`, `max_reproj_max_px = 0.60`;
* consistency of scale across the four control-point groups — `max_lomo_rel_spread = 0.005`;
* the declared fiducial thickness relative to working distance — `max_thickness_over_z = 0.01`,
  and the height is corrected by `(1 + d/Z)`.

### 5.2 What software provably cannot verify (frozen, measured)

Out-of-plane placement of the **printed surface relative to the fiducial plane**.
`P0_ASSUMPTIONS.md` A-06: an undeclared 5 mm offset and a 20 deg local print tilt were
both **measured, not abstained**, with reprojection RMS 0.09–0.12 px and LOMO 0.0002 —
every geometric gate comfortably satisfied while the error reached 0.08 mm and 0.18 mm.
No gate can be added to catch this from a single view.

### 5.3 Consequence (frozen)

Flatness is a **mechanical acceptance**, checked before capture and recorded per panel,
not a software gate.  The uncertainty model carries only a bounded residual term,
`residual_tilt_bound_deg = 3.0` (`config/uncertainty_model_v1.json`).  Every accuracy
number silently inherits whatever real tilt exceeds that bound.

### 5.4 Unresolved — **C / BLOCKER B4**

`P0_PROTOCOL.md` §1.6 currently says only "record the flatness you can actually
verify".  That is not executable.  Required before capture, and not invented here:

1. a numeric mechanical acceptance for panel + frame flatness / local tilt over the
   measurement window, consistent with the 3.0 deg residual bound already in the model;
2. the verification method and instrument (straight edge and feeler, dial indicator,
   surface plate and height gauge, …);
3. the disposition rule when a panel fails it.

---

## 6. Data collection order — FROZEN

### 6.1 Blocking and randomisation

* **Block on device.** Complete all runs for device A, then device B.  Re-locking a
  phone's camera state is the least reliable step, so it is changed as rarely as
  possible.
* **Within a device, block on operator.**  Operator effects are then estimable as the
  difference between two complete, balanced halves.
* **Within an operator, randomise panel order** using a seed written down before
  capture starts (for example `sha256("P0-pilot|<device>|<operator>")`).  This prevents
  drift in technique, lighting or panel handling from aligning with panel identity.
* **Within a panel, run `R1 → R2 → R3`** in angle order.  Angle is deliberately *not*
  randomised: re-aiming between every run would add setup variance to the angle effect.

### 6.2 Effect separation

| Effect | How it is separated |
|---|---|
| within-cell noise | spread of the 7 frames inside one burst |
| angle | `R1` vs `R2` vs `R3` within (panel, device, operator) |
| operator | balanced operator halves within each device |
| device | balanced device halves, same panels, same operators |
| panel / height / shape / font | panel is the blocking unit; the §1.6 assignment decides coverage |

### 6.3 Anti-tuning (frozen)

Nominal and stress capture happen **before** any physical result is analysed.  The
analysis script, the reference table and the panel→glyph assignment are all committed
before the first capture.  After capture, the only permitted changes are bug fixes with
a failing test; no threshold, gate, policy hash or criterion may move.

---

## 7. File naming and metadata — FROZEN

### 7.1 Capture tree (matches `tools/run_real_batch.py --scaffold`)

```
caps/
  calib/<DEVICE>/<NN>.png                      calibration views, NN = 01..
  <PANEL>/<DEVICE>/<OPERATOR>/<REPEAT>/f0.png .. f6.png
```

### 7.2 Token grammar

| Token | Grammar | Example |
|---|---|---|
| `PANEL` | `P[0-9]{2}` | `P07` |
| `DEVICE` | `[A-Z]` (profile alias, resolved by the manifest) | `A` |
| `OPERATOR` | `OP[0-9]` | `OP1` |
| `REPEAT` | `R[1-3]` for nominal, `S[0-9]{2}` for stress | `R2`, `S05` |
| burst frame | `f[0-6].png`, exactly 7 | `f3.png` |
| `run_id` | `<PANEL>-<DEVICE>-<OPERATOR>-<REPEAT>` | `P07-A-OP1-R2` |
| stress `run_id` | `<PANEL>-<DEVICE>-<OPERATOR>-<CLASS>-<SNN>` | `P07-A-OP1-GLARE-S03` |

Stress classes (fixed vocabulary): `DEFOCUS`, `MOTION`, `GLARE`, `MARKER_OCCLUDED`,
`WRONG_FRAME`, `LOW_CONTRAST`, `BOWED_PANEL`, `FRAME_NOT_FLUSH`, `DISTANCE`, `TILT`.

### 7.3 Per-run metadata (manifest fields; the first five are required by the tool)

`run_id`, `frames`, `roi_mm`, `shape_class`, `device` — plus
`panel_id`, `operator`, `repeat`, `glyph_label`, `nominal_h_mm`, `reference_h_mm`,
`reference_method`, `angle_deg`, `declared_flat`, `safety_class`, `threshold_mm`,
`camera_identity_match`, `frame_serial_match`, `frame_not_expired`.

Recorded alongside, in a capture log: working distance, ois_state, lighting, stock,
conversion command, flatness check result, timestamp, anomalies.

### 7.4 Unresolved — **C**

`threshold_mm` has no defined value for the pilot.  P1–P7 do not use the decision
states, so it is harmless, but it must be set to a single documented placeholder for all
runs rather than varied per run.

---

## 8. Blinding / anti-bias controls — FROZEN

| Control | Rule |
|---|---|
| Operator blinding | The capturing operator must **not** know `reference_h_mm` for the glyph being captured, and must not have access to the reference table during capture. |
| Order blinding | The randomised panel order is generated from a written-down seed; the operator receives a worklist, not a rationale. |
| Analysis pre-commitment | The P1–P7 analysis script is written, committed and exercised on stand-in data **before** real captures exist.  It is not written after seeing results. |
| Sealed reference | The reference table is append-only and time-stamped, so a later edit is visible in the history. |
| No silent discards | Every attempted run gets a row, including failures (§9).  A run may never disappear; abstentions and setup failures are reported alongside accuracy, never subtracted from the denominator (`P0_CRITERIA.md` reporting rule). |
| No post-hoc tuning | Gate limits, policy hashes, the uncertainty model and the criteria are frozen at capture time.  A change after capture invalidates the dataset and requires re-capture. |
| Cross-check independence | Whoever performs the microscope cross-check should not be the person who produced the scanner numbers for those same glyphs.  Formalised as **rule R6** in `P0_REFERENCE_PROCEDURE.md` §5 and reported by `tools/validate_reference_table.py` as `SAME_OPERATOR_BOTH_METHODS` (a `WARN`, because this clause is a *should*).  The microscope operator must also not hold any phone-derived height for those glyphs; the mitigation is to take the microscope readings first, blind. |

---

## 9. Failure handling — FROZEN

Every case gets a `capture_log` row with `disposition` and `reason`.

| Situation | Disposition | Retake? |
|---|---|---|
| Setup fault noticed **before** the burst (wrong panel, unlocked AF, frame not seated, light moved) | `VOID_SETUP` | **Yes** — retake under the same `run_id`; log the void |
| Hardware fault during the burst (phone re-focused, app crashed, panel moved, < 7 frames) | `VOID_HARDWARE` | **Yes** — retake, log the void |
| Corrupted / unreadable file, wrong frame count, failed conversion | `VOID_FILE` | **Yes** — re-convert from the original if it survives, else retake |
| Missing mandatory metadata that cannot be reconstructed | `VOID_METADATA` | **Yes** — retake; the run may not be analysed without it |
| Damaged panel (creased, scratched over the glyph, delaminated) | `PANEL_RETIRED` | **No** — the panel is retired, all its existing runs stay in the dataset, and no replacement panel inherits its id |
| Pipeline **abstained** (any `PHYSICAL_SIZE_NOT_ESTABLISHED_*`) | `ABSTAINED` | **No.**  This is data, not a failure.  It feeds P5 (nominal) or P6 (stress) |
| Fiducial detection failed | `ABSTAINED` (`FIDUCIAL` stage) | **No** |
| Measured, but the operator dislikes the number | — | **Never.**  There is no disposition for this |

Hard rule: a retake is allowed only for faults that are **independent of the
measurement outcome** — i.e. identified from the setup or the file, never from the
computed height.  Any retake decided after seeing a height invalidates the cell.

---

## 10. Acceptance calculation — mapping frozen, implemented by `tools/analyse_physical.py`

Thresholds are quoted from `P0_CRITERIA.md` and are **not** restated as new criteria.

| Criterion | Input quantities | Computation | Population |
|---|---|---|---|
| **P1** reference cross-method agreement | `reference_h_mm` from `SCANNER_2400DPI` and from `MICROSCOPE` for the same glyph | mean absolute difference | `>= 15` cross-checked glyphs |
| **P2** residual SD after one global bias correction | `h_mm`, `reference_h_mm` | subtract a single global bias estimated over all nominal observations, then SD of the residuals | nominal observations of the 3 mm class |
| **P3** repeatability SD | `h_mm` within (panel, device, operator) | SD across repeats within the cell; report the burst `burst_sd_mm` separately, they are different quantities | all nominal cells |
| **P4** inter-device bias after global correction | residuals from P2 grouped by `device` | difference of device means | all nominal observations |
| **P5** gate acceptance in nominal conditions | `status` | fraction `MEASURED` of all attempted nominal runs, `VOID_*` excluded and reported separately | 240 nominal runs |
| **P6** unsafe-condition acceptance | `status` in the stress block | fraction `MEASURED` among stress runs | 64 stress runs |
| **P7** empirical interval coverage | `lower_mm`, `upper_mm`, `reference_h_mm` | fraction with `lower <= reference <= upper`, with a confidence interval; `covered` is already computed per row | nominal observations |

Reporting rule (already in `P0_CRITERIA.md`, restated because it is an execution step):
accuracy and abstention are always reported together; an accuracy figure computed only
over `MEASURED` runs without the abstention rate is not a result.

**Implementation:** `tools/analyse_physical.py` computes this table.  It parses the
thresholds out of `P0_CRITERIA.md` at run time, so that document remains the only place
a physical limit is written down, and it takes its populations from
`manifest_used.json` so it cannot select on measured values.  `tools/analyse_results.py`
now routes any `PHYSICAL_PILOT` / `source=real` dataset to it instead of silently
scoring physical rows against the synthetic C-criteria.

Each criterion reports its statistic, its denominator, the frozen band it was compared
against, and one of `PASS` / `CONDITIONAL` / `FAIL` / `UNCOMPUTABLE`.  `UNCOMPUTABLE` is
never a pass, and missing physical fields are never zero-filled.

**P7 is not decidable from the frozen documents** and is therefore reported
`UNCOMPUTABLE` with its statistic attached; see B1 in §12 for the exact decision that is
missing.

---

## 11. Stop conditions — FROZEN (thresholds unchanged, quoted from `P0_CRITERIA.md`)

| Situation | Action |
|---|---|
| All P-criteria in their **Go** band | Continue; the pilot supports proceeding to the sealed design |
| A criterion lands in its **Conditional** band | Continue, but the claim narrows exactly as `P0_CRITERIA.md` states (per device, per font class, wider interval, higher abstention).  Do not widen a gate to move it back into Go |
| **P1 no-go** (cross-method > 0.06 mm) | **Stop.**  There is no usable ground truth; no accuracy claim of any kind may be made, and the remaining analysis is uninterpretable |
| **P2 or P6 no-go** | The measurement claim is downgraded; the Android measurement feature stays blocked |
| **P5 no-go** (< 0.50 acceptance) | Stop capturing.  The capture protocol or fixture is redesigned; thresholds are not touched |
| **P7 cannot be achieved** | Report an engineering band, not a confidence interval; `k` stays uncalibrated |
| A subset is invalidated (a condition mis-executed, metadata lost, tuning suspicion) | Repeat that subset only, with the invalidation and its reason recorded; never silently replace rows |
| A gate limit, policy hash, uncertainty model or criterion changes after capture | The whole dataset is invalidated and must be re-captured |

---

## 12. Readiness blockers

| # | BLOCKER | WHY IT MATTERS | REQUIRED BEFORE DATA COLLECTION |
|---|---|---|---|
| **B1** | **CLOSED (STEP 3C).**  `tools/analyse_physical.py` computes P1-P6 from the frozen bands, `analyse_results.py` routes physical datasets to it (the old all-`nan` / misleading `OVERALL: FAIL` behaviour is gone), and **P7 was frozen as reporting/calibration only (Option C)** in `P0_CRITERIA.md` and `P7_DECISION_MEMO.md` §9: it reports observed coverage, its Wilson 95 % CI, `n` and interval width with status `REPORT_ONLY`, and can never emit a pass/fail accuracy verdict.  The accuracy gates are P1-P6.  Tests: 68 total (39 unchanged + 29 physical). | The pilot's accuracy acceptance is now fully computable and pre-registered before any capture | Done.  Residual, stated in the memo: the pilot carries no pass/fail check on interval calibration, so any claim must note the guard band rests on an unvalidated `k = 1.645` until a later calibration stage |
| **B2** | **PARTLY CLOSED (STEP 4 + 4B) — still NOT CLOSED overall.  Every *human decision* inside B2 that can be made without equipment is now made.**  Closed in STEP 4: the reference procedure (`P0_REFERENCE_PROCEDURE.md`), estimator independence (scanner may reuse the pipeline estimator, microscope may not — R1/R2), the 18-field schema, and `tools/validate_reference_table.py`.  Closed in STEP 4B: **M1** frozen as symmetric transition-band bisection with M3/M4 settled and an operator checklist (§4.2), **S3 = NO** (§3.2), and **R6** observer independence reported.  47 tests.  What P1 does and does not test is stated: P2/P3/P4 are blind to the 0.0054 mm estimator-definitional bias; only P1 tests the ink-boundary definition, and even then it bounds *realisation disagreement*, not correctness.  **Open: B2-1** no scanner reference *value* can be produced — route now fully specified (dpi-derived pure-scale homography, no measurement-code change) but unimplemented, with S4 promoted to the load-bearing scale term; **B2-2** reduced to **M2** (magnification / reading resolution) and **M5** (operator training), both requiring an instrument; **B2-3** microscope / graticule availability unverified, and the graticule is now unconditionally required | P1 gates everything else.  A reference that is undefined, or that shares the pipeline's systematic error, cannot validate it | B2-1: write the scan-measurement path, decide S4/S5/S6.  B2-2: choose M2 once an instrument is identified, then train against M1 (M5).  B2-3: a named, calibrated instrument confirmed on hand.  Scanner image processing was deliberately not guessed |
| **B3** | **`roi_mm` cannot be determined for a real capture.**  It is a required manifest field expressed in fiducial-plane millimetres, but there is no overlay renderer, no ROI picker, and `panels.json` carries no glyph coordinates | Without it no physical run can be processed at all; guessing it silently measures the wrong region | One of: mechanical registration of coupon to frame plus exported glyph coordinates, or an ROI-selection path.  Decision is the team's; this audit does not choose |
| **B4** | **Mechanical flatness acceptance is not quantified.**  A-06 proves out-of-plane print is undetectable in software, yet `P0_PROTOCOL.md` §1.6 only says "record the flatness you can actually verify", and `residual_tilt_bound_deg = 3.0` has no fixture specification behind it | Every accuracy number inherits uncontrolled out-of-plane bias.  A 20 deg local tilt produced 0.18 mm of error with all gates passing | A numeric flatness / local-tilt acceptance over the measurement window, its verification instrument and method, and the disposition rule on failure |
| **B5** | **Panel → measured-glyph assignment is not pre-registered.**  Only 20 of 400 glyph instances are camera-measured, and which ones decides whether P2's 3 mm class has data | Choosing after capture is post-hoc selection; choosing badly leaves a criterion uncomputable | A committed map covering all 5 heights and both shape classes, fixed before the first capture |
| **B6** | **Equipment availability is unverified.**  Needed but not confirmed to exist: 2400 dpi scanner, measuring microscope, certified scale or graticule, calibrated caliper with certificate, two phones with manual camera control (AF/AE/AWB lock, HDR off, OIS off), copy stand, dimensionally stable print stock, flat rigid backing, image conversion tool | The protocol silently assumes all of it.  A missing item changes the design, not just the schedule | The §13 inventory completed with real yes/no answers and substitutes agreed for anything missing |

Closed by measurement during this audit, therefore **not** blockers: runtime
(~1.3 s per frame at 12 MP, whole pilot ≈ 0.7 h single-threaded), 12 MP PNG reading
(1.3–2.1 s), capture directory schema (`--scaffold` already matches §7), and
determinism (verified in the step-1 audit).

---

## 13. Equipment inventory — to be completed before capture

Nothing here is assumed to exist.  Fill in the right-hand column with a real answer.

**For the reference (B2) subset of this inventory only**, see
`B2_MINIMUM_SETUP.md`: it reduces B2 to scanner + certified length standard +
microscope (plus printed coupons), assigns ACCEPTABLE / CONDITIONALLY ACCEPTABLE /
NOT ACCEPTABLE to every candidate substitute using only the existing documents, and
gives the borrowing plan.  It changes no criterion, threshold or spec in this document;
it is a scoping and feasibility read of what is already here.  Note one emphasis
mismatch it flags: the measuring microscope is listed under PREFERRED below, while the
same row and the MISSING table state that **P1 — and therefore every accuracy claim —
depends on it**.  The stronger statement is the binding one.

### REQUIRED — the experiment cannot run without these

| Item | Spec | Have it? |
|---|---|---|
| Flatbed scanner | 2400 dpi optical, enhancement off, 8-bit grey output | |
| Certified length standard | steel scale or glass graticule with a calibration certificate | |
| Calibrated digital caliper | 0.01 mm resolution, with certificate | |
| Fiducial frame stock | dimensionally stable: polyester film, or film label on rigid board / acrylic | |
| Rigid flat backing plate | float glass or ground plate, `>= 150 x 100 mm` | |
| Two phones | manual/pro camera control: AF lock, AE lock, AWB lock, HDR off | |
| Copy stand or tripod | holds the camera steady for a 7-frame burst | |
| Diffuse lighting | two sources, ~45 deg, no specular path | |
| Image conversion tool | JPEG/DNG → 8-bit greyscale PNG with no sharpening (A-02) | |
| Printer at true 100 % scale | verified against the frame's 100 mm check bar | |

### PREFERRED — materially strengthens the result

| Item | Why | Have it? |
|---|---|---|
| Measuring / toolmaker's microscope | the only independent realisation of the measurand; **P1 depends on it** | |
| Second print stock | matte and semi-gloss, for the print/ink variation block | |
| Crossed polarisers | glare control on glossy stock | |
| Clamps / vacuum plate | holds coupons flat instead of relying on adhesive | |

### OPTIONAL

| Item | Why |
|---|---|
| CMM or optical comparator | `P0_ASSUMPTIONS.md` shows the caliper survey already contributes ~0.0006 mm on a 3 mm glyph, so this is a nice-to-have, not a blocker |
| Dial indicator on a surface plate | a more quantitative flatness check than a straight edge |
| Phone able to output DNG/RAW | would let verdict #24 (RAW vs JPEG) be tested |

### MISSING / NEEDS SUBSTITUTE

| Gap | Consequence | Candidate substitute (needs agreement) |
|---|---|---|
| No measuring microscope | **P1 becomes uncomputable** → by §11 no accuracy claim may be made | a second, independently calibrated optical method; or explicitly record P1 as not evaluated and drop every accuracy claim |
| OIS cannot be disabled on a device | uncontrolled per-frame optical shift | keep the device, record `ois_state`, and treat its burst spread as the honest uncertainty |
| Only one phone available | verdict #24 and criterion **P4** (inter-device bias) become uncomputable | proceed single-device and state that the claim is per-device, exactly as the P4 Conditional band already requires |
| No conversion tool without sharpening | violates A-02 and silently shifts the ink boundary | verify the tool's default pipeline, or capture in a format the reader accepts directly |

---

## 14. Verdict

```
PHYSICAL_EXPERIMENT_READY = NO
```

Blockers **B2–B6** in §12.  **B1 is CLOSED** (STEP 3C): the P1-P6 gate analyser and
the reporting-only P7 exist, are tested and are pre-registered.  **B2 is partly closed**
(STEP 4 + 4B): the reference procedure, the estimator-independence decision, the enforced
ground-truth schema, the **M1** edge criterion and the **S3 = NO** strategy all now exist
— **B2 contains no undecided procedure left that equipment-free work could settle.**  But
**B2 is not closed**: no scanner reference value can be produced (B2-1), M2/M5 need an
instrument in hand (B2-2), and availability is unverified (B2-3), so a physical run still
cannot be referenced.  B3 remains hard and untouched: without it a physical run cannot be
processed at all.  The overall verdict stays NO until B2-B6 are closed.
B4 is the one that would silently corrupt otherwise-valid numbers.

No one-page execution checklist is issued while the verdict is NO.  §1–§11 above are
frozen and remain valid once the blockers are closed; the items still open inside them
are §1.6 glyph assignment, §2.5 reference *implementation* (estimator independence, M1 and
S3 are all now resolved), §4 stock-per-panel register, §5.4 flatness acceptance, and §7.4
pilot `threshold_mm`.
