export default function KpiCards({ kpis }) {
    const cards = [
        { label: 'Total Productos', value: kpis.total_products.toLocaleString(), icon: 'inventory_2' },
        { label: 'Inventario Actual', value: kpis.total_stock.toLocaleString(), icon: 'warehouse' },
        { label: 'Comprometido en Kits', value: kpis.total_committed.toLocaleString(), icon: 'vaccines' },
        { label: 'Stock Disponible', value: kpis.total_available.toLocaleString(), icon: 'check_circle' },
        { label: 'Unidades a Pedir', value: kpis.total_to_order.toLocaleString(), icon: 'shopping_cart' },
        { label: 'Productos en Riesgo', value: `${kpis.risk_pct}%`, icon: 'warning', isRisk: true },
        { label: 'Consumo Paciente (Mes)', value: (kpis.consumo_paciente_mes || 0).toLocaleString(), icon: 'personal_injury' },
        { label: 'Consumo Interno (Mes)', value: (kpis.consumo_interno_total_mes || 0).toLocaleString(), icon: 'local_hospital' },
    ]

    return (
        <div className="kpi-grid">
            {cards.map((c, i) => (
                <div
                    key={c.label}
                    className={`kpi-card ${c.isRisk ? 'risk' : ''}`}
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
    )
}
