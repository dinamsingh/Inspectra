# Fixture flatness / out-of-plane print control — blocker B4

**What B4 is:** the mechanical guarantee that the printed surface really is in the
fiducial plane, because no software gate can check it.

**Changes nothing scientific:** no measurement algorithm, no `config/`, no P1-P7
threshold, no `k = 1.645`, no Solution Lock, no synthetic artefact, no B3 machinery.
B2, B5 and B6 untouched. **No new acceptance threshold is invented** — the acceptance
is read out of the uncertainty model that already ships (§2.4).

**Verdict: `B4_SPECIFICATION = RESOLVED`, `B4 = OPEN`** (§11). The rule, the method,
the instrument and the disposition now exist; nothing has been physically measured.

---

## 1. The exact problem

### 1.1 Five different things, routinely confused

| # | Quantity | Definition in this project | Observable from one view? |
|---|---|---|---|
| 1 | **Camera / view obliqueness** | angle between the *fiducial plane normal* and the optical axis, recovered from the homography — `p0.camera.view_tilt_deg` | **Yes.** Gated: `max_view_tilt_deg = 30.0` |
| 2 | **Panel placement tilt** | the whole assembly (backing + coupon + frame) sitting at an angle to the camera | **Yes** — it *is* quantity 1. Harmless: the homography absorbs it |
| 3 | **Local print-plane tilt** | angle between the **printed surface** at the glyph and the **fiducial plane** defined by the four markers. The scale comes from the markers, so if the ink sits on a differently-inclined plane, an in-plane length is foreshortened by `cos α` | **NO.** §1.2 |
| 4 | **Fixture flatness** | whether the backing plate and the frame are themselves flat and rigid, so that (3) is small by construction | No — a mechanical property |
| 5 | **Coupon warp / bow** | curvature of the paper itself, which produces *both* a local offset `d` and a local tilt `α` over the glyph | No |

The single hazard is **(3)**, and the reason it is a hazard is that it is
indistinguishable from (1) in a single image while having a completely different effect:
(1) is corrected exactly by the homography, (3) is not corrected at all.

### 1.2 What the software can and cannot detect — existing evidence only

`P0_EXECUTION_PLAN.md` §5.1 lists what is checkable: view obliqueness
(`max_view_tilt_deg = 30.0`), projective fit consistency
(`max_reproj_rms_px = 0.25`, `max_reproj_max_px = 0.60`), scale consistency across the
four marker groups (`max_lomo_rel_spread = 0.005`), and the **declared** fiducial
thickness over working distance (`max_thickness_over_z = 0.01`, with the height
corrected by `1 + d/Z`).

What it cannot check is quantity (3), and this is **measured, not argued**.
`P0_ASSUMPTIONS.md` **A-06** ("Status: measured, not assumed") and the five relevant
runs in `out/synthetic` — read directly from `result.json`, not re-generated:

| run | local print tilt | undeclared plane offset | true | measured | error | reproj RMS | LOMO | view tilt | status |
|---|---|---|---|---|---|---|---|---|---|
| `E_THICKNESS-declared__base` | 0° | −0.45 mm, **declared** | 3.0600 | 3.0607 | **+0.0007** | 0.057 | 0.00008 | 0.228° | MEASURED |
| `N_NONPLANAR_TILT-10__base` | **10°** | 0 | 3.0600 | 3.0144 | **−0.0456** | 0.060 | 0.00008 | 0.294° | **MEASURED** |
| `N_NONPLANAR_TILT-20__base` | **20°** | 0 | 3.0600 | 2.8753 | **−0.1847** | 0.087 | 0.00008 | 0.090° | **MEASURED** |
| `N_PLANE_OFFSET_UNDECLARED-1.5__base` | 0° | **1.50 mm** | 3.0600 | 3.0824 | **+0.0224** | 0.084 | 0.00023 | 0.324° | **MEASURED** |
| `N_PLANE_OFFSET_UNDECLARED-5.0__base` | 0° | **5.00 mm** | 3.0600 | 3.1402 | **+0.0802** | 0.074 | 0.00018 | 0.447° | **MEASURED** |

Every gate limit is passed with room to spare — reprojection RMS 0.057-0.087 against a
0.25 limit, LOMO 0.00008-0.00023 against 0.005, view tilt < 0.5° against 30 — while the
height is wrong by up to 0.18 mm. The four defective runs are labelled
`UNSAFE_UNDETECTABLE` in the suite's own safety classification, and criterion **C9**
(`out/synthetic/analysis/analysis.json`) states it in the analysis output:

> *single-view undetectable defects measured with |err| up to 0.1847 mm; these require
> fixture control, not gates*

**The finding stands, and is preserved verbatim: a single view can look geometrically
impeccable while the print sits out of plane.** Note also the first row — a *declared*
0.45 mm offset is corrected to +0.0007 mm. The problem is never the offset; it is the
offset nobody recorded.

---

## 2. Error budget from existing numbers only

### 2.1 The closed form, and that it matches the measurements

Foreshortening of an in-plane length under local tilt `α` is `h·(1 − cos α)`. Checked
against the runs above on `h = 3.06 mm`:

| α | predicted | measured in `out/synthetic` | agreement |
|---|---|---|---|
| 10° | −0.0465 mm | −0.0456 mm | 8.9 × 10⁻⁴ |
| 20° | −0.1845 mm | −0.1847 mm | 1.6 × 10⁻⁴ |

So the sensitivity can be tabulated without inventing anything:

| local tilt α | error on a 3.06 mm glyph |
|---|---|
| 1° | 0.0005 mm |
| 2° | 0.0019 mm |
| **3° (the model's own bound)** | **0.0042 mm** |
| 5° | 0.0116 mm |
| 10° | 0.0465 mm |
| 15° | 0.1043 mm |
| 20° | 0.1845 mm |

`PHASE0_REVIEW.md`'s first-order table agrees where it overlaps: local tilt 5° →
0.011 mm, local tilt 15° → 0.102 mm.

### 2.2 Thresholds that exist but are **not** flatness limits

This must be said plainly, because reusing them would be the easy mistake:

| Existing number | What it actually bounds | Usable as a flatness limit? |
|---|---|---|
| `max_view_tilt_deg = 30.0` | **view obliqueness** (quantity 1). `PHASE0_SPEC.md` line 48 and `PHASE0_VERDICTS.md` #16 both say so explicitly: the draft's 5° referred to local print tilt, the shipped gate measures something else | **No** |
| `max_thickness_over_z = 0.01` | the **declared** fiducial thickness over working distance, used to apply `1 + d/Z` | **No** — it constrains a number the operator supplies, not the real offset |
| `max_reproj_rms_px = 0.25`, `max_reproj_max_px = 0.60` | *fit* consistency. `PHASE0_REVIEW.md` F5.3 warns specifically against treating this as planarity evidence: 16 points and 8 DOF give a low residual even with real out-of-plane geometry | **No** |
| `max_lomo_rel_spread = 0.005` | *scale* consistency across marker groups; measured at 0.0002 in the defective runs | **No** |
| `≤ 0.10 mm` absolute flatness in `SOLUTION_LOCK_V2.md` §10.3 | superseded: `PHASE0_VERDICTS.md` #16 classifies it **B** and `PHASE0_REVIEW.md` calls it the wrong metric and structurally impossible with a card frame whose own thickness is 0.3-0.5 mm | **No** |

### 2.3 The one number that *is* about flatness

`config/uncertainty_model_v1.json`: **`residual_tilt_bound_deg = 3.0`**, consumed by
`p0/uncertainty.py`:

```python
tilt_bound = math.radians(float(model.get("residual_tilt_bound_deg", 0.0)))
u_tilt     = h_mean * (1.0 - math.cos(tilt_bound)) / SQRT3
```

On a 3.06 mm glyph that is `u_tilt = 0.0024 mm` (1σ), i.e. a worst case of 0.0042 mm at
exactly 3.0°. `u_tilt` is then combined in `u_common` and flows into `u_c` and hence into
every interval and every guard-band decision the pipeline has ever emitted.

**This is an input assumption, not a measurement and not a gate.** Nothing anywhere
verifies it. And it does not degrade gracefully: the measured 10° error (0.0456 mm) is
**19.2×** the `u_tilt` the model carries, so exceeding the bound does not widen the
interval — it silently invalidates it.

### 2.4 Therefore the acceptance is already fixed

`P0_EXECUTION_PLAN.md` §5.4 asks for "a numeric mechanical acceptance … **consistent
with the 3.0 deg residual bound already in the model**". Consistency leaves exactly one
value:

> **B4 acceptance:** local print-plane tilt relative to the fiducial plane, anywhere in
> the measurement window, **≤ `residual_tilt_bound_deg` = 3.0°**.

This is **not a new threshold**. It is the number the shipped budget already assumes,
promoted from a silent assumption to a checked precondition. Loosening it is not a
fixture decision — it would require editing `config/uncertainty_model_v1.json`, and
`tools/validate_flatness.py` refuses a register that states any other value.

### 2.5 Interaction with the B3 registration budget

`B3_GLYPH_ROI_MAP.md` §4 derives an ROI-centre budget of `min(0.5 w, 0.225 h)` —
0.108 mm for the worst glyph. These are independent: B3 bounds *where the scan looks*,
B4 bounds *how the surface is oriented*. A panel can satisfy B3 perfectly and still be
tilted; that is precisely the A-06 case.

---

## 3. Mechanical control strategies

All are evaluated against the frozen design: A4 coupon sheets 95 × 55 mm per panel, a
rigid flat backing ≥ 150 × 100 mm, and the fiducial frame laid on the print
(`P0_PROTOCOL.md` §0).

| Strategy | Scientific benefit | New risk | Equipment | Reversibility | Compatible with the current coupon? | Required validation |
|---|---|---|---|---|---|---|
| **Rigid flat backing** (float glass / ground plate) — already in the BOM | Defines the print plane; every other strategy assumes it | None, if the plate is genuinely flat; a bowed "rigid" plate is worse than none because it looks reassuring | plate ≥ 150 × 100 mm | fully reversible | yes — it is the documented baseline | the plate's own flatness must be verified, not assumed |
| **Flat platen / glass on top** (glass pressed over the print) | Forces the paper flat across the whole window | Extra optical surface: reflections, and a second refracting layer between ink and lens that nothing in the pipeline models | sheet glass | fully reversible | **compromises capture**, not geometry — the documented lighting setup already fights specular paths | would need its own optical study; **not recommended without one** |
| **Clamping at the perimeter** | Pulls the sheet flat; `P0_EXECUTION_PLAN.md` §13 lists clamps under PREFERRED, *"holds coupons flat instead of relying on adhesive"* | Over-clamping can **induce** local buckling between clamps — the panel can be flatter at the edges and worse at the glyph | clamps | fully reversible | yes; clamps must stay outside the 50 × 20 mm window | gap measurement **after** clamping, at the window, not before |
| **Bonded mounting** (glued flat) | `PHASE0_SPEC.md` §5 item 3 says "coupons glued flat"; removes spring-back entirely | Adhesive thickness variation becomes a local offset; a bubble is a local dome directly under a glyph; irreversible if a panel must be re-surveyed | adhesive | **irreversible** — a bonded panel cannot be re-mounted | gap measurement after cure, plus a bubble inspection |
| **Vacuum plate** | §13 lists a vacuum plate alongside clamps; uniform pull, no edge buckling | Hole pattern can dimple thin stock; needs a pump | vacuum plate + pump | fully reversible | yes | gap measurement over the window |
| **Mechanical jig** (fixes coupon *and* frame position) | Also makes the B3 registration constant instead of per-mounting | Design and build effort; a jig that is itself not flat propagates error to every panel | fabrication | reversible | needs no coupon change if it registers on the coupon outline | jig flatness verified once, then per-panel gap checks |
| **Nothing (unconstrained)** | — | This is the **stress-block condition**, not a nominal one: §4 lists "bowed (unclamped) panel" as a deliberate P6 stress case | none | — | yes | would make the gap measurement the *only* thing holding flatness |

**No strategy is selected here, and cheapness is not the criterion.** What B4 fixes is
the *acceptance and its verification*; which mechanism achieves it is a fixture decision
that depends on what can actually be borrowed, and two of the options (bonded, top
glass) carry risks that need their own study. `validate_flatness.py` records
`mounting_method` and flags `UNCONSTRAINED` and `TAPED_PERIMETER` as weak, because with
those the gap measurement is the only thing standing between a warped panel and accuracy
data.

---

## 4. Verification method

**The question: how do we know the coupon is flat enough before the camera runs?**

### 4.1 What the repository already documents

* `P0_PROTOCOL.md` §1 step 6: *"Record the flatness you can actually verify over the
  window (feeler / straight edge). A caliper survey does **not** characterise
  out-of-plane form; see A-06."* — a **straight edge and feeler gauge**, named.
* `P0_EXECUTION_PLAN.md` §13 OPTIONAL: *"Dial indicator on a surface plate — a more
  quantitative flatness check than a straight edge"* — a second, better instrument,
  named.
* A-06 itself names the qualitative frame check: *"flat backing, frame flush, visual
  rock/gap check"*.
* The calibrated caliper is REQUIRED but is explicitly **not** a form-measuring
  instrument (§1 step 6 above).

So the instruments exist in the documents. What was missing is the **link between what
they measure and what the budget bounds**: the budget speaks in degrees, a feeler gauge
reads a gap in millimetres.

### 4.2 The conversion — derived from A-05, not invented

`P0_ASSUMPTIONS.md` **A-05** models a bowed panel, to first order over a few
millimetres, as a plane that is offset and tilted. For a parabolic bow of sagitta `s`
over a straightedge span `L`, the largest local slope is `4 s / L`, so

```
max_gap_mm = tan(bound) · L / 4          bound = 3.0°
```

| Straightedge span | Gap consistent with ≤ 3.0° |
|---|---|
| 20 mm — the window's short side | **0.262 mm** ← binding |
| 50 mm — the window's long side | **0.655 mm** |
| 95 mm — the coupon's long edge | 1.245 mm |

The **short span is binding**: 0.262 mm over 20 mm is the same local tilt as 0.655 mm
over 50 mm. Both directions must therefore be checked, and
`tools/validate_flatness.py` requires both.

Two sanity notes. First, these limits are comfortably above feeler-gauge resolution, so
the acceptance is *measurable* with the documented instrument — the validator
nonetheless requires the instrument's resolution to be recorded and rejects one too
coarse to resolve the limit it is being used against. Second, a bow contributes to
**both** error terms: a 1.0 mm sagitta over the 95 mm coupon gives an offset-like term
`s/Z = 0.5 %` → 0.0153 mm on a 3.06 mm glyph (this is exactly the
`PHASE0_REVIEW.md` "carton bow 1.0 mm" row, so that row is the `d/Z` term, **not** the
tilt term) and a tilt-like term of 2.41° → 0.0027 mm. Only the second is the invisible
one.

### 4.3 What remains genuinely unverifiable today

```
B4_VERIFICATION_METHOD = RESOLVED  (straightedge + feeler over both window spans,
                                    or a dial indicator on a surface plate;
                                    plus the frame flush rock/gap check)
```

but three things cannot be established without hardware, and are recorded rather than
assumed:

1. **The backing plate's own flatness.** The register requires
   `backing_rigid_flat_verified`; nothing in the repository specifies how to verify a
   plate, and a plate's certificate is an equipment matter (B6).
2. **Whether the chosen mounting method achieves ≤ 3.0° in practice** — measurable only
   after mounting a real coupon.
3. **Local dents, creases and true continuous curvature.** A-05's own consequence line:
   *"true continuous curvature, creases and local dents are untested."* A straightedge
   spanning the window can miss a dimple narrower than the ROI. This is a residual
   limitation of the method, stated and not closed.

---

## 5. "Gate passes" is not "physically flat"

| Condition | Software can detect? | Mechanical verification required? | What happens if not verified |
|---|---|---|---|
| Camera / view obliqueness | **Yes** — `view_tilt_deg` vs `max_view_tilt_deg = 30` | no | nothing; the homography corrects it |
| Whole assembly tilted to the camera | **Yes** — same quantity | no | nothing |
| Fiducial **declared** thickness over `Z` | **Yes** — `thickness_over_z` vs 0.01, corrected by `1 + d/Z` | no, but the thickness must be *surveyed* (§1 step 3) | the correction is applied to a wrong number |
| Projective fit quality | **Yes** — reproj RMS / max | no | — but it is **not** planarity evidence (F5.3) |
| Scale consistency across markers | **Yes** — LOMO vs 0.005 | no | measured at 0.0002 even on the defective runs |
| **Local print-plane tilt (print vs fiducial plane)** | **NO** (A-06, measured) | **YES** | up to **0.1847 mm** of error with every gate green; the 3.0° `u_tilt` term becomes fiction |
| **Undeclared plane offset** between print and fiducial | **NO** (A-06, measured) | **YES** — frame flush / rock-and-gap | **+0.0802 mm** at 5 mm, all gates green |
| Coupon warp / bow | **NO** | **YES** — straightedge gap, both spans | contributes both terms; the tilt part is invisible |
| Backing plate not flat or not rigid | **NO** | **YES** | every panel inherits it; looks like a stable systematic bias |
| Clamp-induced local buckling | **NO** | **YES** — gap measured **after** clamping | a panel can be flat at its edges and bowed at the glyph |
| Local dent / crease narrower than the ROI | **NO** | **YES**, and imperfectly (§4.3 item 3) | unbounded, and not covered by the straightedge method |

One more silent path, found while auditing and now closed: `run_real_batch.py` fed the
`PLANARITY` gate's `declared_flat_surface` check from `r.get("declared_flat", True)` —
**defaulting to true**, with the scaffold also writing `True`. An operator who never
thought about flatness got a passing planarity gate. The scaffold now writes `null` and
the runner exits unless `declared_flat` is stated explicitly.

---

## 6. Failure / disposition rule

> **No guessing.** A panel becomes accuracy data only if its flatness record derives
> `PASS`. Absence of evidence is `UNVERIFIED`, which is not `PASS`.

| Situation | Derived state | Disposition |
|---|---|---|
| Straightedge gap implies tilt > 3.0° on either span | **FAIL** | Do not capture. Re-mount, then re-measure and write a **new** record; the old one is retained. If it cannot be brought within 3.0°, the panel is excluded and the exclusion is recorded before capture |
| Coupon warped or curved beyond the gap limit | **FAIL** | as above |
| Panel does not sit flat / rocks on the backing | **FAIL** | re-mount; a rocking panel is not a measurement condition |
| Frame not flush — `ROCK` or `GAP` | **FAIL** | re-seat the frame. This is the undeclared-offset case worth up to 0.08 mm |
| Clamp introduces distortion | **FAIL** if the post-clamp gap exceeds the limit | re-clamp; the measurement that counts is always **after** clamping, at the window |
| Backing not rigid, or its flatness not verified | **UNVERIFIED** | no capture on that backing until verified; this contaminates every panel, not one |
| Flatness measurement inconclusive — instrument too coarse, reading unstable, spans not both checked | **UNVERIFIED** | no capture. `INSTRUMENT_CANNOT_RESOLVE_LIMIT` exists exactly so that "I could not tell" cannot become "it was fine" |
| Record declares `PASS` but its own numbers say otherwise | `STATUS_CONTRADICTS_EVIDENCE` | the evidence decides; the declaration is rejected |
| A run cites a panel with no record | `NO_FLATNESS_RECORD_FOR_PANEL` | the run is refused |
| A run sets `declared_flat: true` while the panel is not `PASS` | `DECLARED_FLAT_WITHOUT_EVIDENCE` | the run is refused. This is the precise route by which an unverified panel would otherwise have passed the `PLANARITY` gate |

Records are append-only in spirit and in practice: a re-mount is a new record, and a
non-`PASS` panel without a disposition note raises `NO_DISPOSITION_NOTE`. Nothing is
deleted to make a register look clean.

**Deliberate exception:** the stress block *wants* a bowed, unclamped panel and a
shimmed frame (`P0_EXECUTION_PLAN.md` §4, `safety_class` `BOWED_PANEL` /
`FRAME_NOT_FLUSH`). Those panels are pre-registered as stress, contribute to **P6**
abstention safety and never to the accuracy statistics, so a `FAIL` there is the
intended condition and not a violation of this rule.

---

## 7. Pre-capture B4 checklist

Only checks the repository justifies. Fill the register as you go:
`python3 tools/validate_flatness.py --template reference/flatness_register.json`

| CHECK | HOW VERIFIED | PASS CONDITION | EVIDENCE RECORDED |
|---|---|---|---|
| Backing plate identified | read its id / mark it | a named plate, not "the table" | `backing_id` |
| Backing plate flat and rigid | straightedge across the plate; it must not flex under hand pressure | no visible light gap; no flex | `backing_rigid_flat_verified` |
| Coupon mounting method | state which mechanism holds the panel | one of `BONDED` / `CLAMPED` / `VACUUM` / `TAPED_PERIMETER` / `UNCONSTRAINED`; the last two are flagged weak | `mounting_method` |
| Instrument named and resolvable | read the gauge set / indicator | resolution finer than the limit it checks (0.262 mm on the short span) | `instrument`, `instrument_resolution_mm` |
| Gap across the **long** window span | straightedge across 50 mm, largest feeler that enters | **≤ 0.655 mm** | `straightedge_span_long_mm`, `max_gap_long_mm` |
| Gap across the **short** window span | straightedge across 20 mm | **≤ 0.262 mm** ← binding | `straightedge_span_short_mm`, `max_gap_short_mm` |
| Measured **after** clamping | repeat the two gap checks with the panel in its final state | both limits met in the final state | same fields, `measured_at` |
| Frame flush on the print | press each edge; look for rock and for a light gap | `NO_ROCK_NO_GAP` | `frame_flush_check` |
| Frame thickness surveyed | `P0_PROTOCOL.md` §1 step 3, four places | recorded in the frame certificate | `thickness_mm` in the certificate |
| Who and when | — | both present | `operator`, `measured_at` |
| Verdict | `validate_flatness.py --register <reg> --manifest <man>` | `B4_FLATNESS_VERIFIED = YES`, exit 0 | the tool's `--json-out` |
| `declared_flat` set from the record | copy the derived status into the manifest | `true` only where the panel derives `PASS` | `declared_flat` per run |

The acceptance itself needs no line in this checklist: the tool reads it from
`config/uncertainty_model_v1.json` and rejects a register that states anything else.

---

## 8. B4 versus a real package

| | **Formal P0** | **Real product** |
|---|---|---|
| Sample | flat printed coupon on a rigid plate, frame flush | pouch, carton, bottle, wrapper |
| Print plane | mechanically controlled to ≤ 3.0° local tilt and verified before capture | curved, flexible, embossed, creased; changes when touched |
| What B4 guarantees | that *this* acceptance was met on *these* panels | **nothing** |

**A clean B4 register on 20 coupons says nothing whatsoever about a curved pack.** It
establishes the opposite: that a controlled measurement required a mechanical guarantee
which a real package cannot provide. The supporting statements already in the repository:

* **A-06** — out-of-plane print is undetectable from a single view, so on a curved
  surface the error exists and is *invisible*;
* **A-05** — the tilted-plane model is first order only; *"true continuous curvature,
  creases and local dents are untested"*;
* **A-09** — the measurand is a proxy, not the statutory character height;
* `SOLUTION_LOCK_V2.md` §3 out-of-scope: *"Curved, flexible, embossed, moulded, creased
  or unknown non-planar surfaces"*; and the fixed public wording, *"The MVP targets
  controlled planar printed cartons; curved and moulded measurement is out of scope."*
* `B3_GLYPH_ROI_MAP.md` §5.1 already refuses to absorb curvature and hands it here;
  `B2_MINIMUM_SETUP.md` §0 already records that real packaged products cannot be P0
  validation data.

So any result statement must carry the coupon condition, not just the number. A curved
real pack is a **different measurement problem**, and B4 is evidence of that, not a
bridge across it.

---

## 9. Implementation

Documentation alone was not enough for one reason: the `PLANARITY` gate consumes a
boolean that defaulted to `True`. That is a silent assumption, so the minimum validator
support was added.

| File | Change |
|---|---|
| `tools/validate_flatness.py` | **new** — reads the acceptance from the uncertainty model, converts the bound to gap limits, derives `PASS` / `FAIL` / `UNVERIFIED` per panel from the evidence, cross-checks a manifest, and prints `B4_FLATNESS_VERIFIED = YES\|NO`. `--template` writes a blank register; exit 0/1/2 |
| `tools/run_real_batch.py` | scaffold writes `declared_flat: null` (was `True`) and adds `flatness_record`; the runner exits unless `declared_flat` is an explicit boolean |
| `docs/B4_FLATNESS_CONTROL.md` | **new** — this document |
| `docs/P0_EXECUTION_PLAN.md` | §5.3 / §5.4 resolved, §12 B4 row, §14 |
| `docs/P0_PROTOCOL.md` §1 step 6 | points at the acceptance and the tool (cross-reference correction) |

**Unchanged:** `p0/` (including the measurement algorithm and every gate), `config/`
(read only — the acceptance is *read* from `uncertainty_model_v1.json`, never written),
`P0_CRITERIA.md`, `SOLUTION_LOCK_V2.md`, every synthetic artefact, all B3 machinery
(`make_glyph_map.py`, `validate_roi_map.py`, `glyph_map.json`), and all six pre-existing
test files.

---

## 10. Tests

`tests/test_flatness_b4.py` — **39 tests**; suite total **261**.

* **acceptance provenance** — it equals `residual_tilt_bound_deg`; a register stating
  5.0, 10.0, 3.5 **or** a tighter 1.0 is rejected; a missing acceptance block is
  rejected; the published gap limits match `tan(bound)·L/4`;
* **physics matches the repository** — `h(1−cos α)` reproduces the measured −0.0456 mm at
  10° and −0.1847 mm at 20°; gap↔tilt conversions are inverses;
* **evidence states** — a surveyed panel can `PASS` (the rule is reachable); a blank
  template is `UNVERIFIED`, never flat; each of ten missing fields individually forces
  `UNVERIFIED`; an empty register verifies nothing; a string instead of a record is
  `UNVERIFIED`;
* **fail states** — tilt beyond the bound is `FAIL`; the **short axis** can be the
  binding one; a gap exactly at the limit passes; frame `ROCK`/`GAP` is `FAIL`;
  `NOT_CHECKED` is `UNVERIFIED`; an instrument too coarse is `UNVERIFIED`; weak mounting
  warns without blocking;
* **no self-certification** — a declared `PASS` cannot override its own measurements or
  stand in for missing evidence; an unknown status string is rejected; omitting the
  status is fine because the evidence decides;
* **manifest cross-check** — unregistered panel, non-`PASS` panel,
  `declared_flat: true` without evidence, and absent `declared_flat` are each rejected;
* **runner** — the scaffold no longer defaults to flat;
* **CLI** — template → `NO` exit 1; surveyed → `YES` exit 0; unreadable → exit 2.

Verification run alongside: `Ran 261 tests OK`; `out/synthetic/analysis/analysis.json`
re-derives **bit-identically** (`overall: PASS`); the stand-in **P1-P7 are
bit-identical**; the reference-table validator still `ACCEPTED`; the B2 setup gate still
`NO`; the B3 glyph map still re-derives to hash `db548c1f1c9441a9`, so **B3 remains
CLOSED**. No physical data was created and no capture was started.

---

## 11. Verdict

```
B4_SPECIFICATION = RESOLVED
B4 = OPEN
```

### The exact B4 rule

> Local print-plane tilt relative to the fiducial plane, anywhere in the measurement
> window, must be **≤ 3.0°** — the `residual_tilt_bound_deg` the uncertainty model
> already assumes. It is verified before capture with a straightedge and feeler (or a
> dial indicator on a surface plate) across **both** window spans, with
> `max_gap ≤ tan(3.0°)·L/4` → **0.655 mm over 50 mm** and **0.262 mm over 20 mm**, plus
> a frame flush rock-and-gap check, on a backing plate whose own flatness was verified.
> Measured **after** clamping. Evidence is recorded per panel; the derived status is
> `PASS` / `FAIL` / `UNVERIFIED`; only `PASS` may carry `declared_flat: true`; and
> loosening the acceptance requires changing the uncertainty model, not the register.

### Existing numbers used

`residual_tilt_bound_deg = 3.0`; `u_tilt = h(1−cos 3°)/√3 = 0.0024 mm` on 3.06 mm;
measured tilt errors −0.0456 mm at 10° and −0.1847 mm at 20° with reproj RMS 0.060/0.087
and LOMO 0.00008; undeclared offset errors +0.0224 mm at 1.5 mm and +0.0802 mm at 5.0 mm;
declared −0.45 mm offset corrected to +0.0007 mm; review table 0.011 mm at 5° and
0.102 mm at 15°; gate limits 30.0° / 0.25 px / 0.60 px / 0.005 / 0.01. **Nothing else.**

### What cannot currently be verified

Everything physical: no backing plate, no straightedge, no feeler gauge, no coupon, no
frame exists. Also unresolved by method rather than by equipment: local dents or creases
narrower than the ROI can escape a straightedge spanning the window (A-05's own
consequence), and how a backing plate's flatness is itself certified is an equipment
question (**B6**).

### Minimum physical setup B4 requires

1. a rigid flat backing plate ≥ 150 × 100 mm whose flatness has been verified;
2. a straightedge plus a feeler gauge set (or a dial indicator on a surface plate) able
   to resolve better than 0.262 mm;
3. one mounting mechanism from §3 that actually achieves ≤ 3.0°;
4. the fiducial frame, to perform the flush check.

Items 1, 2 and 4 are borrow-or-buy-cheap; none is a specialist instrument. That is why
`B4_SPECIFICATION` can be `RESOLVED` while `B4` stays `OPEN`: **the rule is written and
machine-checked, and nothing has been measured.** Pretending otherwise is the one
outcome this step was meant to avoid.

B2, B5 and B6 are untouched.
