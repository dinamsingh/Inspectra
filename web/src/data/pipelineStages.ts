import type { PipelineStage } from '../types/inspection'

/**
 * Sample content for the 8-stage pipeline (HANDOFF.md).
 * Field values are representative sample data for a controlled preview —
 * not a live capture. See StartInspectionSection for the "Sample inspection" label.
 */
export const pipelineStages: PipelineStage[] = [
  {
    id: 'CAPTURE',
    order: 1,
    label: 'Capture',
    summary: 'Officer captures multiple faces of the package under controlled lighting.',
    detail:
      'The officer photographs each declared face of the package — front, back, and any face carrying a printed declaration. A burst of frames is taken per face so the measurement stage can assess repeatability later.',
    sampleFields: [
      { label: 'Package ID', value: 'INS-2026-000482' },
      { label: 'Faces captured', value: '4 of 4' },
      { label: 'Frames per face', value: '7' },
    ],
  },
  {
    id: 'IDENTIFY',
    order: 2,
    label: 'Identify',
    summary: 'The package and its declared category are identified from the captured faces.',
    detail:
      'Brand and product category are identified from the front-of-pack face. This narrows which Legal Metrology declarations and thresholds apply in the CHECK stage.',
    sampleFields: [
      { label: 'Brand', value: 'Sample brand — Anaaj Foods' },
      { label: 'Category', value: 'Packaged food — cereal-based' },
      { label: 'Commodity class', value: 'Pre-packaged, retail sale' },
    ],
  },
  {
    id: 'EXTRACT',
    order: 3,
    label: 'Extract',
    summary: 'Declarations printed on the package are read from the captured images.',
    detail:
      'Text is extracted from each face and mapped to expected declaration fields. Extraction confidence and source face are retained with each field — extraction quality has not yet been assessed against the CHECK stage rules.',
    sampleFields: [
      { label: 'Manufacturer', value: 'Sample Foods Pvt. Ltd.' },
      { label: 'Net quantity', value: '500 g' },
      { label: 'MRP', value: '₹ 145.00 (inclusive of all taxes)' },
      { label: 'Manufacturing date', value: '03/2026' },
      { label: 'Best before', value: '12 months from packaging' },
    ],
  },
  {
    id: 'CHECK',
    order: 4,
    label: 'Check',
    summary: 'Extracted declarations are screened against versioned Legal Metrology rules.',
    detail:
      'Each declaration is evaluated against the applicable rule set. Results use a four-valued outcome — SATISFIED, NOT_SATISFIED, INDETERMINATE, or NOT_APPLICABLE — rather than a binary pass/fail, so missing or ambiguous evidence is never forced into a false positive or negative.',
    sampleFields: [
      { label: 'Net quantity declaration', value: 'SATISFIED' },
      { label: 'MRP declaration', value: 'SATISFIED' },
      { label: 'Best-before format', value: 'INDETERMINATE' },
      { label: 'Rule pack version', value: 'LM-PC-2011 rev. sample' },
    ],
  },
  {
    id: 'MEASURE',
    order: 5,
    label: 'Measure',
    summary: 'Printed text extent is measured when the captured evidence permits it.',
    detail:
      'When calibration, geometry, and image-quality gates are satisfied, the visible printed-ink extent is estimated in millimetres with a stated uncertainty. When they are not, the engine abstains rather than reporting a number it cannot support — see the measurement panel below.',
    sampleFields: [
      { label: 'Observed extent', value: '2.47 mm' },
      { label: 'Uncertainty', value: '± 0.08 mm' },
      { label: 'Evidence sufficiency', value: 'Sufficient' },
    ],
  },
  {
    id: 'EVIDENCE',
    order: 6,
    label: 'Evidence',
    summary: 'Source image, extracted text, rule result, and measurement are linked into one record.',
    detail:
      'Every finding stays linked to the image it came from, the declaration text extracted, the rule version applied, and the measurement engine version used — so a reviewer can trace any result back to its source.',
    sampleFields: [
      { label: 'Linked source images', value: '4' },
      { label: 'Rule version', value: 'LM-PC-2011 rev. sample' },
      { label: 'Engine version', value: 'p0-min synthetic' },
    ],
  },
  {
    id: 'REVIEW',
    order: 7,
    label: 'Review',
    summary: 'The officer examines candidate findings against the linked evidence.',
    detail:
      'Inspectra surfaces candidate findings for the officer to examine — it does not issue a violation determination. The officer decides what, if anything, warrants further action.',
    sampleFields: [
      { label: 'Candidate findings', value: '1 — best-before format, INDETERMINATE' },
      { label: 'Officer decision', value: 'Pending' },
    ],
  },
  {
    id: 'REPORT',
    order: 8,
    label: 'Report',
    summary: 'An evidence-linked inspection record is generated for the officer’s decision.',
    detail:
      'The final record bundles the linked evidence, screening results, and measurement status into a single reviewable document. The authorised officer’s decision — not an automated verdict — is what the record exists to support.',
    sampleFields: [
      { label: 'Record status', value: 'Draft — awaiting officer decision' },
      { label: 'Evidence items', value: '4 images, 5 declarations, 1 measurement' },
    ],
  },
]
