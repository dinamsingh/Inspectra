import { SectionContainer } from '../layout/SectionContainer'
import { Eyebrow } from '../ui/Eyebrow'
import { sampleEvidenceRecords } from '../../data/sampleInspection'
import { EvidenceTimeline } from './EvidenceTimeline'
import styles from './EvidenceSection.module.css'

export function EvidenceSection() {
  return (
    <SectionContainer id="evidence" bordered>
      <Eyebrow>EVIDENCE MODEL</Eyebrow>
      <h2 className={styles.heading}>Every finding stays linked to its source</h2>
      <p className={styles.lead}>
        Source image, extracted text, rule result, measurement status, and rule/engine version
        stay linked as one record, so a reviewer can trace any finding back to its evidence.
        Records below are a sample inspection, not a live capture.
      </p>
      <EvidenceTimeline records={sampleEvidenceRecords} />
    </SectionContainer>
  )
}
