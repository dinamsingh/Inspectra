# NiyamDrishti Phase 0 (P0-min)

Desktop proof-of-concept that answers one question, falsifiably:

> Can NiyamDrishti estimate controlled planar printed glyph extent in millimetres
> with acceptable repeatability and error, quantify its uncertainty, and abstain
> when conditions are unreliable?

Not an app.  No UI.  The phone is only a camera.  Everything here is either a
measurement, a gate, or evidence about one of those two.

**Current state:** synthetic stage complete and passing its pre-registered
criteria; physical stage (20 printed panels) specified but **not yet run**, so
there is no millimetre accuracy claim on real cameras yet.

## A. Repository structure

```
phase0/
  p0/                      library (pure standard library -- see docs A-01)
    core.py                linear algebra, sRGB EOTF, image buffer, PNG, hashing, PRNG
    camera.py              pinhole + Brown-Conrady, poses, plane homographies, rho/tilt/Z
    fiducial.py            NDFID-1 coded markers: render bits, detect, subpixel edge-line corners
    render.py              synthetic scene renderer with exact closed-form ground truth
    geometry.py            normalised DLT + Gauss-Newton homography, reprojection, LOMO, hull
    measure.py             scanline boundary estimator, cluster selection, bootstrap SE, quality
    uncertainty.py         budget combination, thickness correction, guard-band decision
    gates.py               gate policy and the MEASURE / ABSTAIN state machine
    pipeline.py            one burst -> one result (normative stage order)
    results.py             result.json + results.csv writers
    plots.py               dependency-free SVG plotting
  config/                  policies, frame certificates, camera profiles (generated)
  tools/
    make_configs.py        generate the deterministic config set
    experiments.py         the synthetic fixture suite (pre-registered safety classes)
    run_experiment.py      synthetic runner (parallel)
    analyse_results.py     statistics + plots + PASS/FAIL verdict
    calibrate_camera.py    reduced intrinsic calibration (+ --self-test)
    survey_frame.py        caliper measurements -> frame certificate
    make_frame_svg.py      printable 1:1 fiducial frame
    make_coupons_svg.py    printable coupon sheets for the 20-panel pilot
    run_real_batch.py      run the pipeline over real captures
  tests/test_p0.py         39 tests: linear algebra, geometry, ground truth, gates, end to end
  docs/
    P0_PROTOCOL.md         the physical experiment protocol
    P0_EXECUTION_PLAN.md   execution-readiness audit + frozen operational plan
    P0_CRITERIA.md         pre-registered PASS/FAIL criteria
    RESULT_SCHEMA.md       JSON/CSV schema and invariants
    P0_ASSUMPTIONS.md      unresolved assumptions and limitations
  out/                     results (generated; synthetic_v1 kept on purpose)
  fixtures/physical/        printable artefacts
```

## B. Setup

No installation, no network, no third-party packages.

```bash
python3 --version          # 3.9+
cd phase0
python3 tools/make_configs.py
python3 -m unittest discover -s tests          # 39 tests, ~40 s
```

`requirements.txt` lists the *optional* accelerated backend for a future port; it
is deliberately not required to run anything here.

## C. Runnable pipeline

```bash
# full synthetic suite (73 fixtures, 76 runs, ~3.5 min on 8 cores)
python3 tools/run_experiment.py --out out/synthetic --frames 7 --jobs 8

# quick smoke run
python3 tools/run_experiment.py --only E_MATH,E_DECISION --frames 3 --fast --out out/smoke

# analysis, plots and verdict
python3 tools/analyse_results.py --in out/synthetic
```

Outputs: `out/synthetic/results.csv`, `runs/<run_id>/result.json`,
`runs/<run_id>/frame0.png`, `manifest.json`, `analysis/RESULT.md`,
`analysis/analysis.json`, `analysis/plots/*.svg`.

## D. Synthetic fixture generator

`p0/render.py` defines the ink region analytically, so the true ink extent is
known in closed form (`design height + 2 x ink spread`) and is verified by
`test_true_height_is_exact_for_every_shape`.  It models, in this order: analytic
ink coverage through the exact inverse plane homography, reflectance in linear
light, illumination gradient, specular glare, PSF (isotropic or motion), optional
unsharp mask (ISP sharpening), sensor noise, clipping, sRGB encoding.

Controllable defects: blur, motion blur, glare, illumination gradient, noise, ink
spread, halftone dither, lens distortion, view tilt/azimuth/roll, working
distance, wrong marker ids, missing markers, print-plane offset, print-plane tilt,
low contrast, sharpening overshoot.

## E. Experiment runner

`tools/experiments.py` pre-registers every fixture with a `safety_class`:
`SAFE`, `UNSAFE_DETECTABLE`, `UNSAFE_UNDETECTABLE`, `DIAGNOSTIC`.  The analysis
uses those labels; they cannot be reassigned after seeing a result without
documenting the evidence (this happened once -- see the halftone pitch sweep and
`out/synthetic_v1`).

## F. Result schema

See `docs/RESULT_SCHEMA.md`.  Key invariant: an abstaining run **never** carries a
numeric height, bound or decision.

## G. Diagnostic plots

`out/synthetic/analysis/plots/`: true vs estimated, bias vs height, repeatability,
error distribution, blur sensitivity (with the estimator comparison), perspective
sensitivity, sampling density, illumination/glare, ink-spread tracking, abstention
causes, decision guard band, undetectable defects.

## H. Tests

`python3 -m unittest discover -s tests` (39 tests) -- linear algebra, sRGB non-affinity,
PNG round trip, distortion round trip, homography recovery, LOMO, exact ground
truth for all four glyph shapes, fiducial dictionary distance, end-to-end ideal
accuracy, hard failure on missing/wrong markers, the gate invariant (no number
when abstaining), first-order plane-offset and cosine-tilt predictions, thickness
correction, determinism, estimator superiority under noise, uncertainty
combination, guard-band branches, and fail-closed behaviour on NaN.

## I. Physical protocol

`docs/P0_PROTOCOL.md` for the method, `docs/P0_EXECUTION_PLAN.md` for the frozen
operational detail and the readiness verdict (currently
`PHYSICAL_EXPERIMENT_READY = NO`, six blockers).  Summary: print and **survey** one frame, mount 20 coupons
on a flat plate, measure every glyph with a calibrated 2400 dpi scanner
cross-checked against a measuring microscope, then capture 240 nominal bursts
(20 panels x 2 devices x 2 operators x 3 repeats x 7 frames) plus a ~60-run stress
block, and analyse with the same tooling.

## J. PASS/FAIL criteria

`docs/P0_CRITERIA.md`.  Pre-registered, encoded as constants in the analyser.
Failure narrows the claim; it never moves a threshold.

## K. Unresolved assumptions

`docs/P0_ASSUMPTIONS.md` (A-01 to A-15).  The two that matter most:

* **A-06** an out-of-plane print surface is *provably not detectable* from a single
  view -- measured, not assumed -- so it must be controlled by the fixture;
* **A-12** no physical data exists yet, so no millimetre accuracy claim about real
  cameras may be made from this repository.

## Scope discipline

This repository deliberately contains no Android code, no database, no OCR, no
rule engine and no report generator.  It exists to make one measurement claim
falsifiable before any of that is built.
