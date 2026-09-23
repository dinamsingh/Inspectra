import type { PipelineStage } from '../../types/inspection'
import styles from './PipelineStageDetail.module.css'

interface PipelineStageDetailProps {
  stage: PipelineStage
}

export function PipelineStageDetail({ stage }: PipelineStageDetailProps) {
  return (
    <div
      role="tabpanel"
      id={`stage-panel-${stage.id}`}
      aria-labelledby={`stage-tab-${stage.id}`}
      tabIndex={0}
      className={styles.panel}
    >
      <p className={styles.summary}>{stage.summary}</p>
      <p className={styles.detail}>{stage.detail}</p>
      <dl className={styles.fields}>
        {stage.sampleFields.map((field) => (
          <div key={field.label} className={styles.field}>
            <dt className={styles.fieldLabel}>{field.label}</dt>
            <dd className={styles.fieldValue}>{field.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
