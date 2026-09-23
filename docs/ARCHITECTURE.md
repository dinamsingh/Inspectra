# Inspectra — Architecture Overview

Inspectra is being developed in layers so that the validated measurement work remains independently reproducible.

## Current repository architecture

```
                    Inspectra
                        |
          +-------------+-------------+
          |                           |
       Product                     Phase 0
        layer                  measurement core
          |                           |
   capture / OCR /             planar image /
   rules / review /            geometry / measure /
   reporting                    uncertainty / gates
          |                           |
          +-------------+-------------+
                        |
                 evidence + review
```

## Phase 0

The `phase0/` tree contains the current runnable proof of concept for controlled planar printed-glyph measurement.

Its normative sequence is:

```
image / frame
   ↓
quality + fiducial gates
   ↓
undistortion + planar rectification
   ↓
baseline + boundary estimation
   ↓
physical extent
   ↓
uncertainty + guard band
   ↓
MEASURE / ABSTAIN
```

## Product layer

The final field product is designed around:

```
CAPTURE → IDENTIFY → EXTRACT → CHECK → MEASURE
        → EVIDENCE → OFFICER REVIEW → REPORT
```

The product layer is broader than Phase 0. The repository does **not** claim that every product-layer component is already implemented.

## Decision boundary

Inspectra is screening assistance.

- OCR/CV provide observations.
- The rule engine evaluates applicable rules.
- Measurement is reported only when evidence permits.
- Unreliable measurement conditions lead to abstention.
- The authorised officer remains responsible for the final legal determination.

## Deployment direction

The evaluator-facing web layer is being developed separately from the Python Phase-0 engine.

A future deployed product may expose:

- a web/mobile-facing interface,
- lightweight API/orchestration,
- persistent inspection metadata,
- evidence storage,
- and a compute service for the measurement engine.

Those deployment components are future implementation work unless a repository status entry says otherwise.
