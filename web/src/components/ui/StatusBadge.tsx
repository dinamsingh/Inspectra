import type { ReactNode } from 'react'
import styles from './StatusBadge.module.css'

export type StatusTone = 'positive' | 'review' | 'issue' | 'neutral' | 'accent'

interface StatusBadgeProps {
  tone: StatusTone
  children: ReactNode
}

export function StatusBadge({ tone, children }: StatusBadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[tone]}`}>
      <span className={styles.dot} aria-hidden="true" />
      {children}
    </span>
  )
}
