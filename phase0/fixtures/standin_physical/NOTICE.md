# STAND-IN PHYSICAL_PILOT dataset — NOT PHYSICAL EVIDENCE

Everything in this directory is **synthetic and arbitrary**.  No camera, coupon,
fiducial frame, scanner or microscope was involved in producing any number here.

## What it is for

Exercising the plumbing of `tools/analyse_physical.py`: that `PHYSICAL_PILOT` rows are
accepted as a population, that P1–P7 are computed, that missing data yields
`UNCOMPUTABLE` rather than a silent zero, that abstentions survive into the
denominators, and that the output is deterministic.

## What it is NOT

* not a measurement of anything physical;
* not evidence for or against any P-criterion;
* not a prediction of what the real pilot will produce;
* not to be quoted, screenshotted or put in a presentation.

`phase0/docs/P0_ASSUMPTIONS.md` A-12 still holds: **no physical data exists.**

## How the numbers were made

`make_standin.py` fixes generator parameters and lets the criteria fall wherever they
fall.  It targets a *mixture* of statuses so every analyser branch is covered — it does
**not** target a passing outcome.

| Parameter | Value | Purpose |
|---|---|---|
| `GLOBAL_OFFSET_MM` | 0.020 | a systematic offset shared by both devices |
| `DEVICE_OFFSET_MM` | A +0.015, B −0.015 | gives P4 something non-zero to measure |
| `WITHIN_CELL_SD_MM` | 0.090 | spread across the three angle repeats |
| `U_C_MM`, `K` | 0.050, 1.645 | reported interval, k matching `uncertainty_model_v1.json` |
| `REFERENCE_DIFF_MM` | 0.018 | scanner-vs-microscope disagreement scale for P1 |
| abstained nominal runs | 1 of 24 | keeps an abstention in the P5 denominator |
| stress runs measured | 1 of 8 | makes P6 land outside its Go band |

Randomness is the repository's deterministic `Rng` seeded from the run id, so
regenerating reproduces the files byte for byte.

## Contents

| File | Role |
|---|---|
| `results.csv` | 32 rows: 24 nominal (1 abstained) + 8 stress (7 abstained) |
| `manifest_used.json` | the pre-registered run list the analyser reads populations from |
| `reference_table.csv` | 16 glyphs × 2 methods, the shape `P0_EXECUTION_PLAN.md` §2.4 defines |

Regenerate with:

```bash
python3 fixtures/standin_physical/make_standin.py
```
