import { useState } from 'react'
import { SectionContainer } from '../layout/SectionContainer'
import { Eyebrow } from '../ui/Eyebrow'
import {
  sampleMeasurementAccepted,
  sampleMeasurementBorderline,
  sampleMeasurementUndersize,
  sampleAbstention,
} from '../../data/sampleInspection'
import { MeasurementResultCard } from './MeasurementResultCard'
import { AbstentionCard } from './AbstentionCard'
import styles from './MeasurementPanelSection.module.css'

type ExampleKey = 'meets' | 'undersize' | 'borderline' | 'abstained'

const EXAMPLES: { key: ExampleKey; label: string }[] = [
  { key: 'meets', label: 'Meets screening threshold' },
  { key: 'undersize', label: 'Potential undersize' },
  { key: 'borderline', label: 'Borderline' },
  { key: 'abstained', label: 'Measurement not established' },
]

export function MeasurementPanelSection() {
  const [active, setActive] = useState<ExampleKey>('meets')

  return (
    <SectionContainer subtle bordered>
      <Eyebrow>MEASUREMENT · SAMPLE RESULTS</Eyebrow>
      <h2 className={styles.heading}>Evidence-bounded measurement</h2>
      <p className={styles.lead}>
        Inspectra reports the visible printed-ink extent when calibration, geometry, and
        image-quality evidence permits it — with a stated uncertainty, not a bare number. When
        conditions are unreliable, it abstains rather than guessing. These are sample results for
        a controlled preview, not a live measurement.
      </p>
      <div className={styles.tabs} role="group" aria-label="Example measurement outcome">
        {EXAMPLES.map((example) => (
          <button
            key={example.key}
            type="button"
            className={active === example.key ? `${styles.tab} ${styles.tabActive}` : styles.tab}
            onClick={() => setActive(example.key)}
            aria-pressed={active === example.key}
          >
            {example.label}
          </button>
        ))}
      </div>

      {active === 'meets' && <MeasurementResultCard result={sampleMeasurementAccepted} />}
      {active === 'undersize' && <MeasurementResultCard result={sampleMeasurementUndersize} />}
      {active === 'borderline' && <MeasurementResultCard result={sampleMeasurementBorderline} />}
      {active === 'abstained' && <AbstentionCard abstention={sampleAbstention} />}

      <div className={styles.terminology}>
        <div className={styles.termCard}>
          <p className={styles.termLabel}>Visible printed-ink extent</p>
          <p className={styles.termText}>
            What is measured — the visible extent of printed ink, not a legally defined character
            height.
          </p>
        </div>
        <div className={styles.termCard}>
          <p className={styles.termLabel}>Measurement when evidence permits</p>
          <p className={styles.termText}>
            A number is only reported when calibration and image-quality gates are satisfied.
          </p>
        </div>
        <div className={styles.termCard}>
          <p className={styles.termLabel}>Physical size screening under controlled conditions</p>
          <p className={styles.termText}>
            Validated so far on a synthetic harness. It does not yet work for every package or
            capture condition.
          </p>
        </div>
      </div>
    </SectionContainer>
  )
}
