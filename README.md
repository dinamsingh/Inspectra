# SIH26034 NiyamDrishti — Phase 0 (P0-min)

Desktop proof-of-concept for calibrated planar printed-glyph measurement, plus the
frozen strategy and adversarial review documents.

| Path | What it is |
|---|---|
| `phase0/` | Runnable P0-min pipeline, synthetic fixture harness, tests, experiment results |
| `phase0/out/synthetic/analysis/RESULT.md` | Headline experiment verdict |
| `SOLUTION_LOCK_V2.md` | Frozen product + architecture baseline |
| `PHASE0_REVIEW.md` | Adversarial review of the Phase-0 design |
| `PHASE0_VERDICTS.md` | PASS / MODIFY / REMOVE / EXPERIMENT verdicts on 59 decisions |
| `PHASE0_SPEC.md` | Phase-0 implementation specification |

Quick start (no dependencies, standard library only):

```bash
cd phase0
python3 tools/make_configs.py
python3 -m unittest discover -s tests
python3 tools/run_experiment.py --out out/run2 --frames 7 --jobs 8
python3 tools/analyse_results.py --in out/run2
```

Status: synthetic stage passes its pre-registered criteria. No physical camera
data yet, so no millimetre accuracy claim about real devices is supported. See
`phase0/docs/P0_PROTOCOL.md`.
