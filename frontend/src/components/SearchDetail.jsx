import { useState, useMemo } from 'react'


export default function SearchDetail({ rows }) {
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedMed, setSelectedMed] = useState(null)
    const [isDropdownOpen, setIsDropdownOpen] = useState(false)

    // Filtrar opciones para el autocompletado (dropdown)
    const filteredOptions = useMemo(() => {
        if (!searchTerm) return []
        const q = searchTerm.toLowerCase()
        return rows.filter(r =>
            r.codigo?.toLowerCase().includes(q) ||
            r.nombre?.toLowerCase().includes(q)
        ).slice(0, 15) // Max 15 resultados
    }, [rows, searchTerm])

    const handleSelect = (med) => {
        setSelectedMed(med)
        setSearchTerm(`${med.codigo} - ${med.nombre}`)
        setIsDropdownOpen(false)
    }

    const handleChange = (e) => {
        setSearchTerm(e.target.value)
        setIsDropdownOpen(true)
        if (e.target.value === '') {
            setSelectedMed(null)
        }
    }

    // Adaptar metadatos para las KpiCards individuales
    const individualKpis = useMemo(() => {
        if (!selectedMed) return []

        return [
            {
                label: 'Inventario Actual',
                value: selectedMed.stock_actual,
                icon: 'warehouse'
            },
            {
                label: 'Comprometido en Kits',
                value: selectedMed.cantidad_comprometida,
                icon: 'vaccines'
            },
            {
                label: 'Stock Disponible',
                value: selectedMed.stock_disponible,
                icon: 'check_circle'
            },
            {
                label: 'Consumo Promedio/Día',
                value: typeof selectedMed.consumo_promedio_diario === 'number'
                    ? selectedMed.consumo_promedio_diario.toFixed(2)
                    : selectedMed.consumo_promedio_diario,
                icon: 'show_chart'
            },
            {
                label: 'Cobertura (Días)',
                value: selectedMed.cobertura_dias >= 9999 ? '∞' : selectedMed.cobertura_dias,
                icon: 'calendar_month'
            },
            {
                label: 'A Pedir',
                value: selectedMed.cantidad_a_pedir,
                icon: 'shopping_cart',
                risk: selectedMed.estado_riesgo === 'Reabastecer'
            }
        ]
    }, [selectedMed])

    return (
        <div className="search-detail-container fade-in" style={{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            background: 'var(--bg-card)',
            borderRadius: '10px',
            boxShadow: 'var(--shadow-sm)',
            padding: '1.5rem',
            overflowY: 'auto'
        }}>
            {/* Header del Buscador */}
            <div style={{ flexShrink: 0, marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.1rem', color: 'var(--cv-navy)', marginBottom: '0.5rem' }}>
                    Buscador de Medicamento Individual
                </h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                    Escriba el código o nombre del producto para visualizar su información logística detallada en formato de tarjetas.
                </p>

                {/* Input Autocompletado */}
                <div style={{ position: 'relative', maxWidth: '600px' }}>
                    <div style={{ position: 'relative' }}>
                        <span
                            className="material-symbols-rounded"
                            style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-light)', fontSize: '1.2rem' }}
                        >
                            search
                        </span>
                        <input
                            type="text"
                            className="search-input"
                            style={{ paddingLeft: '2.5rem', marginBottom: 0, width: '100%' }}
                            placeholder="Buscar por código o nombre..."
                            value={searchTerm}
                            onChange={handleChange}
                            onFocus={() => setIsDropdownOpen(true)}
                        />
                    </div>

                    {/* Lista flotante */}
                    {isDropdownOpen && filteredOptions.length > 0 && (
                        <ul style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            background: 'white',
                            border: '1px solid #E2E8F0',
                            borderRadius: '8px',
                            boxShadow: 'var(--shadow-md)',
                            marginTop: '0.4rem',
                            maxHeight: '250px',
                            overflowY: 'auto',
                            zIndex: 10,
                            listStyle: 'none',
                            padding: '0.5rem 0'
                        }}>
                            {filteredOptions.map(opt => (
                                <li
                                    key={opt.codigo}
                                    style={{
                                        padding: '0.6rem 1rem',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem',
                                        borderBottom: '1px solid #f1f5f9'
                                    }}
                                    onClick={() => handleSelect(opt)}
                                    className="dropdown-item"
                                >
                                    <strong>{opt.codigo}</strong> — {opt.nombre}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>

            {/* Resultado (Tarjetas) */}
            {selectedMed ? (
                <div className="fade-in">
                    <div style={{
                        padding: '1rem',
                        background: selectedMed.estado_riesgo === 'Reabastecer' ? 'rgba(220, 38, 38, 0.05)' : 'rgba(22, 163, 74, 0.05)',
                        borderLeft: `4px solid ${selectedMed.estado_riesgo === 'Reabastecer' ? 'var(--danger)' : 'var(--success)'}`,
                        borderRadius: '0 8px 8px 0',
                        marginBottom: '1.5rem'
                    }}>
                        <h3 style={{ fontSize: '1.2rem', color: 'var(--cv-navy)', marginBottom: '0.2rem' }}>
                            {selectedMed.nombre}
                        </h3>
                        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                            <span>CÓDIGO: {selectedMed.codigo}</span>
                            <span style={{ color: selectedMed.estado_riesgo === 'Reabastecer' ? 'var(--danger)' : 'var(--success)' }}>
                                ESTADO: {selectedMed.estado_riesgo.toUpperCase()}
                            </span>
                        </div>
                    </div>

                    {/* Renderizamos las KpiCards individuales in-line para no interferir con el componente global acoplado al resumen */}
                    <div className="kpi-grid">
                        {individualKpis.map((c, i) => (
                            <div
                                key={c.label}
                                className={`kpi-card ${c.risk ? 'risk' : ''}`}
                                style={{ animationDelay: `${i * 0.08}s` }}
                            >
                                <div className="kpi-header">
                                    <div className="kpi-label">{c.label}</div>
                                    <div className="kpi-icon-wrapper">
                                        <span className="material-symbols-rounded" style={{ fontSize: '1.4rem' }}>
                                            {c.icon}
                                        </span>
                                    </div>
                                </div>
                                <div className="kpi-value">{c.value}</div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-light)',
                    border: '2px dashed #E2E8F0',
                    borderRadius: '8px',
                    padding: '2rem',
                    textAlign: 'center'
                }}>
                    <span className="material-symbols-rounded" style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.5 }}>
                        manage_search
                    </span>
                    <p>No ha seleccionado ningún medicamento.<br /> Utilice la barra de búsqueda superior.</p>
                </div>
            )}
        </div>
    )
}
