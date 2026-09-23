import { undetectableDefectFinding } from '../../data/validationMetrics'
import styles from './PendingValidationNotice.module.css'

export function PendingValidationNotice() {
  return (
    <div className={styles.notice}>
      <p className={styles.heading}>Physical laboratory validation pending</p>
      <p className={styles.text}>
        Every number above comes from a synthetic harness where ground truth is exact by
        construction. No physical camera data has been collected yet — a pre-registered protocol
        exists but has not been executed.
      </p>
      <p className={styles.text}>
        <strong>A finding worth naming honestly:</strong> {undetectableDefectFinding.description}
      </p>
    </div>
  )
}
