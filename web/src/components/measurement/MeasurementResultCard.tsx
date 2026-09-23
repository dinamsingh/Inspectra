import type { MeasurementResult } from '../../types/inspection'
import { StatusBadge } from '../ui/StatusBadge'
import styles from './MeasurementResultCard.module.css'

interface MeasurementResultCardProps {
  result: MeasurementResult
}

const DECISION_TONE: Record<MeasurementResult['decision'], 'positive' | 'issue' | 'review'> = {
  MEETS_SCREENING_THRESHOLD: 'positive',
  POTENTIAL_UNDERSIZE: 'issue',
  REQUIRES_OFFICER_REVIEW_BORDERLINE: 'review',
}

export function MeasurementResultCard({ result }: MeasurementResultCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <div>
          <p className={styles.label}>Observed printed-ink extent</p>
          <span className={styles.value}>
            {result.observedExtentMm.toFixed(2)}
            <span className={styles.unit}>mm</span>
          </span>
        </div>
        <StatusBadge tone={DECISION_TONE[result.decision]}>{result.decision}</StatusBadge>
      </div>
      <div className={styles.metaGrid}>
        <div>
          <p className={styles.metaLabel}>Interval</p>
          <p className={styles.metaValue}>
            [{result.lowerBoundMm.toFixed(2)}, {result.upperBoundMm.toFixed(2)}]
          </p>
        </div>
        <div>
          <p className={styles.metaLabel}>Uncertainty</p>
          <p className={styles.metaValue}>± {result.uncertaintyMm.toFixed(2)} mm</p>
        </div>
        <div>
          <p className={styles.metaLabel}>Screening threshold</p>
          <p className={styles.metaValue}>{result.thresholdMm.toFixed(2)} mm</p>
        </div>
        <div>
          <p className={styles.metaLabel}>Evidence</p>
          <p className={styles.metaValue}>Sufficient</p>
        </div>
      </div>
    </div>
  )
}
