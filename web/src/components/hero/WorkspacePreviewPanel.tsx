import { StatusBadge } from '../ui/StatusBadge'
import styles from './WorkspacePreviewPanel.module.css'

export function WorkspacePreviewPanel() {
  return (
    <div className={styles.frame} aria-hidden="true">
      <div className={styles.chrome}>
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.chromeLabel}>Sample inspection — CHECK stage</span>
      </div>
      <div className={styles.body}>
        <div className={styles.rowTop}>
          <span className={styles.idLabel}>Package ID</span>
          <span className={styles.idValue}>INS-2026-000482</span>
        </div>
        <div className={styles.fieldGrid}>
          <div className={styles.field}>
            <div className={styles.fieldLabel}>Net quantity</div>
            <div className={styles.fieldValue}>500 g</div>
          </div>
          <div className={styles.field}>
            <div className={styles.fieldLabel}>MRP</div>
            <div className={styles.fieldValue}>₹ 145.00</div>
          </div>
          <div className={styles.field}>
            <div className={styles.fieldLabel}>Manufacturing date</div>
            <div className={styles.fieldValue}>03/2026</div>
          </div>
          <div className={styles.field}>
            <div className={styles.fieldLabel}>Best before</div>
            <div className={styles.fieldValue}>12 months</div>
          </div>
        </div>
        <div className={styles.statusRow}>
          <StatusBadge tone="positive">Net quantity — SATISFIED</StatusBadge>
          <StatusBadge tone="review">Best-before format — INDETERMINATE</StatusBadge>
        </div>
      </div>
    </div>
  )
}
