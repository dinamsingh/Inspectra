import type { ValidationMetric } from '../../types/inspection'
import { StatusBadge } from '../ui/StatusBadge'
import styles from './SyntheticMetricCard.module.css'

const STATUS_TONE: Record<ValidationMetric['status'], 'positive' | 'accent' | 'neutral' | 'review'> = {
  'SYNTHETIC-ONLY': 'accent',
  VALIDATED: 'positive',
  DESIGNED: 'neutral',
  'PENDING-PHYSICAL': 'review',
}

export function SyntheticMetricCard({ metric }: { metric: ValidationMetric }) {
  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <span className={styles.label}>{metric.label}</span>
        <StatusBadge tone={STATUS_TONE[metric.status]}>{metric.status}</StatusBadge>
      </div>
      <p className={styles.value}>{metric.value}</p>
      {metric.note && <p className={styles.note}>{metric.note}</p>}
    </div>
  )
}
