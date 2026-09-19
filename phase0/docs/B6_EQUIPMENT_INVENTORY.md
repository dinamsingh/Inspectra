# Equipment inventory and access audit — blocker B6

**What B6 is:** the real-world list of physical resources the *current* protocol needs,
with an honest availability state for each, so that what must be arranged is known
before anything is attempted.

`P0_EXECUTION_PLAN.md` §12 states the requirement exactly: *"the §13 inventory completed
with real yes/no answers and substitutes agreed for anything missing"*. This document is
that inventory; `tools/validate_inventory.py` makes it machine-checkable.

**Changes nothing scientific:** no measurement algorithm, no `config/`, no P0 criterion,
no threshold, no `k = 1.645`, no Solution Lock, no synthetic artefact, no B3 or B5
machinery. B2 and B4 are not closed here.

**Verdict: `B6_SPECIFICATION = RESOLVED`, `B6 = OPEN`** (§12).

---

## 1. Master equipment list

Every physical item named by the current protocol — `P0_PROTOCOL.md` §0 (bill of
materials) and §1 step 6, `P0_EXECUTION_PLAN.md` §13, `B2_MINIMUM_SETUP.md` §1,
`B2_SETUP_VERIFICATION.md` §1-§3, `B4_FLATNESS_CONTROL.md` §4/§11. **Nothing is added
that the protocol does not ask for**, and a test guards the count.

Availability is set conservatively per §5: no item has been confirmed, so every status is
`UNKNOWN` or `ACCESS_NEEDED`.

| Item | Purpose | B2 | B4 | Capture | Calib. | Level | Current status |
|---|---|---|---|---|---|---|---|
| **Flatbed scanner** | primary reference for every measured glyph | ● | | | | MANDATORY | **ACCESS NEEDED** |
| **Certified length standard** (steel scale / glass graticule) | calibrates the scanner scale in both axes | ● | | | ● | MANDATORY | **ACCESS NEEDED** |
| **Measuring / toolmaker's microscope** | the only independent realisation of the measurand; **P1 depends on it** | ● | | | | MANDATORY (§2.1) | **ACCESS NEEDED** |
| **Calibrated digital caliper** | frame survey, the 100 mm print check, the B3 registration | ● | ● | ● | ● | MANDATORY | **ACCESS NEEDED** |
| **Straightedge** | flatness gap across both window spans | | ● | | | MANDATORY | **NOT AVAILABLE** |
| **Gap gauge** (feeler set, or dial indicator on a surface plate) | reads the straightedge gap | | ● | | | MANDATORY | **NOT AVAILABLE** |
| **Rigid flat backing plate** ≥ 150 × 100 mm | defines the flat print plane | | ● | ● | | MANDATORY | **NOT AVAILABLE** |
| **Fiducial frame stock** (polyester film / acrylic) | the four-marker frame | | | ● | ● | MANDATORY | **NOT AVAILABLE** |
| **Print stock** | coupon substrate | ● | | ● | | MANDATORY | **NOT AVAILABLE** |
| **Printer at true 100 % scale** | prints coupons and frame | ● | | ● | | MANDATORY | **ACCESS NEEDED** |
| **Two phones** with AF/AE/AWB lock, HDR off | the devices under test | | | ● | | MANDATORY ×2 | **UNKNOWN** |
| **Copy stand or tripod** | holds the camera still for a 7-frame burst | | | ● | | MANDATORY | **UNKNOWN** |
| **Diffuse lighting**, two sources ~45° | no specular path into the lens | | | ● | | MANDATORY | **UNKNOWN** |
| **Image conversion tool** → 8-bit grey PNG, no sharpening (A-02) | makes captures readable | | | ● | | MANDATORY | **UNKNOWN** |
| Second print stock | matte / semi-gloss variation block | | | ● | | PREFERRED | NOT AVAILABLE |
| Clamps / vacuum plate | holds coupons flat without adhesive | | ● | | | PREFERRED | NOT AVAILABLE |
| Crossed polarisers | glare control on glossy stock | | | ● | | PREFERRED | NOT AVAILABLE |
| Dial indicator on a surface plate | quantitative alternative to a straightedge | | ● | | | OPTIONAL | NOT AVAILABLE |
| CMM / optical comparator | frame-survey alternative | | | | ● | OPTIONAL | NOT AVAILABLE |
| RAW-capable phone | would let the RAW-vs-JPEG verdict be tested | | | ● | | OPTIONAL | UNKNOWN |

**14 mandatory item types, 20 in the catalogue. None is verified.**

Two items do *not* appear, deliberately:

* **The coupons themselves** are an *output* of the printer + print stock, tracked by
  `B2_SETUP_VERIFICATION.md` (`coupon_panels_printed`), not a separately procured item.
* **The fiducial frame** likewise: the frame stock is the item, the surveyed frame is a
  produced artefact with a certificate (`tools/survey_frame.py`).

---

## 2. Minimum versus optional

### 2.1 A — irreducibly required (the experiment cannot run at all)

Flatbed scanner · certified length standard · measuring microscope · calibrated caliper ·
print stock · printer at 100 % · two phones · copy stand · lighting · conversion tool ·
straightedge · gap gauge · backing plate · frame stock. **All 14.**

One classification is corrected rather than copied. `P0_EXECUTION_PLAN.md` §13 lists the
**microscope under PREFERRED**, while the same row says *"P1 depends on it"* and the
MISSING table says that without it *"P1 becomes uncomputable → no accuracy claim may be
made"*. Those cannot both be right. The stronger statement is binding — a pilot that
cannot make any accuracy claim has not run — so the microscope is **MANDATORY** here.
`B2_SETUP_VERIFICATION.md` and the §13 pointer already flagged this mismatch; B6 resolves
it in the only direction the evidence allows.

### 2.2 B — required only for a specific sub-step

| Item | Only needed for |
|---|---|
| Straightedge, gap gauge | **B4** flatness verification |
| Certified length standard | **B2** scanner scale calibration |
| Microscope | **B2** P1 cross-check |
| Frame stock | frame fabrication + survey (calibration) |

### 2.3 C — preferred

Second print stock, clamps or vacuum plate, crossed polarisers. Each materially
strengthens a specific block; none gates the pilot, and the tool reports them as `WARN`.

### 2.4 D — optional, and explicitly not to be bought

| Item | Why not |
|---|---|
| **CMM / optical comparator** | `P0_PROTOCOL.md` §1 already computes it: a 0.02 mm caliper survey over a ~100 mm baseline is a 0.02 % scale error = **0.0006 mm** on a 3 mm glyph, ~250× below the accuracy target. `PHASE0_VERDICTS.md` #14 downgraded the CMM requirement to optional for exactly this reason |
| **Dial indicator + surface plate** | a straightedge and feeler already resolve the 0.262 mm binding acceptance with margin (`B4_FLATNESS_CONTROL.md` §4.2) |
| **RAW-capable phone** | tests a verdict outside P1-P7 |
| **Top glass platen** | `B4_FLATNESS_CONTROL.md` §3 flags it as adding an unmodelled optical surface; not recommended without its own study |

**Nothing in the protocol requires a purchase beyond consumables.** The three specialist
items (scanner, standard, microscope) are access problems, not purchase problems.

---

## 3. Access plan

Route *classifications* only. **No claim is made that any particular institution,
library or shop holds any item** — that is external verification the inventory records
per unit, not something this document may assert.

| Item | Access classification |
|---|---|
| Flatbed scanner | `CAN_BORROW` · `COLLEGE_LAB` · `PRINT_OR_REPROGRAPHICS_SHOP` |
| Certified length standard | `SPECIALIST_METROLOGY_LAB` · **`MUST_HAVE_CALIBRATION_RECORD`** · `NO_SAFE_SUBSTITUTE` |
| Measuring microscope | `SPECIALIST_METROLOGY_LAB` · **`MUST_HAVE_CALIBRATION_RECORD`** · **`MUST_HAVE_TRAINED_OPERATOR`** · `NO_SAFE_SUBSTITUTE` |
| Calibrated caliper | `CAN_BORROW` · `COLLEGE_LAB` · **`MUST_HAVE_CALIBRATION_RECORD`** |
| Straightedge | `CAN_BORROW` · `CAN_PURCHASE_CHEAPLY` |
| Gap gauge (feeler set) | `CAN_BORROW` · `COLLEGE_LAB` · `CAN_PURCHASE_CHEAPLY` |
| Backing plate | `CAN_BORROW` · `CAN_PURCHASE_CHEAPLY` |
| Frame stock | `CAN_PURCHASE_CHEAPLY` · `PRINT_OR_REPROGRAPHICS_SHOP` |
| Print stock | `CAN_PURCHASE_CHEAPLY` · `PRINT_OR_REPROGRAPHICS_SHOP` |
| Printer at 100 % | `CAN_BORROW` · `PRINT_OR_REPROGRAPHICS_SHOP` |
| Two phones | `CAN_BORROW` |
| Copy stand | `CAN_BORROW` · `CAN_PURCHASE_CHEAPLY` |
| Lighting | `CAN_BORROW` · `CAN_PURCHASE_CHEAPLY` |
| Conversion tool | `SOFTWARE_ONLY` |

**`NO_SAFE_SUBSTITUTE`, restated from `B2_MINIMUM_SETUP.md` §6:** an uncertified ruler in
place of the length standard (a scale error is a common multiplicative bias on every
reference value — no scatter, no failing gate, just a confident wrong answer); a caliper
across a 3 mm glyph; a second scanner in place of the microscope (rule R2 rejects the
pair); `panels.json` nominal heights as ground truth.

**Documented degradation, not a substitute:** with **one phone**, `P0_EXECUTION_PLAN.md`
§13 says verdict #24 and criterion **P4** become uncomputable and the claim is per-device
only. The inventory therefore treats one phone as a **failure**, because accepting it is a
design change and must be an explicit decision rather than a silent downgrade.

**Practical bundling:** the length standard, microscope, caliper, feeler gauge and a
surface plate tend to live in the *same* mechanical-metrology environment, while the
scanner and printer live elsewhere. That is **two access visits**, not fourteen.

---

## 4. B2 / B4 overlap — the smallest sufficient set

| Item | B2 | B4 | Capture | Calibration |
|---|---|---|---|---|
| Flatbed scanner | ● | | | |
| Certified length standard | ● | | | ● |
| Measuring microscope | ● | | | |
| **Calibrated caliper** | ● | ● | ● | ● |
| Straightedge | | ● | | |
| Gap gauge | | ● | | |
| **Backing plate** | | ● | ● | |
| Frame stock | | | ● | ● |
| **Print stock / printer** | ● | | ● | |
| Phones ×2, copy stand, lighting, conversion tool | | | ● | |

**The caliper is the one genuinely shared instrument** — it serves the frame survey
(calibration), the 100 mm print check (B2 prerequisite), the B3 two-point registration and
the B4 backing-plate sanity check. One calibrated caliper covers all four.

**Where sharing must stop.** Independence forbids collapsing the reference tier:

* the **microscope may not be replaced** by the scanner or a second scan — rules R1/R2 in
  `P0_REFERENCE_PROCEDURE.md` §5 exist to prevent exactly that, because a pair in which
  both sides ran the pipeline estimator reports agreement it never tested;
* the **length standard may not be replaced** by the fiducial frame — **S3 = NO**
  (`P0_REFERENCE_PROCEDURE.md` §3.2) made the certified standard unconditional;
* the **caliper may not measure a glyph** (`P0_EXECUTION_PLAN.md` §2.3), so its sharing
  is across *jobs*, never across the measurand.

So the smallest sufficient physical set is **14 item types, of which 3 need specialist
access, 1 is shared four ways, and 6 are cheap consumables or borrowable fixtures.**

---

## 5. Current inventory — conservative by rule

```
Every item: UNKNOWN unless explicitly confirmed with evidence.
```

Nothing is inferred from context, and nothing is marked available because it is merely
obtainable. §1's status column is `UNKNOWN` / `ACCESS NEEDED` / `NOT AVAILABLE`
throughout, and `tools/validate_inventory.py` treats `UNKNOWN` and `ACCESS_NEEDED`
identically to absent.

**The packaged products are samples, not equipment.** Biscuit packs, a room freshener, a
peanut-butter jar, a creatine tub and anything similar:

* are **not** counted toward B2, B4 or B6 — the catalogue has no entry for them, and
  recording one is rejected as `UNKNOWN_ITEM_TYPE`
  (`tests/test_inventory_b6.py::TestSamplesAreNotEquipment`);
* cannot be P0 validation data at all — `B2_MINIMUM_SETUP.md` §0 and
  `B4_FLATNESS_CONTROL.md` §8: they break the frozen nominal matrix, the flatness
  requirement (A-05/A-06) and the B5 assignment;
* are genuinely useful elsewhere — answering Solution Lock gate **G0** (what the
  controlling rule means by character height) and a later realism dataset. Neither is B6.

---

## 6. Procurement / borrowing priority — by dependency

Ranked by what unblocks what, not by cost or desirability.

| Rank | Blocks | Items | Why this rank |
|---|---|---|---|
| **1** | **reference measurement (B2)** | flatbed scanner · certified length standard · measuring microscope | P1 gates every other criterion: without a reference, P2/P3/P4 have nothing to compare against and no accuracy claim is permitted at all |
| **2** | **flatness verification (B4)** | straightedge · gap gauge · backing plate | A-06 is measured: local out-of-plane print is invisible to every gate, so without these a panel may not become accuracy data |
| **3** | **controlled capture** | two phones · copy stand · lighting · print stock · printer · frame stock | the pilot cannot produce a frame without them, but they are useless before ranks 1-2 exist |
| **4** | **recording / calibration** | calibrated caliper **with its record** · conversion tool | needed for the frame survey, the 100 mm check, the B3 registration and A-02 — the caliper is rank 4 only because it is also borrowable alongside rank 1 |
| **5** | nice to have | second print stock · clamps or vacuum plate · crossed polarisers · dial indicator · CMM · RAW phone | reported, never blocking |

**Practical consequence of the ranking:** rank 1 and rank 4's caliper are the same visit;
rank 2 is cheap and can be arranged in parallel; rank 3 should not be purchased before
rank 1 access is confirmed, because a missing microscope changes what the pilot can claim
at all.

---

## 7. Evidence that makes an item "available"

No certificate format and no legal standard is invented. What is required is that the
paperwork *exists*, is *transcribed*, and names a *real object*.

| Item | Evidence required |
|---|---|
| **Every** item | `item_id` naming one physical object · `make_model` · `verified_by` · `verified_at` · `availability = AVAILABLE` · `verification_status` (how it was confirmed — physical inspection, driver/nameplate read, certificate seen) |
| Flatbed scanner | the above; **capability** (optical dpi, bit depth, enhancement off) is recorded by `verify_b2_setup.py`, not duplicated here |
| Certified length standard | the above **plus `instrument_cal_ref`**; its certificate reference, issue date, traceability wording and stated uncertainty go into the B2 evidence file |
| Measuring microscope | the above **plus `instrument_cal_ref`** and **`trained_operator`** naming who was trained against M1 and when (`P0_REFERENCE_PROCEDURE.md` §4.2.6) |
| Calibrated caliper | the above **plus `instrument_cal_ref`** (`P0_PROTOCOL.md` §0 requires a calibration record) |
| Straightedge, gap gauge | the above; the gauge's **resolution** is checked against the 0.262 mm acceptance by `validate_flatness.py` |
| Backing plate | the above; its **flatness verification** is recorded per panel by `validate_flatness.py` (`backing_rigid_flat_verified`) and cross-checked back to this inventory by `item_id` |
| Frame stock, print stock | the above; a description of what the stock actually is |
| Printer | the above; the **100 mm check-bar measurement** lives in the B2 evidence file |
| Two phones | the above, **one record per handset**; the AF/AE/AWB-lock and HDR-off capability is a capture-profile matter |
| Copy stand, lighting | the above; physical inspection is sufficient evidence |
| Conversion tool | the above, with the tool **name and version**; that its output is unsharpened is recorded in the B2 evidence file |

---

## 8. Machine-checkable inventory

**The existing B2 gate cannot do this job, and was checked before adding anything.**
`tools/verify_b2_setup.py` covers the *reference tier only* — it says so itself, and
`P0_EXECUTION_PLAN.md` §13 repeats it: *"It covers the reference tier only — it does not
verify B3-B6."* It has no notion of phones, copy stand, lighting, backing plate,
straightedge, gap gauge, frame stock, print stock or conversion-tool identity, and it
produces no aggregate equipment verdict.

So one small file was added, and it is scoped to **avoid a second source of truth**:

| File | Records |
|---|---|
| `equipment_inventory.json` (new) | does the object **exist**, is it **identified**, is its **paperwork** on hand |
| `verify_b2_setup.py` evidence | reference-tier **capability** |
| `validate_flatness.py` register | the flatness **measurements** taken with the B4 instruments |

Schema per item — exactly the fields §8 of this task asked for, and no duplicates:

```json
{
  "item_type": "FLATBED_SCANNER",     "item_id": "SCAN-LIB-01",
  "make_model": "...",                "serial": "...",
  "availability": "AVAILABLE|NOT_AVAILABLE|UNKNOWN|ACCESS_NEEDED",
  "access_route": "CAN_BORROW|COLLEGE_LAB|SPECIALIST_METROLOGY_LAB|...",
  "instrument_cal_ref": null,         "certificate_ref": null,
  "operator": null,                   "trained_operator": null,
  "verified_by": "...",               "verified_at": "...",
  "verification_status": "PHYSICALLY_INSPECTED", "notes": ""
}
```

**Cross-checks instead of duplication.** When the other files are supplied, ids must
agree: a B2 evidence `scanner.instrument_id` that differs from the inventory is
`ID_DISAGREES_WITH_B2_EVIDENCE`, and a flatness register using a backing plate that is
not a verified inventory item is `BACKING_PLATE_NOT_IN_INVENTORY`. One physical object,
one identity.

```bash
python3 tools/validate_inventory.py --template reference/equipment_inventory.json
python3 tools/validate_inventory.py --inventory reference/equipment_inventory.json \
        --b2-evidence reference/b2_setup.json \
        --flatness-register reference/flatness_register.json
```

---

## 9. The experiment start gate

```
B6_INVENTORY_VERIFIED = YES   only when every mandatory physical resource
                              is AVAILABLE with its required evidence
                        NO    on anything missing, UNKNOWN, ACCESS_NEEDED,
                              placeholder, short on quantity, or contradicting
                              another gate
```

How it refuses to assume:

* **14 mandatory item types**; one short and the answer is `NO`.
* `UNKNOWN` and `ACCESS_NEEDED` are honest, legitimate answers — and both read as `NO`.
* `AVAILABLE` **without** evidence is `EVIDENCE_INCOMPLETE`, not availability.
* Placeholders (`TBD`, `unknown`, `n/a`, `UNSPECIFIED`, blank) are not evidence.
* A missing calibration record is `NO` for the three items the documents require one for,
  and is **not** demanded for the eleven they do not.
* The same object listed twice does not fill a quantity of two
  (`DUPLICATE_ITEM_ID`) — so two phones must be two handsets.
* An item outside the catalogue is rejected, which is how a packaged product or an
  invented instrument gets refused.
* PREFERRED items `WARN`; OPTIONAL items are silent. Neither ever blocks.
* The gate is **reachable**: `test_a_complete_inventory_returns_yes` builds a
  hypothetical fully-equipped inventory and asserts `YES`, while claiming nothing about
  what exists.

**Scope, printed in the tool's own output:** a `YES` means *equipment is on hand*. It does
**not** mean B2 is closed, B4 is closed, or that anything has been validated. B2 still
needs reference values produced and P1 computed; B4 still needs panels surveyed.

---

## 10. Implementation

| File | Change |
|---|---|
| `tools/validate_inventory.py` | **new** — the catalogue (20 items, 14 mandatory), the evidence rules, the cross-checks, `--template`, and `B6_INVENTORY_VERIFIED = YES\|NO`. Exit 0/1/2 |
| `tests/test_inventory_b6.py` | **new** — 42 tests |
| `docs/B6_EQUIPMENT_INVENTORY.md` | **new** — this document |
| `docs/P0_EXECUTION_PLAN.md` | §12 B6 row, §13 pointer, §14 |

**Unchanged:** `p0/`, `config/`, `P0_CRITERIA.md`, `SOLUTION_LOCK_V2.md`, every synthetic
artefact, all B3 machinery, all B5 machinery, `verify_b2_setup.py`,
`validate_flatness.py`, `validate_reference_table.py`, and every pre-existing test file.
No new inventory system was built where one already existed (§8).

## 11. Tests

`tests/test_inventory_b6.py` — **42 tests**; suite total **352**. Covering: catalogue
provenance (every entry has a purpose and a blocker; the microscope is mandatory; two
phones; calibration records demanded exactly where documented; optional items never
mandatory; a guard on the catalogue size so it cannot quietly grow); reachability (a
complete inventory is `YES`, the blank template is `NO`, determinism, the verdict states
its own scope); *nothing is assumed* (each of the 14 mandatory items absent → `NO`;
`UNKNOWN` / `ACCESS_NEEDED` / `NOT_AVAILABLE` → `NO`; missing or invented availability
values; `AVAILABLE` minus each evidence field; six placeholder strings; missing
calibration record for each of the three items that need one, and *not* demanded where
undocumented; untrained microscope operator; one phone; the same object listed twice; an
item outside the catalogue; a non-object record); preferred and optional never blocking;
cross-checks against the B2 evidence for all five shared ids and against the flatness
register's backing plate; samples-are-not-equipment; and CLI exit codes.

## 12. Verdict

```
B6_SPECIFICATION = RESOLVED
B6 = OPEN
```

The inventory, its evidence rules, its access classification and its gate exist and are
tested. **Not one physical item has been confirmed**, so the gate returns `NO` today —
which is the correct answer, not a failure of this step.

### Exact minimum equipment list

14 mandatory item types: flatbed scanner · certified length standard · measuring
microscope · calibrated caliper · straightedge · gap gauge · rigid flat backing plate ·
fiducial frame stock · print stock · printer at true 100 % · **two** phones · copy stand ·
diffuse lighting · image conversion tool.

### What must be physically arranged

Three specialist-access items (scanner, certified standard, microscope), one shared
calibrated instrument (caliper), six cheap consumables or borrowable fixtures, two
handsets, and one piece of software. Roughly **two access visits** plus consumables — and
rank 1 before rank 3, because a missing microscope changes what the pilot can claim at
all.

### What is still not verifiable

Everything, in the sense that matters: no item has been seen, named or evidenced. Beyond
that, B6 cannot settle how a **backing plate's own flatness is certified** — the documents
name no method, so the inventory records the claim and `validate_flatness.py` requires it
per panel, but neither can conjure a plate certificate.

**Physical capture has NOT started.** No physical data exists anywhere in this repository;
the only measurement-shaped files are the synthetic suite and the clearly-labelled
stand-in fixture. B2 remains **OPEN** (no reference values), B4 remains **OPEN** (nothing
measured), B3 and B5 remain **CLOSED**, and `PHYSICAL_EXPERIMENT_READY` remains **NO**.
