import styles from './PrototypeStatusBanner.module.css'

export function PrototypeStatusBanner() {
  return (
    <div className={styles.banner}>
      <span className={styles.indicator} aria-hidden="true" />
      <p className={styles.text}>
        <strong>Prototype in active development.</strong> The measurement and abstention engine
        below is synthetically validated. Capture, extraction, and rule-checking are shown as
        sample data while those parts are built.
      </p>
    </div>
  )
}
