# Reference (ground-truth) measurement procedure — blocker B2

**Scope:** defines how the reference values that P1 compares, and that P2/P3/P4 are
measured against, are produced. Closes the *methodological* half of B2 and states exactly
what remains.

**Changes nothing else:** no measurement algorithm, no `config/`, no P1-P7 threshold, no
Solution Lock. B3-B6 are untouched.

**Verdict: `B2 = NOT CLOSED`** — three residual blockers in §11.

---

## 1. Instrument audit

Only documented properties are listed. Anything the repository does not state is marked
**UNRESOLVED** rather than assumed.

| Instrument | What it can actually measure | Same measurand as the phone pipeline? | Documented resolution / limit | Can serve as reference? |
|---|---|---|---|---|
| **Flatbed scanner, 2400 dpi** (`P0_PROTOCOL.md` §0, §3) | a sampled greyscale image of the panel at 94.5 px/mm; a length only *after* an estimator extracts an ink boundary from it | **Yes, if and only if** the 50 % linearised-luminance estimator is run on the scan — which is what `P0_PROTOCOL.md` §3 step 3 instructs ("the same estimator") | 2400 dpi ⇒ 1 px = **0.0106 mm**. The stated reference uncertainty target is **≤ 0.01 mm**, i.e. *below one pixel*, so subpixel estimation is mandatory, not optional | **Yes — primary**, for every camera-measured glyph |
| **Measuring / toolmaker's microscope** (§0, §3) | the distance between two positions a human operator sets crosshairs to, on a magnified image | **No — a different realisation.** A human judges a *visually apparent* ink edge; that is not a 50 % crossing of a linearised luminance profile. The two coincide only approximately | **UNRESOLVED**: magnification, stage resolution, illumination mode and edge criterion are not specified anywhere in the repository | **Yes — independent cross-check only** (P1) |
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

### 3.2 UNRESOLVED — required parameters the repository does not specify

None of these may be invented; each is a decision for the project owner.

| # | Missing parameter | Why it blocks execution |
|---|---|---|
| S1 | **Which software implements "the same estimator" on a scan.** `p0.measure.measure_glyph` needs a homography and a fiducial; a flatbed scan has neither (scale comes from dpi). No tool in the repository measures a scan | Without it there is no way to produce a single scanner reference value |
| S2 | **How the glyph is located in the scan** (the ROI). There is no fiducial in a scan and no ROI-selection path | Same class of problem as B3, but for scans; not solvable here |
| S3 | **Whether the fiducial frame is scanned lying on the coupon** so the normal pipeline applies. `P0_EXECUTION_PLAN.md` §2.5 raises this as an option and does not settle it | Changes S1 and S2 entirely |
| S4 | **How platen non-uniformity is applied** — recorded per §3 step 1, but no correction rule is given | A recorded-but-unapplied correction is not a correction |
| S5 | **Repeat scans per panel**, and whether `n_repeats` aggregates repeats or repeated readings of one scan | Affects the stated `reference_u_mm` |
| S6 | **Baseline direction on a scan** — the measurand is perpendicular to the fitted baseline; how the baseline is established without the pipeline's detection step is unstated | Perpendicularity is part of the measurand |

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

### 4.2 UNRESOLVED — required parameters the repository does not specify

| # | Missing parameter |
|---|---|
| M1 | **Edge criterion**: how the operator decides where the ink boundary is (first visible tone, mid-tone, last clear paper). The pipeline's 50 % rule cannot be applied by eye, so a stated visual criterion is mandatory and absent |
| M2 | **Magnification, illumination mode and stage resolution.** Opaque coupon stock implies reflected (episcopic) illumination, but nothing states it |
| M3 | **How "perpendicular to the baseline" is realised on the stage** — stage rotation, a reference edge, or the glyph's own baseline |
| M4 | **Repeats per glyph and how `reference_u_mm` is derived** from them |
| M5 | **Operator training / inter-operator agreement** before the cross-check counts |

Until M1 is decided, a microscope row is recordable but its `measurement_procedure`
must be `UNRESOLVED`, which the validator **rejects** as a usable reference — by design.

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

R1, R2 and R4 are enforced by `tools/validate_reference_table.py` and covered by
`tests/test_reference_table.py`.

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
| `n_repeats` | yes | how many readings the value aggregates |
| `raw_readings` | yes (may be empty) | the individual readings, so the aggregate is auditable |
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
| **B2-1 Scanner reference values cannot be produced** | The scanner is the primary reference for every camera-measured glyph, so P2/P3/P4 have no `reference_h_mm` without it. `P0_PROTOCOL.md` §3 step 3 requires *the same estimator* on the scan; no tool measures a scan (S1), the ROI is undefined (S2), and whether the fiducial is scanned with the coupon is unsettled (S3) | **OPEN.** Deliberately not implemented: the documented scale-calibration inputs (S4) do not exist, no scanner or scan exists to validate against, and a manual pixel reading would silently substitute a *visual* criterion for the protocol's photometric one | Decide S1-S3 (and S4-S6). If the answer is code, it is a new tool that calls `p0.measure`; measurement code must not change. If the answer is a manual reading, the protocol's "same estimator" wording must be reconciled first |
| **B2-2 Microscope edge criterion undefined** | P1 is the *only* check on the ink-boundary definition. Without a stated visual criterion (M1) two operators measure different quantities and P1 becomes uninterpretable | **OPEN.** Schema supports the rows; `measurement_procedure=UNRESOLVED` is correctly rejected until M1 is decided | Decide M1, then M2-M5 |
| **B2-3 Instrument availability unverified** | P1 cannot be computed at all without a measuring microscope; the scanner path additionally needs a certified scale/graticule | **OPEN** — overlaps B6, but it gates P1 specifically. `P0_EXECUTION_PLAN.md` §13 already records that a missing microscope means P1 is uncomputable and therefore *no accuracy claim may be made* | Complete the §13 inventory with real answers; agree substitutes or accept the stated consequence |

**Not a B2 blocker (resolved by this document):** whether the reference may reuse the
pipeline estimator (§2, R1-R5); the record schema and its validation (§6, implemented);
how agreement is computed before phone data exists (§7, implemented); disagreement
recording (§9); traceability (§10).

**Dependency, not owned by B2:** the concrete cross-check subset (§8) needs the B5
panel→glyph assignment.

---

## 12. What was implemented

| Item | Status |
|---|---|
| `tools/validate_reference_table.py` | schema, unit, enumeration, provenance, duplicate/supersession, independence and linkage validation; reports P1 agreement by delegating to `analyse_physical.compute_p1` |
| `tests/test_reference_table.py` | 32 tests covering schema, units, required fields, duplicates, supersession, independence, disagreement recording, traceability linkage and determinism |
| Manual data-entry path | the schema in §6 is fillable by hand today; the validator gates it |
| Scanner image processing | **deliberately not implemented** — see B2-1 |

No measurement code, no `config/`, no P1-P7 threshold and no synthetic artefact was
changed.
