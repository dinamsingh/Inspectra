import type { HTMLAttributes, ReactNode } from 'react'
import styles from './SectionContainer.module.css'

interface SectionContainerProps extends HTMLAttributes<HTMLElement> {
  id?: string
  width?: 'narrow' | 'wide'
  subtle?: boolean
  bordered?: boolean
  children: ReactNode
}

export function SectionContainer({
  id,
  width = 'wide',
  subtle = false,
  bordered = false,
  className,
  children,
  ...props
}: SectionContainerProps) {
  const classes = [
    styles.section,
    subtle ? styles.subtle : '',
    bordered ? styles.bordered : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <section id={id} className={classes} {...props}>
      <div className={styles[width]}>{children}</div>
    </section>
  )
}
