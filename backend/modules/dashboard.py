"""
dashboard.py — Componentes de visualización del dashboard.

Skills:
    - skill_dashboard_builder: Renders KPIs, tables, and charts using Streamlit + Plotly.

Separates all UI rendering from business logic.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from typing import Optional


# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------
def render_kpis(df_reorder: pd.DataFrame) -> None:
    """
    Render the 6 global KPI metric cards.

    Metrics:
        1. Total productos
        2. Inventario total actual
        3. Total comprometido en kits
        4. Stock disponible real total
        5. Total unidades a pedir
        6. % productos en riesgo (cobertura < 20 días)
    """
    total_products = len(df_reorder)
    total_stock = int(df_reorder["stock_actual"].sum())
    total_committed = int(df_reorder["cantidad_comprometida"].sum())
    total_available = int(df_reorder["stock_disponible"].sum())
    total_to_order = int(df_reorder["cantidad_a_pedir"].sum())

    at_risk = (df_reorder["estado_riesgo"] == "Reabastecer").sum()
    risk_pct = round((at_risk / total_products * 100), 1) if total_products > 0 else 0

    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label"><span class="material-symbols-rounded" style="vertical-align: middle; font-size: 1.2em; margin-right: 4px;">inventory_2</span> Total Productos</div>
                <div class="kpi-value">{total_products:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><span class="material-symbols-rounded" style="vertical-align: middle; font-size: 1.2em; margin-right: 4px;">warehouse</span> Inventario Total</div>
                <div class="kpi-value">{total_stock:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><span class="material-symbols-rounded" style="vertical-align: middle; font-size: 1.2em; margin-right: 4px;">work</span> Comprometido Canastas</div>
                <div class="kpi-value">{total_committed:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><span class="material-symbols-rounded" style="vertical-align: middle; font-size: 1.2em; margin-right: 4px;">check_circle</span> Stock Disponible</div>
                <div class="kpi-value">{total_available:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label"><span class="material-symbols-rounded" style="vertical-align: middle; font-size: 1.2em; margin-right: 4px;">local_shipping</span> Total a Pedir</div>
                <div class="kpi-value">{total_to_order:,}</div>
            </div>
            <div class="kpi-card kpi-risk">
                <div class="kpi-label"><span class="material-symbols-rounded" style="vertical-align: middle; font-size: 1.2em; margin-right: 4px;">warning</span> En Riesgo</div>
                <div class="kpi-value">{risk_pct}%</div>
                <div class="kpi-sub">({at_risk} de {total_products})</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main Table
# ---------------------------------------------------------------------------
def render_main_table(df_reorder: pd.DataFrame, excel_buffer: BytesIO = None, filename: str = None) -> None:
    """Render the full interactive data table."""
    
    # Inyectar CSS para limpiar los filtros (evitar fondos muy oscuros o grises)
    st.markdown("""
        <style>
        /* Estilos corporativos y limpios para inputs de Streamlit */
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.7) !important;
            border: 1px solid rgba(43, 76, 126, 0.2) !important;
            border-radius: 6px !important;
            outline: none !important;
        }
        
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
            background-color: transparent !important;
            color: #1A1A1A !important;
        }

        /* Hover y Focus */
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div:hover,
        div[data-testid="stTextInput"] > div[data-baseweb="input"]:hover {
            border-color: rgba(43, 76, 126, 0.5) !important;
        }
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div:focus-within,
        div[data-testid="stTextInput"] > div[data-baseweb="input"]:focus-within {
            border-color: var(--cv-navy) !important;
            box-shadow: 0 0 0 1px var(--cv-navy) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Titulo y Botón de Exportación en la misma fila
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.markdown('<h3 style="margin-top: 0; padding-top: 0;"><span class="material-symbols-rounded" style="vertical-align: bottom;">table_chart</span> Tabla de Análisis Completo</h3>', unsafe_allow_html=True)
    with col_btn:
        if excel_buffer is not None and filename is not None:
            # Re-usar parte del codigo original de exportación de una forma más compacta
            st.download_button(
                label="Exportar Excel", # Reducido para que quepa bien
                data=excel_buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Procesa el pedido sugerido (solo ítems con cantidad_a_pedir > 0).",
                icon=":material/download:",
                type="secondary",
                use_container_width=True,
            )

    display_cols = [
        "codigo",
        "nombre",
        "stock_actual",
        "cantidad_comprometida",
        "stock_disponible",
        "consumo_promedio_diario",
        "proyeccion_20_dias",
        "cobertura_dias",
        "cantidad_a_pedir",
        "estado_riesgo",
    ]

    df_display = df_reorder[display_cols].copy()

    # Replace inf with a readable string for display
    df_display["cobertura_dias"] = df_display["cobertura_dias"].replace(
        [np.inf], "∞"
    )

    # Rename columns for display
    column_labels = {
        "codigo": "Código",
        "nombre": "Nombre",
        "stock_actual": "Stock Actual",
        "cantidad_comprometida": "Comprometido",
        "stock_disponible": "Stock Disponible",
        "consumo_promedio_diario": "Consumo Prom/Día",
        "proyeccion_20_dias": "Proyección 20d",
        "cobertura_dias": "Cobertura (días)",
        "cantidad_a_pedir": "Cant. a Pedir",
        "estado_riesgo": "Estado",
    }
    df_display = df_display.rename(columns=column_labels)

    # Filters - Añadiendo espacio superior e inferior
    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        risk_filter = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "Reabastecer", "OK"],
            key="risk_filter",
        )
    with col_filter2:
        search = st.text_input("Buscar producto:", key="product_search")
    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    if risk_filter != "Todos":
        df_display = df_display[df_display["Estado"] == risk_filter]

    if search:
        mask = (
            df_display["Código"].str.contains(search, case=False, na=False)
            | df_display["Nombre"].str.contains(search, case=False, na=False)
        )
        df_display = df_display[mask]

    # Reducimos la altura a un fijo más amigable a laptops (320px) para anular scroll externo
    st.dataframe(
        df_display,
        use_container_width=True,
        height=320,
        column_config={
            "Estado": st.column_config.TextColumn(
                "Estado",
                help="OK = cobertura >= 20 días | Reabastecer = cobertura < 20 días",
            ),
        },
    )

    st.markdown(
        f'<div style="font-size: 0.8rem; color: #6c757d; margin-top: -5px; padding-bottom: 5px;">Mostrando {len(df_display)} de {len(df_reorder)} productos</div>',
        unsafe_allow_html=True
    )


# ---------------------------------------------------------------------------
# Modal de Detalle de Cobertura
# ---------------------------------------------------------------------------
@st.dialog("📋 Detalle de Cobertura y Riesgo", width="large")
def show_coverage_details(estado: str, df_reorder: pd.DataFrame):
    st.markdown(f"Listado de medicamentos en estado **{estado}**")
    
    if "Crítico" in estado:
        df_filtered = df_reorder[df_reorder["cobertura_dias"] < 10]
    elif "Atención" in estado:
        df_filtered = df_reorder[(df_reorder["cobertura_dias"] >= 10) & (df_reorder["cobertura_dias"] < 20)]
    else:
        df_filtered = df_reorder[df_reorder["cobertura_dias"] >= 20]
        
    cols_to_show = ["codigo", "nombre", "stock_disponible", "consumo_promedio_diario", "cobertura_dias", "cantidad_a_pedir"]
    df_mini = df_filtered[cols_to_show].copy()
    
    st.dataframe(
        df_mini,
        use_container_width=True,
        hide_index=True,
        height=400
    )


# ---------------------------------------------------------------------------
# Modal de Detalle de Tendencia
# ---------------------------------------------------------------------------
@st.dialog("📉 Detalle de Tendencia de Stock", width="large")
def show_trend_details(categoria: str, df: pd.DataFrame):
    st.markdown(f"Listado de medicamentos en tendencia **{categoria}**")
    
    # Recalcular temporalmente ratios para filtrar
    df_temp = df.copy()
    df_temp['ratio_proyeccion'] = np.where(df_temp['proyeccion_20_dias'] > 0, 
                                            df_temp['stock_disponible'] / df_temp['proyeccion_20_dias'], 
                                            np.inf)
    conds = [
        (df_temp['proyeccion_20_dias'] == 0) | (df_temp['ratio_proyeccion'] == np.inf),
        (df_temp['ratio_proyeccion'] < 0.5),
        (df_temp['ratio_proyeccion'] >= 0.5) & (df_temp['ratio_proyeccion'] < 1.0),
        (df_temp['ratio_proyeccion'] >= 1.0)
    ]
    choices = ['Demanda/Stock Atípico', 'Tendencia Crítica (<50%)', 'En Riesgo (50-99%)', 'Saldado (>=100%)']
    df_temp['grupo_tendencia'] = np.select(conds, choices, default='Demanda/Stock Atípico')
    
    df_filtrado = df_temp[df_temp['grupo_tendencia'] == categoria]
    
    if df_filtrado.empty:
        st.info("No hay medicamentos en esta categoría de tendencia.")
        return
        
    cols_to_show = ["codigo", "nombre", "stock_disponible", "proyeccion_20_dias", "estado_riesgo"]
    df_mini = df_filtrado[cols_to_show].copy()
    
    st.dataframe(
        df_mini,
        column_config={
            "codigo": "Código",
            "nombre": "Medicamento",
            "stock_disponible": st.column_config.NumberColumn("Stock Disp.", format="%d"),
            "proyeccion_20_dias": st.column_config.NumberColumn("Proyección 20d", format="%d"),
            "estado_riesgo": "Estado de Riesgo"
        },
        use_container_width=True,
        hide_index=True,
        height=400
    )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def render_charts(df_reorder: pd.DataFrame) -> None:
    """Render the three main visualizations."""

    # Color palette — Clínica Vida brand & Semantics
    color_navy = "#2B4C7E"
    color_steel = "#5B8DB8"
    color_gold = "#E8B931"
    color_success = "#16A34A"
    color_danger = "#DC2626"
    color_bg = "rgba(0,0,0,0)"

    st.markdown('### <span class="material-symbols-rounded" style="vertical-align: bottom;">bar_chart</span> Visualizaciones Integrales', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "Top 10 a Pedir",
        "Cobertura Global",
        "Stock vs Proyección",
    ])

    with tab1:
        st.markdown('<div class="kpi-label" style="margin-bottom: 1rem;">Productos prioritarios por volumen absoluto de abastecimiento</div>', unsafe_allow_html=True)
        # Top 10 a pedir
        top10 = (
            df_reorder.nlargest(10, "cantidad_a_pedir")
            .sort_values("cantidad_a_pedir", ascending=True)
        )

        if top10["cantidad_a_pedir"].sum() > 0:
            # Asignar colores corporativos por umbral
            colors = []
            for val in top10["cantidad_a_pedir"]:
                if val > 300:
                    colors.append(color_navy) # Alta urgencia / volumen
                elif val > 100:
                    colors.append(color_gold) # Media
                else:
                    colors.append(color_steel) # Baja / Base

            fig = go.Figure()
            # Quitamos cornerradius que genera linting errors en versiones específicas de plotly
            fig.add_trace(go.Bar(
                y=top10["nombre"].str[:40],
                x=top10["cantidad_a_pedir"],
                orientation="h",
                marker=dict(
                    color=colors,
                    line=dict(width=0),
                ),
                text=top10["cantidad_a_pedir"],
                textposition="auto",
                textfont=dict(color="white"),
                hovertemplate=(
                    "<b style='font-size: 14px;'>%{y}</b><br><br>"
                    "Unidades a pedir: <b style='color: " + color_gold + "'>%{x:,.0f}</b><br>"
                    "<extra></extra>"
                ),
            ))
            fig.update_layout(
                xaxis_title="Unidades a Pedir",
                yaxis_title="",
                height=420,
                plot_bgcolor=color_bg,
                paper_bgcolor=color_bg,
                font=dict(family="Inter, sans-serif"),
                margin=dict(l=260, t=10, b=40, r=20),
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay productos que requieran reabastecimiento crítico.")

    with tab2:
        st.markdown('<div class="kpi-label" style="margin-bottom: -1rem;">Visión de salud del inventario base. <strong style="color:var(--cv-navy);">Haz clic en un color para ver el listado de productos.</strong></div>', unsafe_allow_html=True)
        # Categorizar cobertura
        cond_critico = df_reorder["cobertura_dias"] < 10
        cond_warning = (df_reorder["cobertura_dias"] >= 10) & (df_reorder["cobertura_dias"] < 20)
        cond_ok = df_reorder["cobertura_dias"] >= 20

        count_critico = cond_critico.sum()
        count_warning = cond_warning.sum()
        count_ok = cond_ok.sum()

        labels = ["Crítico (< 10 días)", "Atención (10-19 días)", "Saludable (>= 20 días)"]
        values = [count_critico, count_warning, count_ok]
        donut_colors = [color_danger, color_gold, color_success]

        fig2 = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            direction='clockwise',
            sort=False,
            marker=dict(colors=donut_colors, line=dict(color='#FFFFFF', width=3)),
            textinfo='percent',
            textfont=dict(size=14, color="white"),
            hoverinfo='label+value+percent',
            hovertemplate="<b>%{label}</b><br>Productos: %{value}<br>Porcentaje: %{percent}<extra></extra>"
        )])

        # Estilización limpia y corporativa (Donut estilo React)
        fig2.update_layout(
            height=420,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.0,
                font=dict(size=13)
            ),
            plot_bgcolor=color_bg,
            paper_bgcolor=color_bg,
            font=dict(family="Inter, sans-serif"),
            margin=dict(t=30, b=30, l=10, r=10),
            annotations=[dict(text=f"<b>{len(df_reorder)}</b><br>Total", x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        # Interacción click -> Modal
        event = st.plotly_chart(fig2, use_container_width=True, on_select="rerun", selection_mode="points", key="donut_chart", config={'displayModeBar': False})
        
        # Si capturamos un click en la dona
        if event and len(event.selection.points) > 0:
            punto_clickeado = event.selection.points[0]
            label_seleccionado = punto_clickeado.get("label", "")
            if label_seleccionado:
                show_coverage_details(label_seleccionado, df_reorder)

    with tab3:
        st.markdown('<div class="kpi-label" style="margin-bottom: 1rem;">Total Stock vs Proyección 20 Días (Agrupado por Tendencia de Cobertura)</div>', unsafe_allow_html=True)
        
        # Clasificar el inventario por su ratio de proyección
        df_reorder['ratio_proyeccion'] = np.where(df_reorder['proyeccion_20_dias'] > 0, 
                                                 df_reorder['stock_disponible'] / df_reorder['proyeccion_20_dias'], 
                                                 np.inf)
        
        conds = [
            (df_reorder['proyeccion_20_dias'] == 0) | (df_reorder['ratio_proyeccion'] == np.inf),
            (df_reorder['ratio_proyeccion'] < 0.5),
            (df_reorder['ratio_proyeccion'] >= 0.5) & (df_reorder['ratio_proyeccion'] < 1.0),
            (df_reorder['ratio_proyeccion'] >= 1.0)
        ]
        choices = ['Demanda/Stock Atípico', 'Tendencia Crítica (<50%)', 'En Riesgo (50-99%)', 'Saldado (>=100%)']
        df_reorder['grupo_tendencia'] = np.select(conds, choices, default='Demanda/Stock Atípico')
        
        # Ordenar lógicamente
        orden_categorias = ['Tendencia Crítica (<50%)', 'En Riesgo (50-99%)', 'Saldado (>=100%)', 'Demanda/Stock Atípico']
        df_reorder['grupo_tendencia'] = pd.Categorical(df_reorder['grupo_tendencia'], categories=orden_categorias, ordered=True)
        
        df_grouped = df_reorder.groupby('grupo_tendencia', observed=False).agg(
            stock_total=('stock_disponible', 'sum'),
            proy_total=('proyeccion_20_dias', 'sum'),
            conteo=('codigo', 'count')
        ).reset_index()

        fig3 = go.Figure()
        
        # Barras
        fig3.add_trace(go.Bar(
            x=df_grouped['grupo_tendencia'],
            y=df_grouped['stock_total'],
            name='Total Stock',
            marker_color=color_navy,
            hovertemplate="Grupo: %{x}<br>Stock: <b>%{y:,.0f}</b> unid.<extra></extra>"
        ))
        
        fig3.add_trace(go.Bar(
            x=df_grouped['grupo_tendencia'],
            y=df_grouped['proy_total'],
            name='Total Proyección',
            marker_color="#E8B931", # Dorado corporate
            hovertemplate="Grupo: %{x}<br>Proyección: <b>%{y:,.0f}</b> unid.<extra></extra>"
        ))
        
        # Líneas de tendencia (sobre las barras)
        fig3.add_trace(go.Scatter(
            x=df_grouped['grupo_tendencia'],
            y=df_grouped['stock_total'],
            name='Línea Tendencia Stock',
            mode='lines+markers',
            line=dict(color=color_navy, width=3, dash='dot'),
            marker=dict(size=8, color=color_navy)
        ))
        
        fig3.add_trace(go.Scatter(
            x=df_grouped['grupo_tendencia'],
            y=df_grouped['proy_total'],
            name='Línea Tendencia Proyección',
            mode='lines+markers',
            line=dict(color="#E8B931", width=3, dash='dot'),
            marker=dict(size=8, color="#E8B931")
        ))

        fig3.update_layout(
            barmode='group',
            height=450,
            plot_bgcolor=color_bg,
            paper_bgcolor=color_bg,
            font=dict(family="Inter, sans-serif"),
            margin=dict(l=20, t=10, b=40, r=20),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", title="Unidades Totales"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.7)"
            ),
            hovermode="x unified"
        )
        
        event3 = st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False}, on_select="rerun", selection_mode="points", key="bar_chart_tendencia")
        
        # Interceptar clic
        if event3 and len(event3.selection.points) > 0:
            punto_clickeado = event3.selection.points[0]
            # Extraer el valor X correspondiente a la selección de la barra (la categoría clickeada)
            categoria_seleccionada = punto_clickeado.get("x", "")
            if categoria_seleccionada:
                show_trend_details(categoria_seleccionada, df_reorder)


# ---------------------------------------------------------------------------
# Excel Export Button
# ---------------------------------------------------------------------------
def render_export_button(excel_buffer: BytesIO, filename: str) -> None:
    """Render the Excel export download button."""
    st.markdown("---")
    col_exp1, col_exp2, col_exp3 = st.columns([1, 2, 1])
    with col_exp2:
        st.download_button(
            label="Exportar Pedido Sugerido (.xlsx)",
            data=excel_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )

# ---------------------------------------------------------------------------
# Explorador Didáctico de Producto
# ---------------------------------------------------------------------------
def render_product_explorer(df_reorder: pd.DataFrame, df_consumption: pd.DataFrame, df_kits: pd.DataFrame) -> None:
    """Visión didáctica de 1 solo medicamento o top 10 críticos."""
    color_navy = "#2B4C7E"
    
    st.markdown('### <span class="material-symbols-rounded" style="vertical-align: bottom;">search</span> Buscador Didáctico', unsafe_allow_html=True)
    st.markdown("Consulta un medicamento específico para ver su Ficha Clínica o revisa los 10 más críticos.")
    
    # Pre-procesamiento de nombres para el buscador
    lista_codigos = df_reorder['codigo'].astype(str) + " - " + df_reorder['nombre'].astype(str)
    
    # Inyectar CSS ligero para el selectbox si no está presente
    st.markdown("""
        <style>
        div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div {
            background-color: rgba(255, 255, 255, 0.7) !important;
            border: 1px solid rgba(43, 76, 126, 0.2) !important;
            border-radius: 6px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    seleccion = st.selectbox(
        "🔎 Selecciona o escribe un medicamento:",
        options=[""] + list(lista_codigos),
        index=0,
        format_func=lambda x: "Escriba para buscar..." if x == "" else x
    )
    
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    if seleccion == "":
        st.info("Utilice el buscador de arriba para consultar el detalle de un medicamento específico.")
    else:
        # Extraer el código real descartando el nombre
        cod_seleccionado = seleccion.split(" - ")[0]
        row_data = df_reorder[df_reorder['codigo'] == cod_seleccionado].iloc[0]
        
        # Evaluar existencia de cantidad_comprometida (blindaje)
        qty_canastas_val = row_data['cantidad_comprometida'] if 'cantidad_comprometida' in row_data else 0
        
        # Calcular stock total físico
        stock_fisico = row_data['stock_actual']
        stock_canastas = qty_canastas_val
        stock_disponible = row_data['stock_disponible']
        consumo_mes = round(row_data['consumo_promedio_diario'] * 30, 1)
        
        # Tarjeta Ficha Clínica
        st.markdown(f"""
        <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid rgba(43, 76, 126, 0.1);">
            <h2 style="color: {color_navy}; margin-top:0;">{row_data['nombre']}</h2>
            <p style="color: #666; font-size: 1.1em; font-family: monospace;">{row_data['codigo']}</p>
            <div style="display: flex; justify-content: space-between; margin-top: 30px; gap: 20px; flex-wrap: wrap;">
                <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid {color_navy};">
                    <h4 style="margin:0 0 15px 0;">📦 Desglose Físico</h4>
                    <p style="margin:5px 0; display:flex; justify-content:space-between;"><span>Stock Físico Total:</span> <strong>{stock_fisico}</strong></p>
                    <p style="margin:5px 0; display:flex; justify-content:space-between; color:#DC2626;"><span>(-) En Canastas Mq:</span> <strong>{stock_canastas}</strong></p>
                    <div style="height:1px; background:#ddd; margin:10px 0;"></div>
                    <p style="margin:5px 0; display:flex; justify-content:space-between; font-size:1.1em;"><span>= Stock Real Usable:</span> <strong style="color:#16A34A;">{stock_disponible}</strong></p>
                </div>
                <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #E8B931;">
                    <h4 style="margin:0 0 15px 0;">⏱️ Operación y Consumo</h4>
                    <p style="margin:5px 0; display:flex; justify-content:space-between;"><span>Consumo Prom/Mensual:</span> <strong>{consumo_mes} unds</strong></p>
                    <p style="margin:5px 0; display:flex; justify-content:space-between;"><span>Consumo Diario:</span> <strong>{round(row_data['consumo_promedio_diario'], 2)}</strong></p>
                    <p style="margin:5px 0; display:flex; justify-content:space-between;"><span>Cobertura Estimada:</span> <strong>{row_data['cobertura_dias'] if row_data['cobertura_dias'] != np.inf else '∞'} días</strong></p>
                </div>
                <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid {'#DC2626' if row_data['estado_riesgo'] == 'Reabastecer' else '#16A34A'}; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                    <h4 style="margin:0 0 10px 0;">Estado Actual</h4>
                    <h2 style="margin:0; color: {'#DC2626' if row_data['estado_riesgo'] == 'Reabastecer' else '#16A34A'};">{row_data['estado_riesgo'].upper()}</h2>
                    <p style="margin-top: 10px; font-size:0.9em;">Recomendación de Pedido:</p>
                    <h3 style="margin:0;">{row_data['cantidad_a_pedir']} unid.</h3>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Análisis Específicos (Canastas y Consumo)
# ---------------------------------------------------------------------------
def render_specific_analysis(df_reorder: pd.DataFrame, df_consumption: pd.DataFrame, df_kits: pd.DataFrame) -> None:
    """Renders separated tabs for detailed Kits and Monthly Consumption."""
    color_navy = "#2B4C7E"
    color_bg = "rgba(0,0,0,0)"
    
    st.markdown('### <span class="material-symbols-rounded" style="vertical-align: bottom;">analytics</span> Análisis Específicos', unsafe_allow_html=True)
    
    t_consumo, t_canastas = st.tabs(["🔥 Top Consumo Mensual", "📦 Stock en Canastas (Bloqueado)"])
    
    with t_consumo:
        st.markdown("Visualiza los medicamentos de mayor rotación mensual. (`consumo_diario * 30`)")
        
        # Calcular consumo mensual aproximado
        df_cons = df_reorder.copy()
        df_cons['consumo_mensual'] = (df_cons['consumo_promedio_diario'] * 30).round(0).astype(int)
        top_cons = df_cons.nlargest(20, 'consumo_mensual').sort_values('consumo_mensual', ascending=True)
        
        if not top_cons.empty and top_cons['consumo_mensual'].sum() > 0:
            fig_cons = go.Figure()
            fig_cons.add_trace(go.Bar(
                y=top_cons["nombre"].str[:40],
                x=top_cons["consumo_mensual"],
                orientation="h",
                marker=dict(color="#D97706", cornerradius=dict(topright=4, bottomright=4)),
                text=top_cons["consumo_mensual"],
                textposition="auto",
                textfont=dict(color="white", weight="bold"),
                hovertemplate="Consumo Mensual: %{x:,.0f} unds<extra></extra>"
            ))
            fig_cons.update_layout(
                height=500,
                xaxis_title="Unidades Consumidas (Mensual Estimado)",
                yaxis_title="",
                plot_bgcolor=color_bg,
                paper_bgcolor=color_bg,
                font=dict(family="Inter, sans-serif"),
                margin=dict(l=260, t=10, b=40, r=20),
            )
            st.plotly_chart(fig_cons, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos de consumo registrados.")
            
    with t_canastas:
        st.markdown("Revisa exactamente qué medicamentos están comprometidos físicamente en canastas.")
        
        # Validar df_kits y cantidad_comprometida
        has_kits_module = True
        if 'cantidad_comprometida' not in df_reorder.columns:
             # Generar columna dummy en tiempo real si falta 
             df_reorder['cantidad_comprometida'] = 0
             has_kits_module = False

        # Filtrar solo si hay stock en canastas
        df_kits_disp = df_reorder[df_reorder['cantidad_comprometida'] > 0][['codigo', 'nombre', 'stock_actual', 'cantidad_comprometida', 'stock_disponible']]
        
        if df_kits_disp.empty or not has_kits_module:
            st.success("¡Excelente! No hay stock comprometido en canastas actualmente detectado en el sistema.")
        else:
            col_chart, col_table = st.columns([1, 1], gap="large")
            
            with col_chart:
                # Treemap de canastas
                fig_tree = px.treemap(
                    df_kits_disp, 
                    path=[px.Constant("Total Canastas"), 'nombre'], 
                    values='cantidad_comprometida',
                    color_discrete_sequence=[color_navy]
                )
                fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=400)
                st.plotly_chart(fig_tree, use_container_width=True, config={'displayModeBar': False})
                
            with col_table:
                # Mini buscador para canastas
                s_kit = st.text_input("Filtrar canastas:", key="search_kits")
                if s_kit:
                    df_kits_disp = df_kits_disp[df_kits_disp['nombre'].str.contains(s_kit, case=False) | df_kits_disp['codigo'].str.contains(s_kit, case=False)]
                
                st.dataframe(
                    df_kits_disp.sort_values('cantidad_comprometida', ascending=False),
                    use_container_width=True,
                    height=330,
                    column_config={
                        "cantidad_comprometida": st.column_config.NumberColumn("En Canastas", format="%d 📦")
                    }
                )
