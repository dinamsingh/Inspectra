import { projectConfig } from '../../config/project'
import { useActiveSection } from '../../hooks/useActiveSection'
import { Button } from '../ui/Button'
import styles from './SiteHeader.module.css'

const NAV_ITEMS = [
  { id: 'product', label: 'Product' },
  { id: 'start-inspection', label: 'How it works' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'resources', label: 'Resources' },
]

export function SiteHeader() {
  const activeId = useActiveSection(NAV_ITEMS.map((item) => item.id))

  return (
    <header className={styles.header}>
      <div className={styles.bar}>
        <a href="#top" className={styles.identity}>
          <span className={styles.wordmark}>{projectConfig.PROJECT_NAME}</span>
          <span className={styles.descriptor}>Legal Metrology inspection assistant</span>
        </a>
        <nav className={styles.nav} aria-label="Primary">
          <ul className={styles.navLinks}>
            {NAV_ITEMS.map((item) => (
              <li key={item.id}>
                <a href={`#${item.id}`} className={activeId === item.id ? 'active' : undefined}>
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
          <Button as="a" href="#start-inspection" variant="primary">
            Start Inspection
          </Button>
        </nav>
      </div>
    </header>
  )
}
