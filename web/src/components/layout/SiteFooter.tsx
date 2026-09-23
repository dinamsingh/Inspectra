import { projectConfig } from '../../config/project'
import styles from './SiteFooter.module.css'

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.identity}>
          <p className={styles.wordmark}>{projectConfig.PROJECT_NAME}</p>
          <p className={styles.note}>
            A screening assistant for Legal Metrology field inspection. Final legal determination
            remains with the authorised officer.
          </p>
        </div>
        <div className={styles.meta}>
          <span>Problem statement {projectConfig.PROJECT_ID.replace('SIH', '')}</span>
          <span>Smart India Hackathon 2026</span>
        </div>
      </div>
    </footer>
  )
}
