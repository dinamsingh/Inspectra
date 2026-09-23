import { useState } from 'react'
import { SectionContainer } from '../layout/SectionContainer'
import { Eyebrow } from '../ui/Eyebrow'
import { StatusBadge } from '../ui/StatusBadge'
import { pipelineStages } from '../../data/pipelineStages'
import { PipelineStepper } from './PipelineStepper'
import { PipelineStageDetail } from './PipelineStageDetail'
import { OfficerReviewNotice } from './OfficerReviewNotice'
import styles from './StartInspectionSection.module.css'

export function StartInspectionSection() {
  const [activeIndex, setActiveIndex] = useState(0)
  const activeStage = pipelineStages[activeIndex]

  return (
    <SectionContainer id="start-inspection" bordered>
      <Eyebrow>PROTOTYPE PREVIEW</Eyebrow>
      <div className={styles.header}>
        <h2 className={styles.heading}>Start Inspection</h2>
        <StatusBadge tone="neutral">Sample inspection · INS-2026-000482</StatusBadge>
      </div>
      <p className={styles.lead}>
        Step through the eight stages of an inspection. Content below is sample data for a
        controlled preview of the intended product — not a live capture or a live backend result.
      </p>
      <div className={styles.card}>
        <PipelineStepper stages={pipelineStages} activeIndex={activeIndex} onSelect={setActiveIndex} />
        <PipelineStageDetail stage={activeStage} />
      </div>
      <div className={styles.noticeRow}>
        <OfficerReviewNotice />
      </div>
    </SectionContainer>
  )
}
