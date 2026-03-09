import { useMemo, useState } from 'react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    ScatterChart, Scatter, ZAxis, AreaChart, Area, ComposedChart, Line
} from 'recharts'

export default function Charts({ data, type }) {
    const { reorder = [] } = data
    const [chartTab, setChartTab] = useState('pareto')

    // Custom tooltip genérico elegante
    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ backgroundColor: '#fff', border: '1px solid #E2E8F0', padding: '12px', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}>
                    <p style={{ margin: '0 0 4px 0', fontWeight: 800, fontSize: '0.85rem', color: 'var(--cv-navy-dark)' }}>{payload[0].payload.fullNombre}</p>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Val: <span style={{ fontWeight: 800, color: payload[0].color || 'var(--cv-navy)' }}>{payload[0].value}</span>
                    </p>
                </div>
            );
        }
        return null;
    };

    /** =========== LOGICAS PARA INDICADORES CLAVE (TOP 5) =========== **/
    const top5Pedidos = useMemo(() =>
        [...reorder]
            .filter(r => r.cantidad_a_pedir > 0)
            .sort((a, b) => b.cantidad_a_pedir - a.cantidad_a_pedir)
            .slice(0, 5)
            .map(r => ({
                name: (r.nombre || r.codigo)?.substring(0, 20) + '...',
                value: r.cantidad_a_pedir,
                fullNombre: r.nombre
            }))
        , [reorder])

    const top5Consumo = useMemo(() =>
        [...reorder]
            .filter(r => r.consumo_promedio_diario > 0)
            .sort((a, b) => b.consumo_promedio_diario - a.consumo_promedio_diario)
            .slice(0, 5)
            .map(r => ({
                name: (r.nombre || r.codigo)?.substring(0, 20) + '...',
                value: Math.round(r.consumo_promedio_diario * 100) / 100,
                fullNombre: r.nombre
            }))
        , [reorder])

    /** =========== LOGICAS PARA VISUALIZACIONES COMPLETAS =========== **/
    // Scatter: Riesgo vs Consumo
    const scatterData = useMemo(() =>
        reorder
            .filter(r => r.consumo_promedio_diario > 0 && r.cobertura_dias < 30)
            .map(r => ({
                x: Math.round(r.consumo_promedio_diario),
                y: r.cobertura_dias || 0,
                z: r.cantidad_a_pedir || 0,
                fullNombre: r.nombre,
                riesgo: r.estado_riesgo
            }))
        , [reorder])

    // Pareto
    const paretoData = useMemo(() => {
        let sorted = [...reorder]
            .filter(r => r.cantidad_a_pedir > 0)
            .sort((a, b) => b.cantidad_a_pedir - a.cantidad_a_pedir)
            .slice(0, 30);

        let total = sorted.reduce((sum, item) => sum + item.cantidad_a_pedir, 0);
        let acumulado = 0;

        return sorted.map(r => {
            acumulado += r.cantidad_a_pedir;
            return {
                name: (r.nombre || r.codigo)?.substring(0, 18) + '...',
                fullNombre: r.nombre,
                cantidad: r.cantidad_a_pedir,
                porcentaje: Math.round((acumulado / total) * 100)
            }
        });
    }, [reorder])

    /** ============================================================== **/

    if (type === 'kpis') {
        return (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1rem' }}>
                {/* Top 5 Consumo Diario */}
                <div className="chart-card fade-in">
                    <div className="chart-title" style={{ fontSize: '1rem', borderBottom: '2px solid var(--cv-navy-light)', paddingBottom: '0.4rem', marginBottom: '0.4rem' }}>
                        Top 5 Mayor Consumo Diario
                    </div>
                    {top5Consumo.length > 0 ? (
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={top5Consumo} layout="vertical" margin={{ left: 10, right: 30, top: 0, bottom: 5 }} barCategoryGap="20%">
                                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                                <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--text-light)' }} />
                                <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 10, fontWeight: 600, fill: 'var(--cv-navy)' }} />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(43,76,126,0.05)' }} />
                                <Bar dataKey="value" fill="var(--cv-navy-light)" radius={[0, 8, 8, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-light)' }}>Sin datos suficientes</div>
                    )}
                </div>

                {/* Top 5 Urgencia a Pedir */}
                <div className="chart-card fade-in" style={{ animationDelay: '0.1s' }}>
                    <div className="chart-title" style={{ fontSize: '1rem', borderBottom: '2px solid var(--danger)', paddingBottom: '0.4rem', color: 'var(--danger)', marginBottom: '0.4rem' }}>
                        Top 5 Urgencia de Abastecimiento
                    </div>
                    {top5Pedidos.length > 0 ? (
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={top5Pedidos} layout="vertical" margin={{ left: 10, right: 30, top: 0, bottom: 5 }} barCategoryGap="20%">
                                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                                <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--text-light)' }} />
                                <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 10, fontWeight: 600, fill: 'var(--cv-navy)' }} />
                                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(220,38,38,0.05)' }} />
                                <Bar dataKey="value" fill="var(--danger)" radius={[0, 8, 8, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-light)' }}>Sin datos suficientes</div>
                    )}
                </div>
            </div>
        )
    }

    if (type === 'charts') {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '2rem' }}>
                <div style={{ padding: '1rem', background: 'var(--cv-navy-dark)', color: 'white', borderRadius: '12px' }}>
                    <h2 style={{ fontSize: '1.2rem', margin: '0 0 0.5rem 0' }}>Análisis Avanzado de Inventario</h2>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
                        Visualizaciones gerenciales para identificar cuellos de botella y concentraciones de riesgo.
                    </p>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        onClick={() => setChartTab('pareto')}
                        style={{
                            padding: '0.6rem 1.2rem',
                            borderRadius: '8px',
                            border: 'none',
                            fontFamily: 'Inter, sans-serif',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            background: chartTab === 'pareto' ? 'var(--cv-navy)' : 'rgba(43,76,126,0.1)',
                            color: chartTab === 'pareto' ? 'white' : 'var(--cv-navy)',
                            transition: 'all 0.2s ease',
                        }}
                    >
                        Curva de Pareto
                    </button>
                    <button
                        onClick={() => setChartTab('scatter')}
                        style={{
                            padding: '0.6rem 1.2rem',
                            borderRadius: '8px',
                            border: 'none',
                            fontFamily: 'Inter, sans-serif',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            background: chartTab === 'scatter' ? 'var(--cv-navy)' : 'rgba(43,76,126,0.1)',
                            color: chartTab === 'scatter' ? 'white' : 'var(--cv-navy)',
                            transition: 'all 0.2s ease',
                        }}
                    >
                        Matriz de Dispersión
                    </button>
                </div>

                {/* Pareto Chart */}
                {chartTab === 'pareto' && (
                    <div className="chart-card fade-in">
                        <div className="chart-title" style={{ fontSize: '1.1rem' }}>Curva de Pareto (Top 30 Productos por Volumen de Pedido)</div>
                        <ResponsiveContainer width="100%" height={400}>
                            <ComposedChart data={paretoData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                <CartesianGrid stroke="#f5f5f5" />
                                <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-45} textAnchor="end" height={80} />
                                <YAxis yAxisId="left" tick={{ fontSize: 11 }} label={{ value: 'Unidades a Pedir', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }} />
                                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} label={{ value: '% Acumulativo', angle: 90, position: 'insideRight', style: { textAnchor: 'middle' } }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar yAxisId="left" dataKey="cantidad" barSize={20} fill="var(--cv-gold)" radius={[4, 4, 0, 0]} />
                                <Line yAxisId="right" type="monotone" dataKey="porcentaje" stroke="var(--cv-navy)" strokeWidth={3} dot={{ r: 4, fill: 'var(--cv-navy)' }} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Scatter Chart */}
                {chartTab === 'scatter' && (
                    <div className="chart-card fade-in">
                        <div className="chart-title" style={{ fontSize: '1.1rem' }}>Matriz de Dispersión: Consumo Diario vs Cobertura (Solo Críticos {'<'} 30 días)</div>
                        <ResponsiveContainer width="100%" height={450}>
                            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" dataKey="x" name="Consumo/día" unit=" un." tick={{ fontSize: 11 }} label={{ value: 'Consumo Promedio Diario', position: 'insideBottom', offset: -10 }} />
                                <YAxis type="number" dataKey="y" name="Cobertura" unit=" días" tick={{ fontSize: 11 }} label={{ value: 'Cobertura (Días)', angle: -90, position: 'insideLeft' }} />
                                <ZAxis type="number" dataKey="z" range={[50, 600]} name="A Pedir" />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
                                    if (active && payload && payload.length) {
                                        const data = payload[0].payload;
                                        return (
                                            <div style={{ backgroundColor: '#fff', border: '1px solid #E2E8F0', padding: '12px', borderRadius: '8px', boxShadow: '0 4px 10px rgba(0,0,0,0.1)' }}>
                                                <p style={{ margin: '0 0 5px 0', fontWeight: 'bold', color: 'var(--cv-navy)' }}>{data.fullNombre}</p>
                                                <p style={{ margin: 0, fontSize: '0.8rem' }}>Consumo/Día: <b>{data.x}</b></p>
                                                <p style={{ margin: 0, fontSize: '0.8rem' }}>Cobertura: <b>{data.y} días</b></p>
                                                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--danger)' }}>A Pedir: <b>{data.z}</b></p>
                                            </div>
                                        )
                                    }
                                    return null;
                                }} />
                                <Scatter name="Productos" data={scatterData} fill="rgba(220, 38, 38, 0.6)" stroke="var(--danger)" strokeWidth={1} />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
        )
    }

    return null;
}
