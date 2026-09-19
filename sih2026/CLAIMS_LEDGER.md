# Claims ledger

Every substantive claim in the deck, its source, its status and the wording actually used.
Verified against the repository at branch `niyamdrishti-phase0` (commit `9fc9d87`) while
building the deck — not from memory.

Status vocabulary: **VALIDATED** (verifiable repository fact) · **SYNTHETIC-ONLY**
(controlled benchmark, no physical data) · **DESIGNED** (specified and frozen, not yet
executed) · **PENDING-PHYSICAL** (awaits laboratory work) · **UNSUPPORTED** (excluded).

## Quantitative claims

| # | Claim in deck | Source | Status | Wording used |
|---|---|---|---|---|
| 1 | 76 runs in the benchmark | `out/synthetic/analysis/analysis.json` → `n_rows: 76` | SYNTHETIC-ONLY | "76 runs" under the card headed *Controlled synthetic benchmark* |
| 2 | 10 of 10 criteria PASS | same file: 10 verdict entries, all `pass: true`, `overall: PASS` | SYNTHETIC-ONLY | "10 of 10 pre-registered criteria PASS" |
| 3 | max arithmetic error 0.008 mm | criterion C1: `max|err|=0.00797 mm <= 0.010` | SYNTHETIC-ONLY | "max arithmetic error 0.008 mm **on ideal renders**" |
| 4 | median burst repeatability SD 0.0025 mm | criterion C3 | SYNTHETIC-ONLY | "median burst repeatability SD 0.0025 mm" |
| 5 | 11 of 11 unsafe cases abstained | criterion C7: `abstained 11/11` | SYNTHETIC-ONLY | "11 of 11 targeted unsafe cases abstained" |
| 6 | 0 false-clear of 4 undersized; 0 false-accuse of 4 compliant | criterion C8 | SYNTHETIC-ONLY | quoted exactly, inside the benchmark card |
| 7 | measure rate 1.00 on safe conditions | criterion C11 | SYNTHETIC-ONLY | "measure rate 1.00 under safe conditions" |
| 8 | 352 automated tests | `python3 -m unittest discover -s tests` → `Ran 352 tests … OK` | VALIDATED | "352 automated tests" |
| 9 | Re-runs are bit-identical | analysis JSON re-derived identically at every step this session | VALIDATED | "re-runs are bit-identical" |
| 10 | ~1.3 s per 12 MP frame | measured in the readiness audit, recorded in `P0_EXECUTION_PLAN.md` §12 | VALIDATED (desktop, single-thread) | "about 1.3 s per 12 MP frame single-threaded" |
| 11 | 0.185 mm error with every gate green | `N_NONPLANAR_TILT-20` run: err −0.1847 mm, reproj RMS 0.087 px, LOMO 0.00008, all gates pass | SYNTHETIC-ONLY, measured | "measured 0.185 mm error with every gate green" |
| 12 | k = 1.645, not calibrated | `config/uncertainty_model_v1.json`: `k_lower/k_upper 1.645`, `calibrated: false`, `UM-v1-uncalibrated` | VALIDATED | "k = 1.645, reported as nominal and not yet calibrated" |
| 13 | 400 glyph instances, 20 panels, hash-checked | `glyph_map.json` `n_glyphs 400`, hash `db548c1f1c94…`; `glyph_selection.json` `n_panels 20`, hash `1a1b1dabea14…` | VALIDATED | "400 glyph instances … 20 panels … both derived by rule and hash-checked" |
| 14 | 2400 dpi scanner in the minimum setup | `P0_PROTOCOL.md` §0/§3, `B2_MINIMUM_SETUP.md` §1 | DESIGNED | "2400 dpi scanner, certified length standard, measuring microscope" |

## Qualitative and design claims

| # | Claim | Source | Status | Note on wording |
|---|---|---|---|---|
| 15 | Measurand is the visible printed-ink extent perpendicular to the fitted baseline | `config/measurand_policy_v1.json` | VALIDATED | stated on slide 3 **and labelled a screening proxy, not a statutory definition** (A-09) |
| 16 | Fail-closed gates: calibration, geometry, image quality, segmentation, burst, uncertainty | `p0/gates.py` `STAGES` | VALIDATED | listed, not quantified |
| 17 | Abstention returns `PHYSICAL_SIZE_NOT_ESTABLISHED` | `p0/gates.py` `ABSTAIN_PREFIX` | VALIDATED | quoted verbatim |
| 18 | P1–P7 acceptance criteria pre-registered and frozen | `P0_CRITERIA.md` | DESIGNED | "pre-registered and frozen", never "met" |
| 19 | P7 is reporting-only and can never be a pass | `P0_CRITERIA.md` P7 section | DESIGNED | "collects empirical coverage as calibration evidence and can never be shown as a validated interval" |
| 20 | Independent reference: 2400 dpi scan primary + microscope cross-check, P1 gates all | `P0_REFERENCE_PROCEDURE.md` | DESIGNED | "pre-registered", not "performed" |
| 21 | Pre-committed stop conditions | `P0_CRITERIA.md` "Hard stops" | DESIGNED | quoted, with the reason they exist |
| 22 | Curved/flexible/embossed packs out of scope | `SOLUTION_LOCK_V2.md` §3, A-05, A-06 | DESIGNED | "declared out of scope" |
| 23 | Android/Kotlin client, on-device OCR, encrypted store, versioned rule pack, canonical JSON + PDF | design documents; **not implemented** | DESIGNED | sits under the template's own heading *Technologies to be **used***, and slide 3 carries an explicit build-status line saying the Android client is the implementation target, not a finished product |
| 24 | Offline-first, no connectivity needed | design decision | DESIGNED | stated as a design property |
| 25 | Officer makes the legal determination | `SOLUTION_LOCK_V2.md` positioning | DESIGNED | repeated on slides 1, 2 and 5 |
| 26 | Impact on the officer (coverage, less re-typing, reproducible record, supervisory review) | reasoned from the design | DESIGNED | framed as "potential impact", with **no numbers** |
| 27 | Flatness must be mechanical, not gated | `B4_FLATNESS_CONTROL.md`, A-06 | DESIGNED | appears as a risk mitigation, not a capability |

## Claims deliberately NOT made

| Prohibited claim | Why it is absent |
|---|---|
| first / only / unique / best / most advanced | No evidence exists; slide 2's required "Innovation and uniqueness" pointer is answered with *what the system does*, not with a comparative superlative |
| 100 % accurate, zero false positives | The benchmark reports 0 false-clear **of 4 undersized cases in a synthetic subset** — stated with its denominator and its synthetic label |
| legally defensible, court admissible, tamper-proof | Replaced by "evidence-linked", "hash-linked", "screening assistance" |
| fully legally validated, government integrated | Absent. Slide 6 instead names the open legal-definition question |
| AI makes the final legal decision | Explicitly reversed on three slides |
| Any physical accuracy result, scanner-vs-microscope number, physical P1–P7 result, calibration certificate, real-world error percentage | None exists. Slide 3's third card says "laboratory validation pending — no physical claim is made"; slide 6 repeats it |
| Time saved, cost saved, accuracy improvement, adoption figures | Slide 5 states in-deck: "No time-saving, accuracy or cost figure is claimed: none has been measured in the field yet" |
| A specific statutory letter-height in millimetres | Not verified against the Rules to a citable clause, so the deck says "configurable threshold per rule version" instead of a number |
| Equipment availability | Deck never says any instrument is on hand; equipment access appears as a managed **risk** |

## Content excluded because evidence was unavailable

| Excluded | Reason |
|---|---|
| Real product photographs (biscuit pack, room freshener, peanut butter, creatine) | No image assets exist in the repository and none could be photographed or cropped in this environment. They are also **samples, not measurement evidence** — using them next to accuracy figures would mislead. A clean vector package illustration is used instead |
| App UI screenshots | The Android client does not exist. Rather than present a wireframe that could be mistaken for a product, the deck shows the workflow as a process diagram |
| A plotted accuracy chart | Any chart would either replot synthetic data at a size that invites misreading as physical results, or be empty |
| Physical validation timeline with dates | Depends on lab access that is not secured; a dated plan would be invented |
| Team member names and roles | Not supplied |
