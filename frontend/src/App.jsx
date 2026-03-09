import { useState } from 'react'
import './index.css'
import Sidebar from './components/Sidebar'
import WelcomeCard from './components/WelcomeCard'
import Dashboard from './components/Dashboard'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

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

  /* ---------- Upload & Process (3 archivos reales) ---------- */
  const handleProcess = async () => {
    if (!invFile || !kitFile || !consumoFile) return
    setLoading(true)
    setError(null)
    try {
      // 1. Upload inventario mensual
      const formInv = new FormData()
      formInv.append('file', invFile)
      const resInv = await fetch(`${API_BASE}/api/upload/inventario`, { method: 'POST', body: formInv })
      if (!resInv.ok) throw new Error((await resInv.json()).detail)

      // 2. Upload canastas
      const formKit = new FormData()
      formKit.append('file', kitFile)
      const resKit = await fetch(`${API_BASE}/api/upload/canastas`, { method: 'POST', body: formKit })
      if (!resKit.ok) throw new Error((await resKit.json()).detail)

      // 3. Upload consumo histórico
      const formCon = new FormData()
      formCon.append('file', consumoFile)
      const resCon = await fetch(`${API_BASE}/api/upload/consumo`, { method: 'POST', body: formCon })
      if (!resCon.ok) throw new Error((await resCon.json()).detail)

      // 4. Process con días de proyección
      const resProc = await fetch(
        `${API_BASE}/api/process?dias_proyeccion=${diasProyeccion}`,
        { method: 'POST' }
      )
      if (!resProc.ok) throw new Error((await resProc.json()).detail)
      const result = await resProc.json()
      setData(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  /* ---------- Demo ---------- */
  const handleDemo = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/demo`)
      if (!res.ok) throw new Error('Error generando datos demo')
      const result = await res.json()
      setData(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  /* ---------- Export ---------- */
  const handleExport = async () => {
    const res = await fetch(`${API_BASE}/api/export`)
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const today = new Date().toISOString().split('T')[0]
    const a = document.createElement('a')
    a.href = url
    a.download = `pedido_reabastecimiento_${today}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
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
