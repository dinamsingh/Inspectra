import type { AbstentionResult } from '../../types/inspection'
import styles from './AbstentionCard.module.css'

interface AbstentionCardProps {
  abstention: AbstentionResult
}

export function AbstentionCard({ abstention }: AbstentionCardProps) {
  return (
    <div className={styles.card} aria-live="polite">
      <h3 className={styles.heading}>Measurement not established</h3>
      <code className={styles.reasonCode}>{abstention.reason}</code>
      <p className={styles.explanation}>{abstention.explanation}</p>
      <p className={styles.footnote}>
        No forced numeric result is reported when measurement conditions are unreliable.
      </p>
    </div>
  )
}
