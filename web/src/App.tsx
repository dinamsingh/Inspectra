import { SiteHeader } from './components/layout/SiteHeader'
import { SiteFooter } from './components/layout/SiteFooter'
import { HeroSection } from './components/hero/HeroSection'
import { PrototypeStatusBanner } from './components/status/PrototypeStatusBanner'
import { ProductSection } from './components/product/ProductSection'
import { StartInspectionSection } from './components/workspace/StartInspectionSection'
import { MeasurementPanelSection } from './components/measurement/MeasurementPanelSection'
import { EvidenceSection } from './components/evidence/EvidenceSection'
import { ValidationSection } from './components/validation/ValidationSection'
import { ResourcesSection } from './components/resources/ResourcesSection'

function App() {
  return (
    <>
      <SiteHeader />
      <main>
        <HeroSection />
        <PrototypeStatusBanner />
        <ProductSection />
        <StartInspectionSection />
        <MeasurementPanelSection />
        <EvidenceSection />
        <ValidationSection />
        <ResourcesSection />
      </main>
      <SiteFooter />
    </>
  )
}

export default App
