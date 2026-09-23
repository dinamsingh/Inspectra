import { SectionContainer } from '../layout/SectionContainer'
import { Eyebrow } from '../ui/Eyebrow'
import { validationMetrics } from '../../data/validationMetrics'
import { SyntheticMetricCard } from './SyntheticMetricCard'
import { PendingValidationNotice } from './PendingValidationNotice'
import styles from './ValidationSection.module.css'

export function ValidationSection() {
  return (
    <SectionContainer subtle bordered>
      <Eyebrow>EVIDENCE &amp; VALIDATION</Eyebrow>
      <h2 className={styles.heading}>What has been tested, and what has not</h2>
      <p className={styles.lead}>
        The measurement engine has been tested against a synthetic harness with 352 automated
        tests. These numbers describe engineering performance under controlled synthetic
        conditions — they are not a legal accuracy claim about physical devices.
      </p>
      <div className={styles.grid}>
        {validationMetrics.map((metric) => (
          <SyntheticMetricCard key={metric.label} metric={metric} />
        ))}
      </div>
      <PendingValidationNotice />
    </SectionContainer>
  )
}
