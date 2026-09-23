import type { ValidationMetric } from '../types/inspection'

/**
 * Real numbers from phase0/out/synthetic/analysis/RESULT.md — verified against
 * the repo, not estimated. Every metric is synthetic-harness only: ground truth
 * is exact because the harness generates it, so these are not physical-camera
 * results and are not a legal accuracy claim.
 */
export const validationMetrics: ValidationMetric[] = [
  {
    label: 'Accuracy bias',
    value: '+0.00052 mm',
    status: 'SYNTHETIC-ONLY',
    note: 'Mean signed error on 17 nominal synthetic runs.',
  },
  {
    label: 'p95 absolute error',
    value: '0.00544 mm',
    status: 'SYNTHETIC-ONLY',
  },
  {
    label: 'Max absolute error',
    value: '0.00802 mm',
    status: 'SYNTHETIC-ONLY',
  },
  {
    label: 'Median burst repeatability (SD)',
    value: '0.00246 mm',
    status: 'SYNTHETIC-ONLY',
  },
  {
    label: 'Interval coverage',
    value: '1.000 (n = 17)',
    status: 'SYNTHETIC-ONLY',
    note: 'k is nominal (1.645), not yet calibrated against physical data.',
  },
  {
    label: 'Unsafe-condition abstention',
    value: '11 of 11',
    status: 'SYNTHETIC-ONLY',
    note: 'Every fixture engineered to be unmeasurable was correctly abstained, not guessed.',
  },
  {
    label: 'Decision safety',
    value: '0 false-clear, 0 false-accuse',
    status: 'SYNTHETIC-ONLY',
    note: '4 undersize and 4 compliant guard-band fixtures, synthetic harness.',
  },
  {
    label: 'Automated test suite',
    value: '352 tests passing',
    status: 'VALIDATED',
  },
  {
    label: 'Physical laboratory validation',
    value: 'Not started',
    status: 'PENDING-PHYSICAL',
    note: 'No coupon has been printed and no reference instrument used yet. A pre-registered protocol exists but has not been executed.',
  },
]

export const undetectableDefectFinding = {
  errorMm: -0.1847,
  description:
    'A single camera view can pass every calibration, geometry, and image-quality gate while the true measurement error reaches 0.1847 mm, caused by out-of-plane tilt the gates cannot see from one angle. This is an engineering finding from the synthetic harness, not a field observation — it is the reason a mechanical flatness fixture is planned as a hardware control, rather than trying to catch the defect with a software gate alone.',
}
