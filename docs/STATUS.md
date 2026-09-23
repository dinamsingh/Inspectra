# Inspectra — Current Status

Last reviewed for the evaluator-facing repository.

## At a glance

| Area | Status |
|---|---|
| Phase-0 measurement engine | Implemented |
| Synthetic validation | Completed |
| Automated tests | 352 passing at the documented baseline |
| Physical laboratory validation | Pending |
| Android field client | Planned |
| OCR / rule / report product layer | Designed, not represented as fully implemented |
| Public web prototype | In development |

## Evidence boundary

The repository contains a reproducible synthetic benchmark with exact ground truth. Those results are **not** physical-camera validation and are not a legal accuracy claim.

No physical-camera millimetre accuracy result, calibration certificate, or completed laboratory validation is claimed by the current repository.

## Phase-0 physical readiness

The current handoff records:

- B1 — closed
- B2 — physical evidence/equipment — open
- B3 — closed
- B4 — physical survey/verification — open
- B5 — closed
- B6 — physical equipment availability — open

Therefore:

**PHYSICAL_EXPERIMENT_READY = NO**

## Product maturity

The repository intentionally separates three states:

1. **Implemented** — code and repository evidence exist.
2. **Designed** — architecture/protocol is specified but not presented as a finished product.
3. **Pending** — physical validation or future product implementation remains.

This separation is part of the project's evidence discipline.
