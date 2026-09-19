# Pre-registered glyph / ROI mapping — blocker B3

**What B3 is:** how the pipeline is told *which region of the capture* is the glyph
under measurement, in a way that is fixed before capture and cannot be re-chosen
afterwards.

**Changes nothing scientific:** no measurement algorithm, no `config/`, no P1-P7
threshold, no `k = 1.645`, no Solution Lock, no synthetic artefact. B2, B4, B5 and B6
are untouched. **No glyph coordinate is invented** — every coordinate is recomputed
from committed code (§2.1).

**Verdict: `B3 = CLOSED`** (§10).

---

## 1. Current-state audit (inspected, not assumed)

Paths read: `p0/measure.py`, `p0/pipeline.py`, `p0/render.py`, `p0/gates.py`,
`p0/geometry.py`, `p0/camera.py`, `tools/run_real_batch.py`,
`tools/make_coupons_svg.py`, `tools/make_configs.py`, `tools/survey_frame.py`,
`fixtures/physical/coupons/panels.json`, `config/gate_policy_v1.json`,
`config/measurand_policy_v1.json`, `config/frames/FRAME-SYN-0001.json`,
`tests/test_p0.py`, `tests/test_physical_analyzer.py`, `docs/P0_EXECUTION_PLAN.md`,
`docs/P0_PROTOCOL.md`, `docs/P0_CRITERIA.md`, `docs/P0_REFERENCE_PROCEDURE.md`,
`docs/B2_MINIMUM_SETUP.md`, `docs/B2_SETUP_VERIFICATION.md`.

| Question | Answer found in the code |
|---|---|
| What does `roi_mm` mean? | `(cx, cy, w, h)` — centre and box size. `p0/measure.py:170` states it: *"`roi_mm` = (cx, cy, w, h) in plane millimetres"* |
| Which units / which coordinate system? | **Fiducial-plane millimetres**, i.e. the frame's own plane frame, origin at the frame centre, markers at `(±40, ±22)` (`tools/make_configs.py: MARKER_CENTRES`). **Not** image pixels and **not** panel coordinates |
| Panel coordinates or image pixels? | Neither. `p0/measure.py` converts plane → pixels itself via `plane_to_distorted_px(cam, H, ...)`, where `H` comes from the detected fiducial. So the caller supplies plane mm and never touches pixels |
| Where is it consumed? | `p0/pipeline.py:process_frame` uses `roi_mm[0:2]` for `rho_at`, `z_estimate_mm`, `hull_margin_mm` and `leave_one_group_out_scale`, then passes the whole tuple to `estimate_baseline_dir`, `measure_glyph` and `clipping_stats`. `tools/run_real_batch.py:124` passes `tuple(r["roi_mm"])` straight through |
| Does a glyph coordinate list exist? | **No file existed.** But the coordinates were already *determined* by committed code — see §2.1. That is the difference between deriving and inventing |
| Does `panels.json` contain enough? | **No.** It carries only `panel_id`, `sheet`, `font`, `nominal_heights_mm` (ordered) and `shapes` (ordered), with the note *"nominal geometry only; reference measurement required"*. No coordinates. It **is** enough to select the per-panel height order, which the layout depends on |
| Does `run_real_batch.py` have an ROI mechanism? | Only `REQUIRED = ("run_id", "frames", "roi_mm", "shape_class", "device")` — presence, not correctness. **And the scaffold wrote `"roi_mm": [0.0, 0.0, 1.5, 3.2]`** together with `glyph_label: "TODO"` |
| Does the measurement code need more input? | **No.** `measure_glyph(img, cam, H, Hinv, roi_mm, shape_class, policy, ...)` is complete. B3 needs no algorithm change |

### 1.1 The real hazard, stated precisely

B3 was recorded in `P0_EXECUTION_PLAN.md` §12 as *"`roi_mm` cannot be determined"*.
Inspection shows the sharper problem: **`roi_mm` could be determined far too easily.**
The scaffold stub `[0.0, 0.0, 1.5, 3.2]` is a *plausible* box at the centre of the
frame window. Left unedited it does not crash and does not warn — it measures whatever
happens to sit at the middle of the window and reports a number. A missing field would
have been safer than a plausible default.

Everything below is built around that: the ROI must be **computed**, the placeholder
must be **rejected by name**, and any hand adjustment must be an **error**.

---

## 2. Strategy comparison

| Strategy | Reproducible | Operator dependence | Physical requirement | Software | Anti-tuning risk | Works with `p0/measure.py` |
|---|---|---|---|---|---|---|
| **A. Pre-registered panel-coordinate map + measured panel→fiducial registration** (**CHOSEN**) | **yes** — derived from committed code, hash-checked | low: two caliper readings per mounting, no judgement about the glyph | caliper (already REQUIRED) | one generator + one validator, no algorithm change | **low** — ROI is computed from identity + registration, neither of which can see a result | **yes**, unchanged `roi_mm` |
| B. Fixed mechanical registration (jig / datum marks) | yes | lowest | **a jig, plus datum features on the coupon or frame** | trivial | low | yes |
| C. Manual ROI selection (picker / overlay) | no — a second operator gets a different box | **high** | none | overlay renderer + UI, neither exists | **high**: the box is chosen while looking at the image | yes |
| D. Fiducial-relative ROI typed by hand | no | high | none | none | **high**: any number can be typed | yes |
| E. Automatic glyph detection in the capture | maybe | low | none | **a new detector = new algorithm** | medium: detector picks the "clearest" glyph | needs new code |

**Why B was rejected:** the coupon carries no datum feature the frame can register
against, and the frame carries none either (`tools/make_frame_svg.py` draws markers, a
window outline and a check bar). Adding datum marks changes the coupon artwork, and the
physical sample design is frozen (`P0_EXECUTION_PLAN.md` §1). B stays the better
long-term answer and A does not preclude it: a jig would simply make the registration
constant instead of per-mounting.

**Why C and E were rejected:** C hands the operator exactly the freedom the
pre-registration exists to remove, and E requires new measurement-side code, which this
step is forbidden to write. D is what the scaffold effectively invited.

**Why A is not merely the easiest:** it is the only option whose inputs are *already
committed artefacts*. The glyph positions come from the generator that prints the ink,
and the box size from the same function the synthetic suite already uses. A also turns
out to be **self-policing** (§5.1).

---

## 3. Pre-registration

### 3.1 The glyph map — derived, never authored

`tools/make_glyph_map.py` → `fixtures/physical/coupons/glyph_map.json`
(**400 glyphs, 20 panels, `map_hash db548c1f1c9441a9…`**).

Two committed sources, composed:

* **positions** from `tools/make_coupons_svg.py`, replaying `coupon()`'s own stepping —
  first row at `y = 14.0`, row pitch `max(h × 1.9, 7.0)`, first column at `x = 8.0`,
  column pitch `max(1.2 h, 4.0) + 2.0` — with each panel's own height order taken from
  `panels.json` (the generator staggers it, and the pitch depends on the order);
* **box size** from `p0.render.glyph_bbox_mm`, which is the same function
  `tests/test_p0.py` uses to build `roi_mm`
  (`roi = glyph_center_mm + glyph_bbox_mm`).

That those two agree is not assumed — it is asserted by
`test_roi_size_equals_the_repository_bbox_function` and
`test_layout_matches_the_coupon_generator_stepping`, and checked shape by shape:
`BAR_I` `0.18 h`, `H`/`T` `0.80 h`, `RING_O` `0.70 h` outer width in both sources.

Each entry carries exactly what §3 of this task requires:

| Field | Meaning |
|---|---|
| `glyph_key` | `panel:shape:nominal(2dp):index`, e.g. `P01:BAR_I:3.00:1` — **the same canonical form as the reference table** (`P0_REFERENCE_PROCEDURE.md` §6), so a glyph, its reference value and its capture share one identifier |
| `panel_id`, `sheet`, `font` | which coupon |
| `glyph_shape`, `shape_class` | `BAR_I`/`H`/`T`/`RING_O`; `FLAT_TOP`/`ROUND` from `p0.render.glyph_shape_class` — this selects the estimator branch |
| `nominal_h_mm` | the printed row. **Print instruction only**; the map repeats the prohibition against using it as a reference value |
| `glyph_index` | 1 — each (shape, height) occurs once per panel |
| `panel_x_mm`, `panel_y_mm` | glyph centre in **panel-local** mm: origin at the coupon's top-left corner, +x right, **+y down** (the SVG convention the coupon is drawn in) |
| `roi_w_mm`, `roi_h_mm` | the ROI box, nominal artwork (zero ink spread) |
| `roi_tolerance_mm` | the derived ROI-centre budget, §4 |
| `measurement_orientation` | `PERPENDICULAR_TO_FITTED_BASELINE` — the baseline itself is still fitted per frame by `p0.measure.estimate_baseline_dir`, exactly as the measurand requires. B3 does not pre-register a baseline angle |

The map is **panel-local on purpose**. Panel-local coordinates are a property of the
printing; fiducial-plane coordinates are a property of one mounting.

### 3.2 The panel → fiducial registration — measured, per mounting

Panel-local millimetres are not `roi_mm`. The transform is:

```
X = ox + px·cos θ + py·sin θ
Y = oy + px·sin θ − py·cos θ        (panel +y is DOWN, fiducial +y is UP)
```

where `(ox, oy)` is the fiducial-plane position of the coupon's top-left corner and `θ`
the angle of the coupon's top edge. Recorded per panel mounting:

```json
"registration": {
  "corner_top_left_mm":  [x, y],
  "corner_top_right_mm": [x, y],
  "u_mm": 0.02,
  "top_left_identified_by": "PANEL_LABEL_TEXT",
  "method": "CALIPER_TWO_POINT", "operator": "...", "measured_at": "..."
}
```

* **Two points, not one**, because rotation matters: a mounting rotated by `θ` displaces
  a glyph at lever arm `r` by `r·θ`, and the smallest glyph's entire budget is 0.108 mm
  (§4). Measuring both ends **derives** `θ` instead of assuming squareness.
* **The instrument is the calibrated caliper**, which is already REQUIRED
  (`P0_PROTOCOL.md` §0) and already used this way for the frame survey (§1 step 4, ten
  repeats, `u ≈ 0.02 mm`). No new equipment, no invented specification.
* **`top_left_identified_by`** is mandatory because the coupon prints its panel label at
  the top-left (`coupon()`: `panel %s | font %s` at `x0+3, y0+5`). Without recording how
  the origin corner was identified, a 180° mounting silently selects a different glyph.
* **The corner span is a free sanity check.** The measured span must equal the coupon
  edge (95.0 mm, `make_coupons_svg.COUPON`) within the glyph's ROI budget; otherwise the
  wrong corners were measured, the panel is mounted wrongly, or the print is mis-scaled.

### 3.3 `roi_mm` is computed, never typed

```bash
python3 tools/make_glyph_map.py --check fixtures/physical/coupons/glyph_map.json
python3 tools/validate_roi_map.py --manifest manifests/pilot.json --fill manifests/pilot.json
python3 tools/validate_roi_map.py --manifest manifests/pilot.json \
        --gate-policy config/gate_policy_v1.json
```

`--fill` writes `roi_mm`, plus `roi_source: "COMPUTED_FROM_GLYPH_MAP"` and the
`glyph_map_hash` that produced it. The validator then recomputes and requires an exact
match; `tools/run_real_batch.py` additionally refuses to run at all on a missing,
null or malformed `roi_mm`, or on `glyph_label: "TODO"`.

---

## 4. ROI precision — derived, not decreed

How accurately must the ROI centre be known? The answer is already in the code:

* `p0/measure.py`: scanlines sit at `±0.4 × roi_w` about the centre
  (`half_t = 0.5·w·0.80`), and each profile reaches `±0.725 × roi_h`
  (`span_n = 0.5·h·1.45`);
* `config/gate_policy_v1.json`: `min_scanline_fraction = 0.5`.

So, **perpendicular** to the baseline the profile must still contain both edges:
`0.725 h − 0.5 h = 0.225 h`. **Along** the baseline at least half the scanlines must
still land on ink, which fails once the centre error reaches half the ink width. The
binding budget is the smaller:

```
roi_tolerance_mm = min( 0.5 × roi_w ,  0.225 × roi_h )
```

| Glyph | budget |
|---|---|
| `BAR_I` @ 1.2 mm (worst on the coupon) | **0.108 mm** |
| `H` / `T` / `RING_O` @ 1.2 mm | 0.270 mm |
| any shape @ 6.0 mm | 1.350 mm |

**These are upper bounds, and the measured behaviour is stricter.** Driving the existing
pipeline on a synthetic 1.2 mm `BAR_I`:

| ROI offset | outcome |
|---|---|
| none | `MEASURED`, error −0.0023 mm |
| `Δx = +0.05`, `+0.10` mm (inside 0.108) | `MEASURED`, error ≤ 0.0030 mm |
| `Δx = +0.20` mm | abstains, gate `scanline_fraction` |
| `Δy = +0.20` mm (still inside 0.225 h) | abstains, gate `snr` |
| `Δy = +0.60`, `+2.00` mm | abstains, `SEGMENTATION_INSUFFICIENT_SCANLINES` |
| `Δx, Δy = +3.0` mm | abstains, `SEGMENTATION_NO_CONTRAST` |

So the registration must **aim at zero**, never at the bound. The uncertainty is
propagated rather than hoped for: `u_reg = u + r · (u√2 / span)` is computed at each
glyph's lever arm and compared with that glyph's budget —
`REGISTRATION_UNCERTAINTY_EXCEEDS_ROI_TOLERANCE` if it does not fit. With the documented
`u = 0.02 mm` survey it fits for **all 400 glyphs**
(`test_a_careful_caliper_survey_meets_the_smallest_budget`).

**No schema addition to `p0/` or to the result schema was needed.** The manifest gains
optional keys only — `registration`, `glyph_index`, `nominal_h_mm`, `roi_source`,
`glyph_map_hash` — and `roi_mm` keeps its meaning, its units and its 4-tuple shape.

---

## 5. Operator workflow

```
BEFORE THE SESSION
[ ] python3 tools/make_glyph_map.py --check fixtures/physical/coupons/glyph_map.json
[ ] the B5 selection (which glyphs) is committed                  <- B5, not B3

PER PANEL MOUNTING
1. IDENTIFY PANEL      read panel_id from the printed label; confirm it against the map
2. IDENTIFY GLYPH      take glyph_key from the committed selection. Never "pick one"
3. FIDUCIAL GEOMETRY   lay the frame so the target glyph sits inside the 50 x 20 mm
                       window, clear of the edges
4. ESTABLISH ROI       caliper the two coupon top-edge corners in fiducial-plane mm;
                       record them, u_mm, and how the top-left was identified.
                       Then: validate_roi_map.py --fill   (roi_mm is computed here)
5. VERIFY              validate_roi_map.py --gate-policy config/gate_policy_v1.json
                       must print VERDICT: ACCEPTED before any capture is processed
6. MEASURE             run_real_batch.py --manifest ...
7. PROVENANCE          the manifest is committed with roi_source, glyph_map_hash and
                       the registration; results carry panel_id and glyph_label
```

### 5.1 Failure cases — all map onto existing states, none onto a guess

| Situation | What happens | Mechanism |
|---|---|---|
| **Glyph not visible** in the window | caught **before capture**: `GLYPH_OUTSIDE_FRAME_WINDOW`, computed from the frame certificate's `window_mm` | `validate_roi_map.py` |
| **Glyph partly occluded** by the frame | same check; the box's half-extents, not just its centre, must clear the window | `validate_roi_map.py` |
| **Wrong glyph appears** in the ROI | `ROI_WRONG_GLYPH` if the declared centre is beyond the budget; and if it is genuinely the wrong region, the pipeline **abstains** rather than reporting a height (§4 table) | validator **and** existing gates |
| **Panel orientation wrong** | `REGISTRATION_SPAN_IMPLAUSIBLE` (wrong corners / rotated mounting) or `REGISTRATION_ORIGIN_UNIDENTIFIED` (origin corner not evidenced); a large but honest rotation is a `WARN` and is handled exactly by the transform | `validate_roi_map.py` |
| **ROI cannot be established** | there is no fallback: `MISSING_ROI` / `MISSING_REGISTRATION` / `BAD_REGISTRATION` are errors, and `run_real_batch.py` exits rather than running | validator + runner |
| **Registration too coarse for that glyph** | `REGISTRATION_UNCERTAINTY_EXCEEDS_ROI_TOLERANCE` — refused before capture instead of producing a plausible number | `validate_roi_map.py` |
| **ROI centre too near the control-point hull** | `ROI_OUTSIDE_HULL_MARGIN`, pre-checking the `min_hull_margin_mm = 8.0` gate that would otherwise abstain at analysis time | `validate_roi_map.py --gate-policy` |
| **Package curved / flexible** | **out of scope for B3, and not silently absorbed.** The P0 sample is flat printed coupons; curvature is a *fixture* property and is **blocker B4**, where `A-06` already records that out-of-plane print is undetectable from a single view (a 20° local tilt produced 0.1847 mm of error with every gate passing). Real packaged products are not P0 validation data (`B2_MINIMUM_SETUP.md` §0). B3 neither detects nor corrects curvature and does not claim to |

The last row matters: the honest answer to "what if it is curved" is *B3 cannot see
that, B4 owns it, and no ROI mechanism can substitute for fixture control*.

---

## 6. Anti-tuning

The operator cannot promote the best-looking glyph after seeing a value, because
`roi_mm` is a **pure function of two things that exist before the capture is processed**:

```
roi_mm = f( glyph_map[glyph_key] , registration(panel mounting) )
```

* the **glyph map** is committed, derived from the coupon generator, and hash-checked
  (`--check` fails on a single 0.5 mm edit: `test_cli_check_fails_on_a_tampered_map`);
* the **registration** is two caliper readings of the mounting. It contains no image, no
  height and no result;
* **neither input can encode "lowest error", "best focus", "easiest glyph", "measured
  height" or "compliance result"** — none of those quantities appears in either.

Four concrete substitution routes are closed:

| Attempted substitution | Blocked by |
|---|---|
| nudge the ROI a little — still inside the budget | **`ROI_ADJUSTED_BY_HAND`** is an *error*, not a warning. Anything other than the computed value is refused, even when it would still measure the right glyph |
| point at the neighbouring glyph | `ROI_WRONG_GLYPH` (`test_a_substituted_neighbour_glyph_is_rejected`) |
| relabel the run as a different glyph | `GLYPH_KEY_MISMATCH` / `SHAPE_CLASS_MISMATCH` / `GLYPH_NOT_IN_MAP`, and the ROI then no longer matches the registration |
| leave the scaffold stub and let it measure the window centre | `SCAFFOLD_PLACEHOLDER_ROI` by name; the scaffold now writes `null`; `run_real_batch.py` exits |
| quietly add a second run for the same cell and keep the better one | `DUPLICATE_RUN_ID` / `DUPLICATE_GLYPH_CELL` |

This composes with the existing anti-tuning controls (`P0_EXECUTION_PLAN.md` §6.3, §8):
the manifest, the glyph map and the reference table are all committed before capture.

---

## 7. Implementation

| File | Change |
|---|---|
| `tools/make_glyph_map.py` | **new** — derives the 400-glyph map; `--check` re-derives and compares |
| `tools/validate_roi_map.py` | **new** — the transform, the computed ROI, `--fill`, and 20 validation codes |
| `fixtures/physical/coupons/glyph_map.json` | **new, generated** — the committed pre-registration |
| `tools/run_real_batch.py` | scaffold emits `roi_mm: null` / `roi_source: "UNSET"` instead of a plausible stub, and adds `glyph_index`, `nominal_h_mm`, `registration`; the runner refuses a missing/malformed `roi_mm` or a `TODO` glyph label |
| `docs/P0_PROTOCOL.md` §5 | the "fill in roi_mm" comment now points at the computed route (factual cross-reference correction) |
| `docs/B3_GLYPH_ROI_MAP.md` | **new** — this document |

**Unchanged:** `p0/` (no algorithm change), `config/`, `P0_CRITERIA.md`,
`SOLUTION_LOCK_V2.md`, every synthetic artefact, the result schema, and
`p0/results.py:CSV_COLUMNS`.

---

## 8. Tests

`tests/test_glyph_roi_map.py` — **60 tests**; suite total **222**.

| Required by the task | Test |
|---|---|
| valid pre-registered ROI accepted | `test_a_computed_roi_is_accepted`, `test_fill_then_validate_is_clean` |
| wrong panel/glyph association rejected | `test_wrong_panel_glyph_association_is_rejected`, `test_unmapped_glyph_is_rejected`, `test_shape_class_mismatch_is_rejected`, `test_glyph_key_contradiction_is_rejected` |
| missing ROI rejected | `test_missing_roi_is_rejected`, `test_scaffold_placeholder_roi_is_rejected_by_name`, `test_a_scaffolded_manifest_is_rejected_until_filled` |
| coordinate / unit errors rejected | `test_unit_and_shape_errors_in_roi_are_rejected` (µm-scale values, wrong length, string, negative, zero, swapped w/h), `test_swapped_width_and_height_is_named_as_such` |
| duplicate glyph mapping rejected | `test_duplicate_run_id_is_rejected`, `test_duplicate_glyph_cell_is_rejected`, `test_a_duplicate_map_key_is_refused_outright`, `test_repeats_that_differ_are_allowed` |
| operator cannot silently substitute | `test_a_hand_nudged_roi_is_rejected_even_within_tolerance`, `test_a_substituted_neighbour_glyph_is_rejected`, `test_todo_glyph_label_is_rejected` |
| deterministic mapping | `test_committed_map_matches_a_fresh_derivation`, `test_derivation_is_stable_across_calls`, `test_validation_is_deterministic`, `test_cli_check_fails_on_a_tampered_map` |
| synthetic suite unchanged | `tests/test_p0.py` 39 tests untouched; `out/synthetic/analysis/analysis.json` re-derives bit-identically |

Beyond the minimum: map↔generator consistency, map↔`glyph_bbox_mm` consistency,
staggered-panel layout, scan-span clearance to the neighbouring row, rigid-motion
invariance of the transform, uncertainty growth with lever arm, the caliper-survey
budget across all 400 glyphs, window visibility, and the three
`TestMisplacedRoiAbstains` cases that demonstrate a misplaced ROI abstains instead of
lying.

---

## 9. Boundary with B5

> **B3 = HOW the selected glyph is located.** A committed map of all **400** glyph
> instances, a measured panel→fiducial transform, a derived ROI-centre budget, and a
> validator that refuses anything else.
>
> **B5 = WHICH exact glyphs and panels the experiment uses.** That selection is **not
> made here.**

Deliberately absent from this step: any choice of the ~20 camera-measured glyphs, any
distribution across fonts/shapes/heights, and any statement about which glyphs the P1
cross-check subset should include (`P0_REFERENCE_PROCEDURE.md` §8 leaves that open and
ties it to B5). The map covers all 400 precisely so that B5 can select from it without
the map itself encoding a preference. When B5 lands it adds a selection file listing
`glyph_key`s; every one will already resolve in this map.

`B2` also stays where it was: this document produces no reference value and does not
touch the scanner or microscope tiers.

---

## 10. Verdict

```
B3 = CLOSED
```

Against the stated closure criteria:

| Criterion | Status |
|---|---|
| ROI representation unambiguous | **yes** — `(cx, cy, w, h)` in fiducial-plane mm, units and origin documented, panel-local vs fiducial kept distinct, validated shape and sign |
| Mapping reproducible | **yes** — derived from `make_coupons_svg.py` + `p0.render.glyph_bbox_mm`, hash-checked, `--check` fails on tampering |
| Mapping pre-registered | **yes** — `glyph_map.json` is committed before capture; the manifest records the `glyph_map_hash` that produced each ROI |
| No post-hoc glyph choice possible | **yes** — ROI is computed from identity + registration; a hand nudge is an error, not a warning; the placeholder is rejected by name; duplicates are rejected |
| Current pipeline can consume it | **yes** — `roi_mm` semantics unchanged; no change to `p0/` |
| Physical failure / visibility cases explicitly handled | **yes** — §5.1, each mapped to a named error or to an existing abstention; curvature is explicitly handed to **B4** rather than absorbed |

**Remaining B3 items — none blocking.** Two are recorded as future improvements, not
gaps: a mechanical jig (strategy B) would make the registration constant rather than
per-mounting, and the registration `u_mm` is a figure the operator must actually measure
on the day — the validator refuses the run if the value recorded does not fit the glyph's
budget, so an optimistic entry cannot pass silently.

Nothing here closes B2, B4, B5 or B6, and no physical capture has started.
