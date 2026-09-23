import type { EvidenceRecord } from '../../types/inspection'
import { EvidenceRecordCard } from './EvidenceRecordCard'
import styles from './EvidenceTimeline.module.css'

export function EvidenceTimeline({ records }: { records: EvidenceRecord[] }) {
  return (
    <ol className={styles.list}>
      {records.map((record) => (
        <EvidenceRecordCard key={record.id} record={record} />
      ))}
    </ol>
  )
}
