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
                <div class="kpi-label">❖ Total Productos</div>
                <div class="kpi-value">{total_products:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">⊞ Inventario Total</div>
                <div class="kpi-value">{total_stock:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">▪ Comprometido Canastas</div>
                <div class="kpi-value">{total_committed:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">■ Stock Disponible</div>
                <div class="kpi-value">{total_available:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">▸ Total a Pedir</div>
                <div class="kpi-value">{total_to_order:,}</div>
            </div>
            <div class="kpi-card kpi-risk">
                <div class="kpi-label">⟁ En Riesgo</div>
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
def render_main_table(df_reorder: pd.DataFrame) -> None:
    """Render the full interactive data table."""
    st.markdown("### ▤ Tabla de Análisis Completo")

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

    # Filters
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        risk_filter = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "Reabastecer", "OK"],
            key="risk_filter",
        )
    with col_filter2:
        search = st.text_input("⌕ Buscar producto:", key="product_search")

    if risk_filter != "Todos":
        df_display = df_display[df_display["Estado"] == risk_filter]

    if search:
        mask = (
            df_display["Código"].str.contains(search, case=False, na=False)
            | df_display["Nombre"].str.contains(search, case=False, na=False)
        )
        df_display = df_display[mask]

    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        column_config={
            "Estado": st.column_config.TextColumn(
                "Estado",
                help="OK = cobertura >= 20 días | Reabastecer = cobertura < 20 días",
            ),
        },
    )

    st.caption(f"Mostrando {len(df_display)} de {len(df_reorder)} productos")


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def render_charts(df_reorder: pd.DataFrame) -> None:
    """Render the three main visualizations."""

    # Color palette — Clínica Vida brand
    color_primary = "#2B4C7E"
    color_secondary = "#DC2626"
    color_accent = "#5B8DB8"
    color_warning = "#E8B931"
    color_success = "#16A34A"

    st.markdown("### ◧ Visualizaciones")

    # --- Chart 1: Top 20 products to reorder ---
    tab1, tab2, tab3 = st.tabs([
        "▴ Top 20 a Pedir",
        "◿ Distribución Cobertura",
        "◧ Stock vs Proyección",
    ])

    with tab1:
        top20 = (
            df_reorder.nlargest(20, "cantidad_a_pedir")
            .sort_values("cantidad_a_pedir", ascending=True)
        )

        if top20["cantidad_a_pedir"].sum() > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=top20["nombre"].str[:35],
                x=top20["cantidad_a_pedir"],
                orientation="h",
                marker=dict(
                    color=top20["cantidad_a_pedir"],
                    colorscale=[[0, color_accent], [0.5, color_warning], [1, color_secondary]],
                    line=dict(width=0),
                ),
                text=top20["cantidad_a_pedir"],
                textposition="auto",
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Cantidad a pedir: %{x:,.0f}<br>"
                    "<extra></extra>"
                ),
            ))
            fig.update_layout(
                title="Top 20 Productos con Mayor Cantidad a Pedir",
                xaxis_title="Unidades a Pedir",
                yaxis_title="",
                height=600,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
                margin=dict(l=250),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("■ No hay productos que requieran reabastecimiento.")

    with tab2:
        # Coverage distribution (cap at 60 for readability)
        coverage = df_reorder["cobertura_dias"].replace([np.inf], 60).clip(upper=60)

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=coverage,
            nbinsx=30,
            marker=dict(
                color=color_primary,
                line=dict(color="white", width=1),
            ),
            hovertemplate="Cobertura: %{x:.0f} días<br>Productos: %{y}<extra></extra>",
        ))

        # Add 20-day threshold line
        fig.add_vline(
            x=20,
            line_dash="dash",
            line_color=color_secondary,
            line_width=2,
            annotation_text="Umbral 20 días",
            annotation_position="top",
        )

        fig.update_layout(
            title="Distribución de Cobertura en Días",
            xaxis_title="Días de Cobertura",
            yaxis_title="Cantidad de Productos",
            height=450,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Stock vs projection for top 30 products by consumption
        top30 = df_reorder.nlargest(30, "consumo_promedio_diario")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top30["nombre"].str[:25],
            y=top30["stock_disponible"],
            name="Stock Disponible",
            marker_color=color_accent,
        ))
        fig.add_trace(go.Bar(
            x=top30["nombre"].str[:25],
            y=top30["proyeccion_20_dias"],
            name="Proyección 20 días",
            marker_color=color_primary,
        ))
        fig.update_layout(
            title="Stock Disponible vs Proyección 20 Días (Top 30 por Consumo)",
            xaxis_title="",
            yaxis_title="Unidades",
            barmode="group",
            height=500,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif"),
            xaxis_tickangle=-45,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Excel Export Button
# ---------------------------------------------------------------------------
def render_export_button(excel_buffer: BytesIO, filename: str) -> None:
    """Render the Excel export download button."""
    st.markdown("---")
    col_exp1, col_exp2, col_exp3 = st.columns([1, 2, 1])
    with col_exp2:
        st.download_button(
            label="⤓ Exportar Pedido Sugerido (.xlsx)",
            data=excel_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )
