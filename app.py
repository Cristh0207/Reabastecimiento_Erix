"""
app.py — Punto de entrada principal de la aplicación de Reabastecimiento.

Sistema de Análisis de Inventario y Cálculo Automático de Reabastecimiento.
Bodegas 1185 y 1188 — Modelo de consignación.

Author: Inventory Reorder System
"""

import streamlit as st
import pandas as pd
import base64
from pathlib import Path

from modules.data_loader import load_movements, load_kits
from modules.demo_generator import generate_demo_movements, generate_demo_kits
from modules.inventory_engine import calculate_stock
from modules.consumption_engine import calculate_consumption, calculate_projection
from modules.reorder_engine import calculate_reorder, generate_excel_export, get_export_filename
from modules.dashboard import render_kpis, render_main_table, render_charts, render_export_button


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Reabastecimiento",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Premium CSS — Clínica Vida Corporate Branding
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ===== Google Font ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ===== Root Variables — Clínica Vida Brand ===== */
    :root {
        --cv-navy: #2B4C7E;
        --cv-navy-dark: #1B3A5C;
        --cv-steel: #5B8DB8;
        --cv-steel-light: #8FB8DE;
        --cv-gold: #E8B931;
        --cv-gold-light: #F5D76E;
        --cv-grey-50: #F8FAFB;
        --cv-grey-100: #EEF2F6;
        --cv-grey-200: #DCE3EB;
        --cv-grey-400: #94A3B8;
        --cv-grey-600: #556677;
        --cv-grey-800: #2D3748;
        --bg-primary: #F0F4F8;
        --bg-card: #FFFFFF;
        --accent-gradient: linear-gradient(135deg, var(--cv-navy), var(--cv-steel));
        --gold-gradient: linear-gradient(135deg, var(--cv-gold), var(--cv-gold-light));
        --text-primary: var(--cv-grey-800);
        --text-secondary: var(--cv-grey-600);
        --border-color: var(--cv-grey-200);
        --shadow-card: 0 2px 12px rgba(43, 76, 126, 0.08);
        --shadow-hover: 0 8px 30px rgba(43, 76, 126, 0.15);
        --success: #16A34A;
        --danger: #DC2626;
        --warning: #D97706;
    }

    /* ===== Global ===== */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1400px;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--cv-navy-dark) 0%, var(--cv-navy) 100%);
        border-right: none;
        box-shadow: 4px 0 20px rgba(27, 58, 92, 0.15);
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--cv-steel-light) !important;
    }

    /* ===== Headers ===== */
    .main-title {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }

    .main-subtitle {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.95rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* ===== KPI Grid ===== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1rem;
    }

    @media (max-width: 768px) {
        .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    }

    /* ===== KPI Cards ===== */
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-card);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 128px;
        height: 128px;
        border-top: 3px solid var(--cv-steel);
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        border-top-color: var(--cv-navy);
    }

    .kpi-label {
        color: var(--text-secondary);
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.4rem;
        white-space: nowrap;
    }

    .kpi-value {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.2;
    }

    .kpi-sub {
        color: var(--text-secondary);
        font-size: 0.7rem;
        margin-top: 0.2rem;
    }

    .kpi-risk {
        border-top-color: var(--cv-gold);
    }

    .kpi-risk .kpi-value {
        background: linear-gradient(135deg, var(--warning), var(--danger));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .kpi-risk:hover {
        border-top-color: var(--danger);
    }

    /* ===== Logo ===== */
    .logo-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.5rem;
        margin-bottom: 0.3rem;
        padding: 0.5rem 0;
    }

    .logo-header img {
        height: 52px;
        object-fit: contain;
    }

    .sidebar-logo {
        text-align: center;
        padding: 1.2rem 1rem 0.5rem 1rem;
        background: rgba(255,255,255,0.08);
        border-radius: 0 0 12px 12px;
        margin: 0 0.5rem 0.5rem 0.5rem;
    }

    .sidebar-logo img {
        max-width: 90%;
        height: auto;
        filter: brightness(1.15) contrast(1.05);
    }

    /* ===== Dataframe ===== */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }

    /* ===== Buttons ===== */
    .stDownloadButton > button,
    .stButton > button {
        background: var(--accent-gradient) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.8rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px rgba(43, 76, 126, 0.2) !important;
        position: relative;
        overflow: hidden;
    }

    .stDownloadButton > button:hover,
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px rgba(91, 141, 184, 0.6), 0 0 40px rgba(43, 76, 126, 0.4) !important;
        border-color: var(--cv-steel-light) !important;
    }
    
    /* ===== File Uploader ===== */
    .stFileUploader > div > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }

    .stFileUploader > div > div:hover {
        border-color: var(--cv-gold) !important;
        box-shadow: 0 0 15px rgba(232, 185, 49, 0.3), inset 0 0 10px rgba(232, 185, 49, 0.1) !important;
        background: rgba(255, 255, 255, 0.06) !important;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--cv-grey-100);
        border-radius: 10px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }

    /* ===== Dividers ===== */
    hr {
        border-color: var(--border-color);
    }

    /* ===== File Uploader ===== */
    .stFileUploader {
        border-radius: 12px;
    }

    /* ===== Success / Info boxes ===== */
    .stAlert {
        border-radius: 10px;
    }

    /* ===== Section header (sidebar) ===== */
    .section-header {
        color: var(--cv-gold-light);
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(255,255,255,0.15);
    }

    /* ===== Status badges ===== */
    .badge-ok {
        background: rgba(22, 163, 74, 0.12);
        color: var(--success);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-risk {
        background: rgba(220, 38, 38, 0.12);
        color: var(--danger);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* ===== Gold Accent Bar ===== */
    .gold-bar {
        height: 3px;
        background: var(--gold-gradient);
        border-radius: 2px;
        margin: 0.5rem 0 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Logo Loading
# ---------------------------------------------------------------------------
LOGO_PATH = Path(__file__).parent / "image" / "Propuesta-de-Logo-Clinica-Vida-02-1024x285.png"

def get_logo_base64() -> str:
    """Load and encode the logo as base64 for HTML embedding."""
    if LOGO_PATH.exists():
        data = LOGO_PATH.read_bytes()
        return base64.b64encode(data).decode()
    return ""

logo_b64 = get_logo_base64()




# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "df_movements" not in st.session_state:
    st.session_state.df_movements = None
if "df_kits" not in st.session_state:
    st.session_state.df_kits = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False


# ---------------------------------------------------------------------------
# Sidebar — Data Input
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⊞ Carga de Datos")

    st.markdown('<div class="section-header">Opción 1: Datos de Prueba</div>', unsafe_allow_html=True)

    if st.button("✦ Generar Datos de Prueba", use_container_width=True, type="primary"):
        with st.spinner("Generando datos simulados..."):
            st.session_state.df_movements = generate_demo_movements()
            st.session_state.df_kits = generate_demo_kits(st.session_state.df_movements)
            st.session_state.data_loaded = True
            st.success(f"■ Generados {len(st.session_state.df_movements):,} movimientos y "
                       f"{len(st.session_state.df_kits):,} productos en canastas")

    st.markdown('<div class="section-header">Opción 2: Cargar Archivos</div>', unsafe_allow_html=True)

    uploaded_movements = st.file_uploader(
        "▪ Movimientos de Inventario",
        type=["csv", "xlsx", "xls"],
        help="Columnas: fecha, codigo, nombre, bodega, tipo_movimiento, cantidad",
        key="upload_movements",
    )

    uploaded_kits = st.file_uploader(
        "▪ Canastas (Stock Comprometido)",
        type=["csv", "xlsx", "xls"],
        help="Columnas: codigo, nombre, cantidad_comprometida",
        key="upload_kits",
    )

    if uploaded_movements is not None:
        df_mov, err_mov = load_movements(uploaded_movements)
        if err_mov:
            st.error(f"✕ {err_mov}")
        else:
            st.session_state.df_movements = df_mov
            st.success(f"■ {len(df_mov):,} movimientos cargados")

            if uploaded_kits is not None:
                df_kits, err_kits = load_kits(uploaded_kits)
                if err_kits:
                    st.error(f"✕ {err_kits}")
                else:
                    st.session_state.df_kits = df_kits
                    st.session_state.data_loaded = True
                    st.success(f"■ {len(df_kits):,} productos en canastas cargados")
            else:
                st.warning("⟁ Cargue el archivo de canastas para calcular el pedido.")

    # Info
    st.markdown("---")
    st.markdown("### ℹ Información")
    st.markdown("""
    - **Consumo**: Últimos 90 días
    - **Cobertura**: 20 días
    - **Reabastecimiento**: Quincenal
    - **Bodegas**: 1185 + 1188
    - **Canastas**: Descuenta stock
    """)


# ---------------------------------------------------------------------------
# Main Content — Dashboard
# ---------------------------------------------------------------------------
if st.session_state.data_loaded and st.session_state.df_movements is not None and st.session_state.df_kits is not None:
    try:
        # === Computation Pipeline ===
        with st.spinner("⟳ Calculando análisis de inventario..."):
            # Step 1: Stock
            df_stock = calculate_stock(st.session_state.df_movements)

            # Step 2: Consumption + Projection
            df_consumption = calculate_consumption(st.session_state.df_movements, days=90)
            df_consumption = calculate_projection(df_consumption, coverage_days=20)

            # Step 3: Reorder
            df_reorder = calculate_reorder(df_stock, df_consumption, st.session_state.df_kits)

        # === Render Header + Dashboard ===
        if logo_b64:
            st.markdown(
                f"""<div class="logo-header">
                    <img src="data:image/png;base64,{logo_b64}" alt="Clínica Vida">
                    <div>
                        <div class="main-title" style="text-align:left;font-size:1.9rem;">Sistema de Reabastecimiento</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="main-title">❖ Sistema de Reabastecimiento</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="main-subtitle">Análisis de Inventario &bull; Bodegas 1185 &amp; 1188 &bull; Modelo Consignación</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="gold-bar"></div>', unsafe_allow_html=True)

        # KPIs
        render_kpis(df_reorder)

        st.markdown("---")

        # Charts
        render_charts(df_reorder)

        st.markdown("---")

        # Table
        render_main_table(df_reorder)

        # Export
        excel_buffer = generate_excel_export(df_reorder)
        filename = get_export_filename()
        render_export_button(excel_buffer, filename)

    except Exception as e:
        st.error(f"❌ Error en el procesamiento: {str(e)}")
        st.exception(e)

else:
    # Empty state
    st.markdown("---")
    logo_img = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'style="height:80px;margin-bottom:1.5rem;" '
        f'alt="Clínica Vida">'
    ) if logo_b64 else '<div style="font-size: 4rem; margin-bottom: 1rem;">❖</div>'

    st.markdown(
        f"""
        <div style="text-align: center; padding: 4rem 2rem; background: white; border-radius: 16px; box-shadow: 0 2px 12px rgba(43,76,126,0.08);">
            {logo_img}
            <h2 style="color: #2B4C7E; margin-bottom: 0.5rem;">Bienvenido al Sistema de Reabastecimiento</h2>
            <p style="color: #556677; font-size: 1.05rem; max-width: 600px; margin: 0 auto;">
                Cargue sus archivos de movimientos y canastas desde la barra lateral,
                o genere datos de prueba para explorar el sistema.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
