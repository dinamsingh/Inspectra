# Inspectra — SIH 2026 | Legal Metrology Inspection Assistant

> **Problem Statement SIH26034**  
> Software System to check compliance of Packaged Commodities under the Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels.

Inspectra is being developed as an **evidence-led, offline-first field inspection assistant** for Legal Metrology officers.

Its core idea is simple:

> **Reading a declaration is not the same as establishing that it is physically printed at the required size.**

Inspectra therefore treats OCR, rules and physical measurement as separate evidence sources, and is designed to **abstain instead of guessing** when the available evidence is insufficient.

---

## Current status

| Area | Status | What is true today |
|---|---|---|
| Measurement engine | **Implemented** | Runnable Phase-0 proof of concept with deterministic processing, uncertainty and fail-closed gates |
| Synthetic validation | **Completed** | 76 controlled runs with exact synthetic ground truth |
| Automated tests | **352 passing** | Repository-verifiable engineering state |
| Physical validation | **Pending** | No real-camera millimetre accuracy claim is made |
| Android field app | **Planned** | Product layer is designed; not presented as finished |
| OCR / rule / report product layer | **Designed** | Architecture and boundaries are specified; not claimed as fully implemented |
| Public web prototype | **In development** | Will expose the evaluator-facing product workflow |

> **Important:** Synthetic benchmark results are not physical-camera results and are not a legal accuracy claim.

---

## Why this project is technically non-trivial

A conventional OCR pipeline can read 500 g perfectly even when the printed characters are physically too small.

The difficult part is therefore not only:

    image → OCR → rule check

It is:

    capture → evidence quality → calibrated physical measurement → uncertainty → abstention → officer review

The project is deliberately designed around that boundary.

### Core design principles

- **Evidence-bounded measurement** — produce a millimetre estimate only when the measurement conditions support it.
- **Uncertainty is part of the result** — not a hidden confidence score.
- **Fail-closed abstention** — unreliable evidence produces no forced number.
- **Rule-version awareness** — inspection findings are tied to the applicable rule version.
- **Officer remains the final legal decision-maker** — Inspectra assists screening; it does not adjudicate.
- **Evidence stays linked** — source image, extracted observation, rule result and measurement context travel together.

---

## What is actually built

### Phase 0 measurement engine

The current repository contains a reproducible desktop proof of concept for controlled planar printed-glyph measurement.

High-level flow:

    Image / synthetic frame
            ↓
    Image quality + fiducial checks
            ↓
    Undistortion + planar rectification
            ↓
    Baseline refinement + boundary extraction
            ↓
    Physical extent estimate
            ↓
    Uncertainty budget + guard-band decision
            ↓
    MEASURE  ───────────────┐
                            │
    ABSTAIN ← unsafe/weak evidence

The engine is intentionally narrower than the final product. It is a **falsifiable measurement core**, not a finished mobile application.

---

## Synthetic validation snapshot

All figures below are from the controlled synthetic harness and have exact ground truth.

| Measure | Result |
|---|---:|
| Synthetic runs | **76** |
| Max absolute arithmetic error | **0.00802 mm** |
| P95 absolute error (SAFE nominal conditions) | **0.00544 mm** |
| Median burst SD | **0.00246 mm** |
| Targeted unsafe cases abstained | **11 / 11** |
| False-clear of undersized cases | **0 / 4** |
| False-accuse of compliant cases | **0 / 4** |
| Safe-condition measure rate | **1.00** |

See the full machine-generated result:

- [phase0/out/synthetic/analysis/RESULT.md](phase0/out/synthetic/analysis/RESULT.md)

And the method:

- [phase0/docs/P0_PROTOCOL.md](phase0/docs/P0_PROTOCOL.md)
- [phase0/docs/P0_CRITERIA.md](phase0/docs/P0_CRITERIA.md)
- [phase0/docs/P0_ASSUMPTIONS.md](phase0/docs/P0_ASSUMPTIONS.md)

---

## Measurement boundary

The current Phase-0 measurand is deliberately narrow:

**visible printed-ink extent perpendicular to the fitted baseline**, under controlled planar conditions.

It is **not**:

- nominal font size,
- OCR-box height,
- a generic claim about every package surface,
- or a claim that the software itself makes the final statutory determination.

Curved, moulded, flexible, embossed, creased or otherwise non-planar surfaces are not treated as automatically measurable. Where evidence cannot support the estimate, the system is designed to abstain.

---

## Target product workflow

The final field workflow is designed as:

    CAPTURE
       ↓
    IDENTIFY
       ↓
    EXTRACT
       ↓
    CHECK
       ↓
    MEASURE (when evidence permits)
       ↓
    EVIDENCE
       ↓
    OFFICER REVIEW
       ↓
    REPORT

The product-level architecture is documented separately from the Phase-0 engine so that the validated measurement work remains reproducible and independently auditable.

→ [Architecture overview](docs/ARCHITECTURE.md)  
→ [Current project status](docs/STATUS.md)

---

## Repository map

    Inspectra/
    ├── phase0/                         # Measurement POC + synthetic validation
    │   ├── p0/                         # Core measurement implementation
    │   ├── tools/                      # Experiment, analysis and validation tools
    │   ├── tests/                      # Automated tests
    │   ├── config/                     # Measurand, gate and uncertainty policies
    │   ├── docs/                       # Frozen protocol, criteria and assumptions
    │   ├── fixtures/                   # Physical experiment artefacts
    │   └── out/synthetic/              # Committed synthetic evidence
    │
    ├── sih2026/                        # SIH deck, claims ledger and evaluator audit
    │
    ├── SOLUTION_LOCK_V2.md             # Frozen product + architecture baseline
    ├── PHASE0_SPEC.md                  # Phase-0 implementation specification
    ├── PHASE0_REVIEW.md                # Adversarial technical review
    ├── PHASE0_VERDICTS.md              # Design decision record
    ├── HANDOFF.md                      # Detailed engineering handoff
    └── README.md                       # This public project overview

---

## Quick start — run the measurement POC

The current Phase-0 reference implementation is intentionally dependency-light and uses the Python standard library for its core run.

    cd phase0

    python3 tools/make_configs.py
    python3 -m unittest discover -s tests

    python3 tools/run_experiment.py \
      --out out/run2 \
      --frames 7 \
      --jobs 8

    python3 tools/analyse_results.py \
      --in out/run2

For the committed synthetic result:

    cat phase0/out/synthetic/analysis/RESULT.md

---

## What is not claimed

Inspectra deliberately does **not** claim:

- real-world millimetre accuracy from physical cameras before laboratory validation,
- 100% accuracy or zero false positives,
- automatic legal adjudication,
- court-admissibility or legal defensibility,
- correct net quantity from an image alone,
- reliable physical measurement on every packaging shape,
- or government-system integration that has not been authorised and built.

This repository separates **implemented evidence**, **designed architecture**, and **pending validation** rather than collapsing them into one maturity claim.

---

## Key engineering records

- [Solution Lock V2](SOLUTION_LOCK_V2.md) — frozen scope, architecture and non-negotiable boundaries
- [Phase 0 Specification](PHASE0_SPEC.md) — implementation specification
- [Adversarial Review](PHASE0_REVIEW.md) — technical challenge and revisions
- [Phase 0 Verdicts](PHASE0_VERDICTS.md) — decision record
- [Phase 0 README](phase0/README.md) — detailed engine documentation
- [Synthetic Results](phase0/out/synthetic/analysis/RESULT.md) — reproducible benchmark output
- [SIH Claims Ledger](sih2026/CLAIMS_LEDGER.md) — claims, evidence and deliberate non-claims
- [Evaluator Audit](sih2026/EVALUATOR_AUDIT.md) — what was challenged and changed

---

## Project resources

- **GitHub:** https://github.com/dinamsingh/Inspectra
- **SIH Problem Statement:** SIH26034
- **Prototype:** evaluator-facing web layer in active development
- **Demo:** will be added to the prototype hub when the product workflow is ready

---

## One-line positioning

> **Inspectra helps Legal Metrology officers inspect packaged products, connect declarations and evidence to versioned rules, estimate visible printed text extent under controlled conditions, and abstain when the evidence is not sufficient.**

---

**Project:** Inspectra  
**SIH 2026 | Problem Statement 26034**  
**Primary user:** Legal Metrology enforcement officer