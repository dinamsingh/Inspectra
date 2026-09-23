import { projectConfig } from '../../config/project'
import styles from './DemoVideoPlaceholder.module.css'

export function DemoVideoPlaceholder() {
  if (projectConfig.DEMO_VIDEO_URL) {
    return (
      <div className={styles.embedWrapper}>
        <iframe
          src={projectConfig.DEMO_VIDEO_URL}
          title={`${projectConfig.PROJECT_NAME} demo video`}
          className={styles.embed}
          allowFullScreen
        />
      </div>
    )
  }

  return (
    <div className={styles.placeholder} role="img" aria-label="Demo video reserved space">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M6 4.5h9l5 5V19a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19V6A1.5 1.5 0 0 1 5.5 4.5H6Z"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path d="m10.5 10 4 2.3-4 2.3v-4.6Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
      </svg>
      <p>Demo video will be available here.</p>
    </div>
  )
}
