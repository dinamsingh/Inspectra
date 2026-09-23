import type { EvidenceRecord } from '../../types/inspection'
import { StatusBadge } from '../ui/StatusBadge'
import styles from './EvidenceRecordCard.module.css'

const PREDICATE_TONE: Record<EvidenceRecord['ruleResult'], 'positive' | 'review' | 'issue' | 'neutral'> = {
  SATISFIED: 'positive',
  NOT_SATISFIED: 'issue',
  INDETERMINATE: 'review',
  NOT_APPLICABLE: 'neutral',
}

export function EvidenceRecordCard({ record }: { record: EvidenceRecord }) {
  const formattedTime = new Date(record.timestamp).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })

  return (
    <li className={styles.card}>
      <div>
        <p className={styles.time}>{formattedTime}</p>
        <p className={styles.source}>{record.sourceLabel}</p>
      </div>
      <div className={styles.body}>
        <p className={styles.textRow}>&ldquo;{record.extractedText}&rdquo;</p>
        <p className={styles.ruleLabel}>{record.ruleLabel}</p>
        <div>
          <StatusBadge tone={PREDICATE_TONE[record.ruleResult]}>{record.ruleResult}</StatusBadge>
        </div>
        <div className={styles.footer}>
          <span>rule {record.ruleVersion}</span>
          <span>engine {record.engineVersion}</span>
          <span>{record.measurementStatus}</span>
        </div>
      </div>
    </li>
  )
}
