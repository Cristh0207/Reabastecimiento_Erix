import { useState, useMemo } from 'react'

export default function DataTable({ rows, onExport, searchMode = false }) {
    const [search, setSearch] = useState('')
    const [sortCol, setSortCol] = useState(null)
    const [sortDir, setSortDir] = useState('asc')

    const columns = [
        { key: 'codigo', label: 'Codigo' },
        { key: 'nombre', label: 'Producto' },
        { key: 'stock_actual', label: 'Stock', align: 'right' },
        { key: 'cantidad_comprometida', label: 'Comprom.', align: 'right' },
        { key: 'stock_disponible', label: 'Disponible', align: 'right' },
        { key: 'consumo_promedio_diario', label: 'Consumo/dia', align: 'right' },
        { key: 'cobertura_dias', label: 'Cobertura', align: 'right' },
        { key: 'cantidad_a_pedir', label: 'A Pedir', align: 'right' },
        { key: 'estado_riesgo', label: 'Estado' },
    ]

    const filteredRows = useMemo(() => {
        let data = rows
        if (search) {
            const q = search.toLowerCase()
            data = data.filter(r =>
                r.codigo?.toLowerCase().includes(q) ||
                r.nombre?.toLowerCase().includes(q)
            )
        }
        if (sortCol) {
            data = [...data].sort((a, b) => {
                const va = a[sortCol] ?? 0
                const vb = b[sortCol] ?? 0
                if (typeof va === 'string') return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
                return sortDir === 'asc' ? va - vb : vb - va
            })
        }
        return data
    }, [rows, search, sortCol, sortDir])

    const toggleSort = (col) => {
        if (sortCol === col) {
            setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        } else {
            setSortCol(col)
            setSortDir('asc')
        }
    }

    return (
        <div className="data-table-container fade-in">
            <div className="data-table-header" style={{ flexShrink: 0 }}>
                <div className="data-table-title">
                    {searchMode ? 'Buscador de Medicamento' : 'Tabla de Detalle'}
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-light)', marginLeft: '0.5rem' }}>
                        ({filteredRows.length} productos)
                    </span>
                </div>
                <button className="export-btn" onClick={onExport}>
                    <span className="material-symbols-rounded" style={{ fontSize: '1rem' }}>download</span>
                    Excel
                </button>
            </div>

            {/* Search */}
            <div style={{ padding: '0 1rem 1rem 1rem', flexShrink: 0 }}>
                <input
                    className="search-input"
                    type="text"
                    placeholder="Buscar por codigo o nombre..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                />
            </div>

            {/* Table */}
            <div className="data-table-wrapper">
                <table className="data-table">
                    <thead>
                        <tr>
                            {columns.map(col => (
                                <th
                                    key={col.key}
                                    style={{ textAlign: col.align || 'left' }}
                                    onClick={() => toggleSort(col.key)}
                                >
                                    {col.label}
                                    {sortCol === col.key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {filteredRows.slice(0, 200).map((row, i) => (
                            <tr key={i}>
                                {columns.map(col => (
                                    <td
                                        key={col.key}
                                        style={{ textAlign: col.align || 'left' }}
                                        className={
                                            col.key === 'estado_riesgo'
                                                ? row[col.key] === 'Reabastecer' ? 'status-reabastecer' : 'status-ok'
                                                : ''
                                        }
                                    >
                                        {col.key === 'cobertura_dias' && row[col.key] >= 9999
                                            ? '∞'
                                            : typeof row[col.key] === 'number'
                                                ? row[col.key].toLocaleString()
                                                : row[col.key]
                                        }
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
