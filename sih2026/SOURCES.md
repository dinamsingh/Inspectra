# Sources used

## A. Official template (highest priority)

The SIH 2026 idea-submission template PDF supplied with the task. Audited for: slide count
(6 including title), mandatory section headings, the idea-detail pointers that may not be
changed, title-slide metadata fields, chrome (team oval, wordmark, footer bar with slide
number), 16:9 page size, and the instruction to submit as PDF. The template's own
"Important Instructions" slide is deleted in the final deck, exactly as that slide
instructs.

## B. Reference deck (studied for structure, nothing copied)

The SIH 2025 deck supplied (PS SIH25108, Team Hackastra). What was taken: the
**information architecture** only — bordered two-column panels, bullets left and a diagram
right, a labelled sub-heading per required pointer, dense but grouped content, and the
title-slide metadata treatment. What was deliberately **not** taken: its keyword walls, its
outlined-black box styling, its buzzword density, and any of its text, artwork or layout
assets. No content, image, illustration or branding from that deck appears here.

## C. External references cited on slide 6

Content from these was paraphrased, not reproduced. *Content was rephrased for compliance
with licensing restrictions.*

1. **Legal Metrology (Packaged Commodities) Rules, 2011** — mandatory declarations on
   pre-packaged commodities, and their size and legibility.
   Department of Consumer Affairs — [consumeraffairs.nic.in](https://consumeraffairs.nic.in)
2. **Legal Metrology Act, 2009** — the enabling statute.
   [consumeraffairs.nic.in](https://consumeraffairs.nic.in)
3. **Consolidated Rules text** used while building the rule model — the 2011 Rules with
   amendments, as hosted for public reference:
   [bombayhighcourt.gov.in/bhc/libweb/legislation/rulec/LegalMetrologyPackagedCommoditiesRules,2011.pdf](https://bombayhighcourt.gov.in/bhc/libweb/legislation/rulec/LegalMetrologyPackagedCommoditiesRules,2011.pdf)
4. **OIML R 79 — Labelling requirements for prepackaged products** — international
   reference for declaration and legibility requirements.
   [oiml.org/en/publications](https://www.oiml.org/en/publications)
5. **JCGM 100:2008 (GUM), Evaluation of measurement data** — the method behind the
   component uncertainty budget and the coverage factor. [bipm.org](https://www.bipm.org)
6. **Problem statement SIH26034** — Ministry of Consumer Affairs, Food & Public
   Distribution, Department of Consumer Affairs. [sih.gov.in](https://sih.gov.in)

## D. Web research used only to check presentation expectations

Two searches were run, to confirm the template rules rather than to source content.
The results corroborated the template: **six slides maximum, points and diagrams rather
than paragraphs, do not alter the template layout, submit as PDF.**

- [SIH PPT round guide (secondary summary of the submission rules)](https://www.scribd.com/document/899483721/Smart-India-Hackathon-SIH-PPT-Round-a-Complete-Guide-1)
- [SIH 2026 presentation template overview](https://thenewviews.com/sih-2025-ppt-template/)
- A search for the statutory letter-height requirement returned mostly non-Indian sources
  (US 16 CFR §500.21, OIML drafts), so **no millimetre figure was taken from the web** and
  the deck says "configurable threshold per rule version" instead.

*Content was rephrased for compliance with licensing restrictions.*

## E. Project / repository sources (verified at commit `9fc9d87`)

| Path | Used for |
|---|---|
| `phase0/out/synthetic/analysis/analysis.json` | every synthetic figure: `n_rows`, `overall`, criteria C1–C11 detail strings |
| `phase0/out/synthetic/runs/N_NONPLANAR_TILT-20__base/result.json` | the 0.185 mm out-of-plane figure with its gate readings |
| `phase0/config/measurand_policy_v1.json` | the measurand definition and boundary fraction |
| `phase0/config/uncertainty_model_v1.json` | `k = 1.645`, `calibrated: false` |
| `phase0/config/gate_policy_v1.json` | gate names and limits |
| `phase0/p0/gates.py` | gate stage list, `PHYSICAL_SIZE_NOT_ESTABLISHED` prefix |
| `phase0/docs/P0_CRITERIA.md` | P1–P7 bands, P7 reporting-only status, hard stops, prohibited responses |
| `phase0/docs/P0_PROTOCOL.md` | bill of materials, capture protocol, reference measurement |
| `phase0/docs/P0_EXECUTION_PLAN.md` | frozen matrix, runtime measurement, §13 equipment inventory, blocker table |
| `phase0/docs/P0_ASSUMPTIONS.md` | A-02, A-05, A-06, A-07, A-09, A-14 |
| `phase0/docs/P0_REFERENCE_PROCEDURE.md` | independent reference method, M1, S3, independence rules |
| `phase0/docs/B2_MINIMUM_SETUP.md`, `B2_SETUP_VERIFICATION.md` | minimum equipment set, readiness gates |
| `phase0/docs/B3_GLYPH_ROI_MAP.md`, `B4_FLATNESS_CONTROL.md`, `B5_GLYPH_SELECTION.md`, `B6_EQUIPMENT_INVENTORY.md` | pre-registered coverage, flatness acceptance, selection, inventory |
| `phase0/fixtures/physical/coupons/glyph_map.json`, `glyph_selection.json` | 400 instances / 20 panels and their hashes |
| `SOLUTION_LOCK_V2.md`, `PHASE0_REVIEW.md`, `PHASE0_VERDICTS.md`, `PHASE0_SPEC.md` | scope boundaries, out-of-scope list, positioning |
| `python3 -m unittest discover -s tests` | the 352-test figure |

## F. Tooling note

The sandbox has no `python-pptx`, no LibreOffice, no image converter and no network, so the
PPTX (raw OOXML) and the PDF are generated from **one layout model** by
`deck/deckkit.py` + `deck/build_deck.py`, and `deck/preview.py` rasterises each slide for
visual inspection. Text is wrapped once with Adobe base-14 metrics and each wrapped line is
emitted as its own paragraph, so PowerPoint cannot re-wrap differently from the PDF.
