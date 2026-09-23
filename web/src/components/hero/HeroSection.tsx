import { projectConfig } from '../../config/project'
import { Button } from '../ui/Button'
import { Eyebrow } from '../ui/Eyebrow'
import { WorkspacePreviewPanel } from './WorkspacePreviewPanel'
import styles from './HeroSection.module.css'

export function HeroSection() {
  const prototypeIsLive =
    projectConfig.PROTOTYPE_STATUS !== 'in-development' && projectConfig.PROTOTYPE_URL

  return (
    <div className={styles.hero} id="top">
      <div className={styles.grid}>
        <div className={styles.copy}>
          <div className={styles.eyebrowRow}>
            <Eyebrow>LEGAL METROLOGY · SIH 2026 · PS 26034</Eyebrow>
          </div>
          <h1 className={styles.heading}>{projectConfig.PROJECT_NAME}</h1>
          <p className={styles.subheading}>Evidence-led Legal Metrology inspection</p>
          <p className={styles.supporting}>
            Assists field officers in capturing package evidence, screening declarations,
            measuring printed text when evidence permits, and recording reviewable findings.
          </p>
          <div className={styles.ctaRow}>
            {prototypeIsLive ? (
              <Button as="a" href={projectConfig.PROTOTYPE_URL ?? undefined} variant="primary">
                Open Prototype
              </Button>
            ) : (
              <Button as="a" href="#start-inspection" variant="primary">
                Open Prototype
              </Button>
            )}
            <Button as="a" variant="secondary" href={projectConfig.GITHUB_URL} target="_blank" rel="noopener noreferrer">
              View GitHub
            </Button>
          </div>
        </div>
        <WorkspacePreviewPanel />
      </div>
    </div>
  )
}
