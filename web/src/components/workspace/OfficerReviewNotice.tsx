import styles from './OfficerReviewNotice.module.css'

export const OFFICER_REVIEW_TEXT =
  'Inspectra surfaces candidate findings for review. The final legal determination remains with the authorised officer.'

export function OfficerReviewNotice() {
  return (
    <p className={styles.notice}>
      <span className={styles.mark} aria-hidden="true" />
      {OFFICER_REVIEW_TEXT}
    </p>
  )
}
