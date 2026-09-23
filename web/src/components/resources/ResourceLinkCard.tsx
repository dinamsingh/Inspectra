import type { ReactNode } from 'react'
import styles from './ResourceLinkCard.module.css'

interface ResourceLinkCardProps {
  label: string
  title: string
  description: string
  action: ReactNode
}

export function ResourceLinkCard({ label, title, description, action }: ResourceLinkCardProps) {
  return (
    <div className={styles.card}>
      <p className={styles.label}>{label}</p>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.description}>{description}</p>
      <div className={styles.action}>{action}</div>
    </div>
  )
}
