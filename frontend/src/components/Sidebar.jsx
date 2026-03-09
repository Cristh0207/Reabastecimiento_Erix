import { useRef, useState } from 'react'

const NAV_ITEMS = [
    { key: 'indicadores', icon: 'monitoring', label: 'Indicadores Clave' },
    { key: 'buscador', icon: 'search', label: 'Buscador' },
    { key: 'charts', icon: 'bar_chart', label: 'Visualizaciones' },
    { key: 'tabla', icon: 'table_view', label: 'Tabla de Detalle' },
]

export default function Sidebar({
    isOpen, onClose, section, onSectionChange,
    invFile, kitFile, consumoFile,
    onInvFileChange, onKitFileChange, onConsumoFileChange,
    diasProyeccion, onDiasChange,
    onProcess, onDemo, dataLoaded, loading,
}) {
    const invRef = useRef(null)
    const kitRef = useRef(null)
    const consumoRef = useRef(null)

    // Estado local para el input de dias (permite escribir libremente)
    const [diasInput, setDiasInput] = useState(String(diasProyeccion))

    const allFilesReady = invFile && kitFile && consumoFile

    return (
        <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
            {/* Header */}
            <div className="sidebar-header">
                <div className="sidebar-title">
                    <img src="/favicon.png" alt="" style={{ height: '24px', width: '24px', objectFit: 'contain' }} />
                    {dataLoaded ? 'Navegacion' : 'Carga de Datos'}
                </div>
                <button className="sidebar-close" onClick={onClose} aria-label="Cerrar menu">
                    <span className="material-symbols-rounded">chevron_left</span>
                </button>
            </div>

            <div className="sidebar-body">
                {!dataLoaded ? (
                    /* --- Estado: Carga de archivos --- */
                    <>
                        <div className="sidebar-section-label">Cargar Archivos</div>

                        {/* 1. Inventario Mensual */}
                        <div>
                            <div className="file-upload-label">
                                <span className="material-symbols-rounded" style={{ fontSize: '1rem', color: 'var(--cv-gold-light)' }}>
                                    inventory_2
                                </span>
                                Inventario Mensual
                            </div>
                            <div
                                className={`file-upload-zone ${invFile ? 'has-file' : ''}`}
                                onClick={() => invRef.current?.click()}
                            >
                                <input
                                    ref={invRef}
                                    type="file"
                                    accept=".xlsx,.xls"
                                    style={{ display: 'none' }}
                                    onChange={e => onInvFileChange(e.target.files[0])}
                                />
                                {invFile ? (
                                    <span style={{ color: 'var(--success)', fontSize: '0.8rem' }}>
                                        {invFile.name}
                                    </span>
                                ) : (
                                    <>
                                        <span className="material-symbols-rounded" style={{ fontSize: '1.5rem', opacity: 0.4 }}>
                                            upload_file
                                        </span>
                                        <div className="file-upload-hint">Saldos + Entradas + Salidas</div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* 2. Canastas */}
                        <div>
                            <div className="file-upload-label">
                                <span className="material-symbols-rounded" style={{ fontSize: '1rem', color: 'var(--cv-gold-light)' }}>
                                    vaccines
                                </span>
                                Canastas (Reservado)
                            </div>
                            <div
                                className={`file-upload-zone ${kitFile ? 'has-file' : ''}`}
                                onClick={() => kitRef.current?.click()}
                            >
                                <input
                                    ref={kitRef}
                                    type="file"
                                    accept=".xlsx,.xls"
                                    style={{ display: 'none' }}
                                    onChange={e => onKitFileChange(e.target.files[0])}
                                />
                                {kitFile ? (
                                    <span style={{ color: 'var(--success)', fontSize: '0.8rem' }}>
                                        {kitFile.name}
                                    </span>
                                ) : (
                                    <>
                                        <span className="material-symbols-rounded" style={{ fontSize: '1.5rem', opacity: 0.4 }}>
                                            upload_file
                                        </span>
                                        <div className="file-upload-hint">Inventario comprometido en kits</div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* 3. Consumo Histórico */}
                        <div>
                            <div className="file-upload-label">
                                <span className="material-symbols-rounded" style={{ fontSize: '1rem', color: 'var(--cv-gold-light)' }}>
                                    timeline
                                </span>
                                Consumo Histórico
                            </div>
                            <div
                                className={`file-upload-zone ${consumoFile ? 'has-file' : ''}`}
                                onClick={() => consumoRef.current?.click()}
                            >
                                <input
                                    ref={consumoRef}
                                    type="file"
                                    accept=".xlsx,.xls"
                                    style={{ display: 'none' }}
                                    onChange={e => onConsumoFileChange(e.target.files[0])}
                                />
                                {consumoFile ? (
                                    <span style={{ color: 'var(--success)', fontSize: '0.8rem' }}>
                                        {consumoFile.name}
                                    </span>
                                ) : (
                                    <>
                                        <span className="material-symbols-rounded" style={{ fontSize: '1.5rem', opacity: 0.4 }}>
                                            upload_file
                                        </span>
                                        <div className="file-upload-hint">Despachos de los últimos meses</div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Días de proyección */}
                        {allFilesReady && (
                            <div style={{ marginTop: '0.5rem' }}>
                                <div className="file-upload-label">
                                    <span className="material-symbols-rounded" style={{ fontSize: '1rem', color: 'var(--cv-gold-light)' }}>
                                        date_range
                                    </span>
                                    Días a Proyectar
                                </div>
                                <input
                                    type="number"
                                    min="5"
                                    max="90"
                                    value={diasInput}
                                    onChange={e => setDiasInput(e.target.value)}
                                    onBlur={() => {
                                        const val = parseInt(diasInput) || 20
                                        const clamped = Math.max(5, Math.min(90, val))
                                        setDiasInput(String(clamped))
                                        onDiasChange(clamped)
                                    }}
                                    style={{
                                        width: '100%',
                                        padding: '0.6rem 0.8rem',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: 'white',
                                        fontSize: '0.9rem',
                                        fontFamily: 'Inter, sans-serif',
                                        textAlign: 'center',
                                        fontWeight: 700,
                                    }}
                                />
                            </div>
                        )}

                        {/* Procesar (solo si los 3 archivos están listos) */}
                        {allFilesReady && (
                            <button className="demo-btn" onClick={onProcess} disabled={loading} style={{ marginTop: '0.8rem' }}>
                                <span className="material-symbols-rounded">play_arrow</span>
                                Procesar Datos
                            </button>
                        )}

                        {/* Separator */}
                        <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', margin: '0.5rem 0' }} />

                        {/* Demo */}
                        <div className="sidebar-section-label">Explorar Demo</div>
                        <button className="demo-btn" onClick={onDemo} disabled={loading}>
                            <span className="material-symbols-rounded">science</span>
                            Datos de Prueba
                        </button>
                    </>
                ) : (
                    /* --- Estado: Navegación (datos cargados) --- */
                    <>
                        <div className="sidebar-section-label">Secciones</div>
                        <nav className="sidebar-nav">
                            {NAV_ITEMS.map(item => (
                                <button
                                    key={item.key}
                                    className={`sidebar-nav-item ${section === item.key ? 'active' : ''}`}
                                    onClick={() => { onSectionChange(item.key); onClose() }}
                                >
                                    <span className="material-symbols-rounded">{item.icon}</span>
                                    {item.label}
                                </button>
                            ))}
                        </nav>

                        {/* Volver */}
                        <div style={{ marginTop: 'auto', paddingTop: '1rem' }}>
                            <button
                                className="sidebar-nav-item"
                                style={{ color: 'var(--cv-gold)', fontSize: '0.8rem' }}
                                onClick={() => window.location.reload()}
                            >
                                <span className="material-symbols-rounded">arrow_back</span>
                                Volver al Inicio
                            </button>
                        </div>
                    </>
                )}
            </div>
        </aside>
    )
}
