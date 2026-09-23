import { SectionContainer } from '../layout/SectionContainer'
import { Eyebrow } from '../ui/Eyebrow'
import { StatusBadge } from '../ui/StatusBadge'
import { pipelineStages } from '../../data/pipelineStages'
import styles from './ProductSection.module.css'

const BUILT: string[] = [
  'Calibrated planar printed-glyph measurement engine',
  'Camera and geometry calibration',
  'Uncertainty budgeting with stated intervals',
  'Abstention / gating state machine (8 gate stages)',
  'Automated test suite — 352 passing tests',
]

const DESIGNED_ONLY: string[] = [
  'Package image capture workflow',
  'Declaration extraction (OCR)',
  'Legal Metrology rule checking',
  'Cross-face contradiction detection',
  'Signed, versioned rule packs',
]

export function ProductSection() {
  return (
    <SectionContainer id="product" bordered>
      <Eyebrow>HOW INSPECTRA WORKS</Eyebrow>
      <h2 className={styles.heading}>Eight stages, one evidence trail</h2>
      <p className={styles.lead}>
        Inspectra follows a fixed pipeline from capture to record. Each stage hands off to the
        next without discarding what came before, so a finding at REPORT can always be traced
        back to the image it started from.
      </p>
      <div className={styles.pipeline} aria-hidden="true">
        {pipelineStages.map((stage, index) => (
          <span key={stage.id} className={styles.stageWrap}>
            <span className={styles.stage}>
              <span className={styles.stageOrder}>{String(stage.order).padStart(2, '0')}</span>
              {stage.label}
            </span>
            {index < pipelineStages.length - 1 && <span className={styles.stageArrow}>→</span>}
          </span>
        ))}
      </div>

      <div className={styles.boundaryGrid}>
        <div className={styles.boundaryCard}>
          <div className={styles.boundaryHeading}>
            <StatusBadge tone="positive">BUILT</StatusBadge>
            <span>Engine, tested against a synthetic harness</span>
          </div>
          <ul className={styles.boundaryList}>
            {BUILT.map((item) => (
              <li key={item} className={styles.boundaryItem}>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <div className={styles.boundaryCard}>
          <div className={styles.boundaryHeading}>
            <StatusBadge tone="neutral">DESIGNED, NOT BUILT</StatusBadge>
            <span>Specified in the architecture, no code yet</span>
          </div>
          <ul className={styles.boundaryList}>
            {DESIGNED_ONLY.map((item) => (
              <li key={item} className={styles.boundaryItem}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </SectionContainer>
  )
}
