/**
 * Status vocabulary mirrored from the repo's own design docs
 * (SOLUTION_LOCK_V2.md, HANDOFF.md, phase0/out/synthetic/analysis/RESULT.md).
 * Nothing here is invented — every literal is a real token used in the repo.
 */

// The 8 product pipeline stages (HANDOFF.md).
export type PipelineStageId =
  | 'CAPTURE'
  | 'IDENTIFY'
  | 'EXTRACT'
  | 'CHECK'
  | 'MEASURE'
  | 'EVIDENCE'
  | 'REVIEW'
  | 'REPORT'

export interface PipelineStage {
  id: PipelineStageId
  order: number
  label: string
  summary: string
  detail: string
  sampleFields: { label: string; value: string }[]
}

// Measurement-level decision (phase0 gates.py / RESULT.md).
export type MeasurementDecision =
  | 'MEETS_SCREENING_THRESHOLD'
  | 'POTENTIAL_UNDERSIZE'
  | 'REQUIRES_OFFICER_REVIEW_BORDERLINE'

// The 8 gate stages an abstention can be attributed to. Distinct from PipelineStageId.
export type GateStage =
  | 'PROFILE'
  | 'FIDUCIAL'
  | 'IMAGE_QUALITY'
  | 'GEOMETRY'
  | 'PLANARITY'
  | 'SEGMENTATION'
  | 'BURST'
  | 'UNCERTAINTY'

export type AbstentionReason = `PHYSICAL_SIZE_NOT_ESTABLISHED_${GateStage}`

// Package-level aggregate status (SOLUTION_LOCK_V2.md §13).
export type PackageStatus =
  | 'INSUFFICIENT_EVIDENCE'
  | 'PHYSICAL_SIZE_NOT_ESTABLISHED'
  | 'REQUIRES_OFFICER_REVIEW'
  | 'POTENTIAL_NON_COMPLIANCE'
  | 'COMPLIANT_SCREENING'

export const PACKAGE_STATUS_LABEL: Record<PackageStatus, string> = {
  INSUFFICIENT_EVIDENCE: 'Insufficient evidence',
  PHYSICAL_SIZE_NOT_ESTABLISHED: 'Physical size not established',
  REQUIRES_OFFICER_REVIEW: 'Requires officer review',
  POTENTIAL_NON_COMPLIANCE: 'Potential non-compliance — candidate finding',
  // "compliant certificate" wording is explicitly forbidden in the repo.
  COMPLIANT_SCREENING: 'No issue identified in completed in-scope screening checks',
}

// Rule-evaluation predicate (4-valued, SOLUTION_LOCK_V2.md).
export type RulePredicate = 'SATISFIED' | 'NOT_SATISFIED' | 'INDETERMINATE' | 'NOT_APPLICABLE'

export interface MeasurementResult {
  decision: MeasurementDecision
  observedExtentMm: number
  lowerBoundMm: number
  upperBoundMm: number
  uncertaintyMm: number
  thresholdMm: number
}

export interface AbstentionResult {
  reason: AbstentionReason
  gateStage: GateStage
  explanation: string
}

export interface EvidenceRecord {
  id: string
  timestamp: string
  sourceLabel: string
  extractedText: string
  ruleResult: RulePredicate
  ruleLabel: string
  measurementStatus: string
  ruleVersion: string
  engineVersion: string
}

export type ValidationClaimStatus = 'SYNTHETIC-ONLY' | 'VALIDATED' | 'DESIGNED' | 'PENDING-PHYSICAL'

export interface ValidationMetric {
  label: string
  value: string
  status: ValidationClaimStatus
  note?: string
}
