# Inspectra — SIH 2026 idea submission deck

Problem statement **SIH26034** — Software System to check compliance of Packaged
Commodities under the Legal Metrology (Packaged Commodities) Rules, 2011 by scanning
products, images and labels. Ministry of Consumer Affairs, Food & Public Distribution
(Department of Consumer Affairs).

## Files

| File | What it is |
|---|---|
| `Inspectra_SIH2026_Idea.pptx` | the editable deck — 6 slides, 13.333 × 7.5 in, every diagram native shapes, no flattened images |
| `Inspectra_SIH2026_Idea.pdf` | the upload artefact (the portal takes PDF only) |
| `preview/slide1..6.png` | layout rasterisations used for visual QA |
| `OUTLINE.md` | slide-by-slide content outline + the template compliance audit |
| `CLAIMS_LEDGER.md` | every claim, its source, its status, and the claims deliberately not made |
| `SOURCES.md` | external and repository sources |
| `EVALUATOR_AUDIT.md` | adversarial evaluator review and the changes it forced |

Generators live in `deck/` (`deckkit.py`, `build_deck.py`, `preview.py`). Re-run
`python3 deck/build_deck.py` to rebuild both outputs; it exits non-zero if any geometry or
overflow check fails.

## Before you upload — three things to fill in

1. **Theme** (slide 1) — as listed for SIH26034 on the portal.
2. **Team ID** and **Team Name** (slide 1) — as registered.
3. **Problem Statement ID** is written `SIH26034`, following the 2025 format (`SIH25108`).
   Confirm the exact string on the portal.

Optional: the top-right mark is a text wordmark, not the official artwork. To use the exact
official logo, paste the PNG from the template file over it — nothing is locked.

## What the deck claims, in one place

**Validated (repository-verifiable):** a reproducible, dependency-free measurement engine;
352 automated tests passing; bit-identical re-runs; ~1.3 s per 12 MP frame; the measurand,
gate set and abstention code as shipped; `k = 1.645` declared uncalibrated; pre-registered
coverage of 400 glyph instances and 20 panels, hash-checked.

**Synthetic-only (controlled benchmark, labelled as such on the slide):** 76 runs, 10/10
pre-registered criteria PASS, max arithmetic error 0.008 mm on ideal renders, median burst
SD 0.0025 mm, 11/11 targeted unsafe cases abstained, 0 false-clear of 4 undersized, 0
false-accuse of 4 compliant, measure rate 1.00 on safe conditions, and the 0.185 mm
out-of-plane error that every gate passes.

**Designed and frozen, not executed:** P1–P7 acceptance bands; the independent reference
procedure (2400 dpi scan primary, microscope cross-check); the flatness acceptance; the
equipment inventory; the Android client itself.

**Pending:** physical laboratory validation. Stated on the slide as *"laboratory validation
pending — no physical claim is made"*, and repeated on slide 6. No physical accuracy
number, scanner-vs-microscope result, calibration certificate or equipment-availability
claim appears anywhere.

**Never claimed:** first / only / unique / best; 100 % accurate; zero false positives;
legally defensible or court-admissible; tamper-proof; government-integrated; or that the
software makes the legal determination.
