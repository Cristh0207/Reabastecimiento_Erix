import KpiCards from './KpiCards'
import DataTable from './DataTable'
import Charts from './Charts'
import SearchDetail from './SearchDetail'

export default function Dashboard({ data, section, onExport }) {
    const { kpis, reorder } = data

    return (
        <div className="dashboard-container">
            {/* Header */}
            <div className="dashboard-header fade-in" style={{ flexShrink: 0 }}>
                <img src="/logo.png" alt="Clínica Vida" />
                <div>
                    <h1>Sistema de Reabastecimiento</h1>
                    <div className="subtitle">
                        Clinica Vida — Bodegas 1185 y 1188
                    </div>
                </div>
            </div>

            {/* KPIs (Solo visibles en la sección indicadores) */}
            {section === 'indicadores' && (
                <div style={{ flexShrink: 0 }}>
                    <h2 className="section-title fade-in" style={{ fontSize: '1.2rem', color: 'var(--cv-navy)', marginBottom: '1rem', fontWeight: 700 }}>Resumen de Estado</h2>
                    <KpiCards kpis={kpis} />
                </div>
            )}

            {/* Sección activa */}
            <div className="dashboard-content-area">
                {section === 'tabla' && (
                    <DataTable rows={reorder} onExport={onExport} />
                )}

                {section === 'buscador' && (
                    <SearchDetail rows={reorder} />
                )}

                {section === 'indicadores' && (
                    <Charts data={data} type="kpis" />
                )}

                {section === 'charts' && (
                    <Charts data={data} type="charts" />
                )}
            </div>
        </div>
    )
}
