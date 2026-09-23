import { projectConfig } from '../../config/project'
import { SectionContainer } from '../layout/SectionContainer'
import { Eyebrow } from '../ui/Eyebrow'
import { Button } from '../ui/Button'
import { ResourceLinkCard } from './ResourceLinkCard'
import { DemoVideoPlaceholder } from './DemoVideoPlaceholder'
import styles from './ResourcesSection.module.css'

export function ResourcesSection() {
  const prototypeAvailable =
    projectConfig.PROTOTYPE_STATUS !== 'in-development' && projectConfig.PROTOTYPE_URL

  return (
    <SectionContainer id="resources" bordered>
      <Eyebrow>PROJECT RESOURCES</Eyebrow>
      <h2 className={styles.heading}>Follow the project</h2>
      <div className={styles.grid}>
        <ResourceLinkCard
          label="Source"
          title="GitHub repository"
          description={`${projectConfig.PROJECT_NAME} on GitHub — the measurement engine, spec, and review documents.`}
          action={
            <Button as="a" href={projectConfig.GITHUB_URL} target="_blank" rel="noopener noreferrer" variant="secondary">
              View on GitHub
            </Button>
          }
        />
        <ResourceLinkCard
          label="Prototype"
          title="Open Inspectra Prototype"
          description={
            prototypeAvailable
              ? 'An unstable build of the working prototype.'
              : 'A public prototype build is not available yet. Preview the sample inspection workspace above in the meantime.'
          }
          action={
            prototypeAvailable ? (
              <Button as="a" href={projectConfig.PROTOTYPE_URL ?? undefined} target="_blank" rel="noopener noreferrer" variant="secondary">
                Open Prototype
              </Button>
            ) : (
              <Button as="a" href="#start-inspection" variant="secondary">
                Preview sample inspection
              </Button>
            )
          }
        />
        <div className={styles.demoCard}>
          <p className={styles.demoLabel}>Demo</p>
          <h3 className={styles.demoTitle}>Demo video</h3>
          <DemoVideoPlaceholder />
        </div>
      </div>
    </SectionContainer>
  )
}
