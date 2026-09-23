import { useRef } from 'react'
import type { KeyboardEvent } from 'react'
import type { PipelineStage } from '../../types/inspection'
import styles from './PipelineStepper.module.css'

interface PipelineStepperProps {
  stages: PipelineStage[]
  activeIndex: number
  onSelect: (index: number) => void
}

export function PipelineStepper({ stages, activeIndex, onSelect }: PipelineStepperProps) {
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])

  const focusTab = (index: number) => {
    const wrapped = (index + stages.length) % stages.length
    onSelect(wrapped)
    tabRefs.current[wrapped]?.focus()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault()
        focusTab(index + 1)
        break
      case 'ArrowLeft':
        event.preventDefault()
        focusTab(index - 1)
        break
      case 'Home':
        event.preventDefault()
        focusTab(0)
        break
      case 'End':
        event.preventDefault()
        focusTab(stages.length - 1)
        break
    }
  }

  return (
    <div className={styles.stepper} role="tablist" aria-label="Inspection pipeline stages">
      {stages.map((stage, index) => {
        const selected = index === activeIndex
        return (
          <button
            key={stage.id}
            ref={(el) => {
              tabRefs.current[index] = el
            }}
            role="tab"
            id={`stage-tab-${stage.id}`}
            aria-selected={selected}
            aria-controls={`stage-panel-${stage.id}`}
            tabIndex={selected ? 0 : -1}
            className={selected ? `${styles.step} ${styles.active}` : styles.step}
            onClick={() => onSelect(index)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            <span className={styles.order}>{String(stage.order).padStart(2, '0')}</span>
            <span className={styles.label}>{stage.label}</span>
          </button>
        )
      })}
    </div>
  )
}
