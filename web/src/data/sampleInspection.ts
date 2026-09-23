import type {
  AbstentionResult,
  EvidenceRecord,
  MeasurementResult,
} from '../types/inspection'

/**
 * Sample measurement states used by the measurement panel exhibit.
 * All values are representative preview data, not a live result.
 */
export const sampleMeasurementAccepted: MeasurementResult = {
  decision: 'MEETS_SCREENING_THRESHOLD',
  observedExtentMm: 3.27,
  lowerBoundMm: 3.24,
  upperBoundMm: 3.30,
  uncertaintyMm: 0.03,
  thresholdMm: 3.0,
}

export const sampleMeasurementUndersize: MeasurementResult = {
  decision: 'POTENTIAL_UNDERSIZE',
  observedExtentMm: 2.70,
  lowerBoundMm: 2.68,
  upperBoundMm: 2.73,
  uncertaintyMm: 0.03,
  thresholdMm: 3.0,
}

export const sampleMeasurementBorderline: MeasurementResult = {
  decision: 'REQUIRES_OFFICER_REVIEW_BORDERLINE',
  observedExtentMm: 2.99,
  lowerBoundMm: 2.93,
  upperBoundMm: 3.05,
  uncertaintyMm: 0.06,
  thresholdMm: 3.0,
}

export const sampleAbstention: AbstentionResult = {
  reason: 'PHYSICAL_SIZE_NOT_ESTABLISHED_IMAGE_QUALITY',
  gateStage: 'IMAGE_QUALITY',
  explanation:
    'The captured frames did not meet the minimum contrast threshold needed to resolve the printed-text boundary reliably. No numeric result is reported when measurement conditions are unreliable — the officer should recapture under better lighting before re-attempting measurement.',
}

export const sampleEvidenceRecords: EvidenceRecord[] = [
  {
    id: 'EV-0001',
    timestamp: '2026-03-11T10:14:02+05:30',
    sourceLabel: 'Front face, frame 3 of 7',
    extractedText: 'Net Qty: 500 g',
    ruleResult: 'SATISFIED',
    ruleLabel: 'Net quantity declaration present and legible',
    measurementStatus: 'Not applicable to this face',
    ruleVersion: 'LM-PC-2011 rev. sample',
    engineVersion: 'p0-min synthetic',
  },
  {
    id: 'EV-0002',
    timestamp: '2026-03-11T10:14:47+05:30',
    sourceLabel: 'Front face, frame 3 of 7',
    extractedText: 'MRP ₹145.00 (incl. of all taxes)',
    ruleResult: 'SATISFIED',
    ruleLabel: 'MRP declaration format',
    measurementStatus: 'MEETS_SCREENING_THRESHOLD',
    ruleVersion: 'LM-PC-2011 rev. sample',
    engineVersion: 'p0-min synthetic',
  },
  {
    id: 'EV-0003',
    timestamp: '2026-03-11T10:15:19+05:30',
    sourceLabel: 'Back face, frame 5 of 7',
    extractedText: 'Best Before: 12 months from pkg.',
    ruleResult: 'INDETERMINATE',
    ruleLabel: 'Best-before declaration format',
    measurementStatus: 'Not applicable to this face',
    ruleVersion: 'LM-PC-2011 rev. sample',
    engineVersion: 'p0-min synthetic',
  },
]
