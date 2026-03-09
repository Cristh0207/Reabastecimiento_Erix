import { useState } from 'react'
import './index.css'
import Sidebar from './components/Sidebar'
import WelcomeCard from './components/WelcomeCard'
import Dashboard from './components/Dashboard'
import {
  parseCanastas,
  parseInventarioMensual,
  parseConsumoHistorico,
  processRealPipeline,
  generateDemoData,
  exportToExcel,
} from './services/dataService'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [section, setSection] = useState('indicadores')

  // 3 archivos reales
  const [invFile, setInvFile] = useState(null)
  const [kitFile, setKitFile] = useState(null)
  const [consumoFile, setConsumoFile] = useState(null)

  // Días de proyección
  const [diasProyeccion, setDiasProyeccion] = useState(20)

  /* ---------- Procesar 3 archivos reales (client-side) ---------- */
  const handleProcess = async () => {
    if (!invFile || !kitFile || !consumoFile) return
    setLoading(true)
    setError(null)
    try {
      // 1. Parsear los 3 archivos Excel en el navegador
      const [inventario, canastas, consumo] = await Promise.all([
        parseInventarioMensual(invFile),
        parseCanastas(kitFile),
        parseConsumoHistorico(consumoFile),
      ])

      // 2. Ejecutar pipeline de procesamiento
      const result = processRealPipeline(inventario, canastas, consumo, diasProyeccion)
      setData(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  /* ---------- Demo ---------- */
  const handleDemo = () => {
    setLoading(true)
    setError(null)
    try {
      const result = generateDemoData()
      setData(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  /* ---------- Export ---------- */
  const handleExport = () => {
    if (!data || !data.reorder) return
    exportToExcel(data.reorder)
  }

  return (
    <div className="app-layout">
      {/* Hamburger button (mobile only) */}
      <button
        className="hamburger-btn"
        onClick={() => setSidebarOpen(true)}
        aria-label="Abrir menu"
      >
        <span className="material-symbols-rounded">menu</span>
      </button>

      {/* Overlay */}
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        section={section}
        onSectionChange={setSection}
        invFile={invFile}
        kitFile={kitFile}
        consumoFile={consumoFile}
        onInvFileChange={setInvFile}
        onKitFileChange={setKitFile}
        onConsumoFileChange={setConsumoFile}
        diasProyeccion={diasProyeccion}
        onDiasChange={setDiasProyeccion}
        onProcess={handleProcess}
        onDemo={handleDemo}
        dataLoaded={!!data}
        loading={loading}
      />

      {/* Main */}
      <main className="main-content">
        {loading && (
          <div className="loading-spinner">
            <span className="material-symbols-rounded">progress_activity</span>
            Procesando datos...
          </div>
        )}

        {error && (
          <div style={{
            padding: '1rem', background: '#FEF2F2', color: '#DC2626',
            borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem',
            border: '1px solid #FECACA'
          }}>
            {error}
          </div>
        )}

        {!data && !loading && <WelcomeCard />}

        {data && !loading && (
          <Dashboard
            data={data}
            section={section}
            onExport={handleExport}
          />
        )}

        <footer className="app-footer">
          &copy; 2026 Nostra Sistema de Reabastecimiento. &bull; <b>Powered by Nostra</b> para Clinica Vida.
        </footer>
      </main>
    </div>
  )
}

export default App
