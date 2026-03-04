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
from PIL import Image

from modules.data_loader import load_movements, load_kits
from modules.demo_generator import generate_demo_movements, generate_demo_kits
from modules.inventory_engine import calculate_stock
from modules.consumption_engine import calculate_consumption, calculate_projection
from modules.reorder_engine import calculate_reorder, generate_excel_export, get_export_filename
from modules.dashboard import (
    render_main_table,
    render_kpis,
    render_charts,
    render_product_explorer,
    render_specific_analysis,
    render_export_button
)


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
favicon = Image.open(Path(__file__).parent / "image" / "Favicon.png")
st.set_page_config(
    page_title="Sistema de Reabastecimiento",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Premium CSS — Clínica Vida Corporate Branding
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ===== Google Font & Material Icons ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

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

    /* ===== Global Viewport Lock & Fixed Footer ===== */
    /* Apagar scrollbars por completo */
    ::-webkit-scrollbar {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }
    * {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }

    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    body, html, [data-testid="stAppViewContainer"] {
        overflow: hidden !important;
        margin: 0;
        padding: 0;
        height: 100vh;
    }
    
    [data-testid="stAppViewBlockContainer"] {
        display: flex;
        flex-direction: column;
        height: 100vh;
        max-height: 100vh;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        position: relative;
        max-width: 1400px;
    }
    
    /* Make internal container perfectly fit without scroll */
    [data-testid="stAppViewBlockContainer"] > div:first-child {
        flex: 1;
        overflow: hidden !important;
        padding-bottom: 0.5rem !important; 
        padding-top: 0.5rem !important;
    }

    /* ===== Responsive dynamic heights for charts & tables using VH ===== */
    /* Anulamos absolutamente el scroll principal nativo de la UI principal de Streamlit */
    section[data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        overflow: hidden !important;
        max-height: 100vh !important;
    }

    /* Aseguramos que la tabla nunca exceda el 45% del viewport para caber junto al header y footer en pantallas críticas. */
    div[data-testid="stDataFrame"], div[data-testid="stDataFrame"] > div:first-child, div[data-testid="stDataFrame"] iframe {
        max-height: 45vh !important;
        overflow-y: hidden !important;
        /* NOTA: No usamos height forzado (ej. height: 48vh) porque fuerza rectángulos rotos. Max-height solo delimita dinámicamente si es necesario */
    }

    div[data-testid="stPlotlyChart"], div[data-testid="stPlotlyChart"] iframe {
        height: 52vh !important;
        min-height: 250px !important;
    }

    .global-footer-container {
        position: absolute;
        bottom: 1rem;
        left: 0;
        width: 100%;
        text-align: center;
        z-index: 9999;
        pointer-events: none;
    }
    
    .element-container:has(.global-footer-container) {
        position: static !important;
    }

    /* ===== Botón Exportar Luminoso Neón Corporativo ===== */
    /* Target genérico a los botones secundarios (como el de descargar) */
    [data-testid="baseButton-secondary"] {
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border: 1px solid var(--cv-navy-light) !important;
        background-color: transparent !important;
        color: var(--cv-navy-dark) !important;
    }
    
    [data-testid="baseButton-secondary"]:hover {
        background-color: var(--cv-navy-dark) !important;
        color: #FFFFFF !important;
        border-color: var(--cv-navy-light) !important;
        /* Efecto Neón Azul Corporativo Intenso */
        box-shadow: 0 0 10px rgba(43, 76, 126, 0.8), 
                    0 0 20px rgba(43, 76, 126, 0.6), 
                    0 0 30px rgba(27, 58, 92, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    [data-testid="baseButton-secondary"]:active {
        box-shadow: 0 0 5px rgba(43, 76, 126, 0.8), 
                    0 0 12px rgba(27, 58, 92, 0.6) !important;
        transform: translateY(1px) scale(0.98) !important;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: var(--cv-navy-dark);
        border-right: none;
        box-shadow: 2px 0 15px rgba(27, 58, 92, 0.15);
    }

    /* Ocultar barra de scroll en el sidebar y forzar inicio desde arriba */
    section[data-testid="stSidebar"] > div {
        overflow: hidden !important;
    }
    
    /* El header superior se oculta globalmente para inmersión */
    [data-testid="stHeader"] {
        display: none !important;
        padding: 0 !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    /* 🔥 El usuario solicitó EXCLUSIVAMENTE la flecha. Restaurar la flecha de expandir (>) como flotante. */
    [data-testid="collapsedControl"] {
        display: flex !important;
        position: fixed !important;
        top: 0.2rem !important;
        left: 0.2rem !important;
        z-index: 999999 !important;
        background: transparent !important;
    }

    /* El header de la barra lateral se mantiene visible para retener la flecha de cerrado (<) */
    [data-testid="stSidebarHeader"] {
        background: transparent !important;
        padding: 1rem 1rem 0 0 !important; /* Mínimo para que la flecha quede en su sitio */
    }

    /* Force sidebar content to be flex and occupy full height */
    [data-testid="stSidebarContent"] {
        display: flex;
        flex-direction: column;
    }

    [data-testid="stSidebarUserContent"] {
        padding-top: 2.5rem !important; /* Ajuste visual superior sidebar */
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 100%;
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFFFFF !important;
        font-size: 1rem !important;
        margin-bottom: 0.2rem !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--cv-steel-light) !important;
        font-size: 0.85rem !important;
    }

    /* ===== Headers ===== */
    .main-title {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.2rem;
        font-weight: 450;
        text-align: center;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
        transition: all 0.3s ease;
    }
    
    h1:hover, h2:hover, h3:hover, .main-title:hover {
        text-shadow: 0 0 15px rgba(226, 179, 93, 0.4);
    }
    
    .sidebar-title {
        color: white;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .main-subtitle {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.8rem;
        font-weight: 400;
        margin-bottom: 0.2rem;
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
        padding: 1vh 0.5vw;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-card);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 14vh;
        height: 14vh;
        border-top: 3px solid var(--cv-steel);
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        border-top-color: var(--cv-navy);
    }

    .kpi-label {
        color: var(--text-secondary);
        font-size: clamp(0.65rem, 1.2vh, 0.8rem);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.3vh;
        white-space: nowrap;
    }

    .kpi-value {
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: clamp(1.4rem, 3.5vh, 2rem);
        font-weight: 800;
        line-height: 1.1;
    }

    .kpi-sub {
        color: var(--text-secondary);
        font-size: clamp(0.55rem, 1vh, 0.7rem);
        margin-top: 0.2vh;
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

    /* ===== Logo & Header Main Title Alingment ===== */
    /* Empujar hacia arriba forzando visibilidad en el borde superior del viewport */
    .stApp > header {
        display: none !important;
        height: 0px !important;
    }

    /* Container base que Streamlit inyecta arriba del contenido */
    /* Quitamos el padding top gigante por defecto (aprox 6rem) */
    .block-container,
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin-top: 0 !important; 
    }

    /* También quitamos cualquier espacio del primer hijo */
    .block-container > div:first-child,
    [data-testid="stAppViewBlockContainer"] > div:first-child {
        padding-top: 0.5rem !important;
        margin-top: 0.5rem !important; /* Empezando completamente en neutro 0 desde el recorte global absoluto */
    }

    .logo-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
        margin-top: 0rem !important; /* Neutro base para ganar la pequeña bajada natural */
        margin-bottom: 0.5rem;
        padding: 0 !important;
    }

    .logo-header img {
        height: 38px; /* Recobrable tamaño normal ya que hay espacio */
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
    
    /* ===== Hover Glows ===== */
    .kpi-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .kpi-card:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 30px rgba(226, 179, 93, 0.3), 0 0 15px rgba(226, 179, 93, 0.2) !important;
        border-color: var(--cv-gold-light) !important;
    }
    .kpi-card:hover .material-symbols-rounded {
        text-shadow: 0 0 10px rgba(226, 179, 93, 0.6);
        color: var(--cv-gold-light);
    }
    
    [data-testid="stTooltipIcon"] svg {
        color: white !important;
        opacity: 0.9 !important;
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
    
    /* ===== File Uploader (Supabase Inspired) ===== */
    [data-testid="stFileUploader"] {
        margin-bottom: -0.5rem;
    }
    
    [data-testid="stFileUploader"] label {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.2rem !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(255, 255, 255, 0.015) !important;
        border: 1px dashed rgba(255, 255, 255, 0.15) !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.5rem !important;
        transition: all 0.2s ease !important;
        min-height: auto !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.2rem !important;
        text-align: center !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        background-color: rgba(255, 255, 255, 0.04) !important;
        border-color: var(--cv-steel-light) !important;
        box-shadow: 0 0 10px rgba(91, 141, 184, 0.15) !important;
    }

    [data-testid="stFileUploaderDropzone"] svg {
        display: block !important;
        width: 20px !important;
        height: 20px !important;
        margin: 0 auto 0 auto !important;
        color: var(--cv-steel-light) !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] > div:nth-child(2) {
        display: none !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"] > div:first-child {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 0.70rem !important;
        margin-top: 0 !important;
        text-align: center !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "Límite: 200MB • CSV / Excel" !important;
        font-size: 0.65rem !important;
        color: rgba(255, 255, 255, 0.4) !important;
        margin-top: 0 !important;
        display: block !important;
        text-align: center !important;
        width: 100% !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.75) !important;
        padding: 0 0.5rem !important;
        margin: 0 auto !important;
        align-self: center !important;
        min-height: 22px !important;
        line-height: 1 !important;
        font-size: 0.65rem !important;
        border-radius: 4px !important;
        font-weight: 400 !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
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
    [data-testid="stAlert"], .stAlert {
        border-radius: 6px !important;
        padding: 0.4rem 0.6rem !important;
        min-height: auto !important;
        display: flex !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }
    .stAlert > div, [data-testid="stAlert"] > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        gap: 0.5rem !important;
    }
    .stAlert p {
        font-size: 0.8rem !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    .stAlert [data-testid="stIconMaterial"] {
        font-size: 1.1rem !important;
    }
    
    /* ===== Primary Button Styling ===== */
    [data-testid="baseButton-primary"] {
        min-height: 28px !important;
        height: 28px !important;
        padding: 0 0.5rem !important;
    }
    [data-testid="baseButton-primary"] p {
        font-size: 0.75rem !important;
        margin: 0 !important;
    }
    [data-testid="baseButton-primary"] span.material-symbols-rounded {
        font-size: 1rem !important;
    }
    
    /* ===== Spinner Status ===== */
    [data-testid="stSpinner"] p {
        color: #FFFFFF !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
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

    /* ===== Sidebar Primary Buttons — Gold Corporate Style (Global) ===== */
    div[data-testid="stSidebar"] button[kind="primary"],
    div[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
    section[data-testid="stSidebar"] button[kind="primary"],
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
        background-color: var(--cv-gold) !important;
        background: var(--cv-gold) !important;
        color: var(--cv-navy-dark) !important;
        border: 0 solid transparent !important;
        font-weight: 600 !important;
        box-shadow: 0 0 15px rgba(226, 179, 93, 0.3) !important;
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
    }

    div[data-testid="stSidebar"] button[kind="primary"] p,
    div[data-testid="stSidebar"] button[data-testid="baseButton-primary"] p,
    section[data-testid="stSidebar"] button[kind="primary"] p,
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] p {
        color: var(--cv-navy-dark) !important;
    }

    div[data-testid="stSidebar"] button[kind="primary"]:hover,
    div[data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover,
    section[data-testid="stSidebar"] button[kind="primary"]:hover,
    section[data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover {
        background-color: var(--cv-gold-light) !important;
        background: var(--cv-gold-light) !important;
        box-shadow: 0 0 20px rgba(226, 179, 93, 0.5) !important;
        transform: translateY(-2px) !important;
        border: 0 solid transparent !important;
    }

    /* ===== RESPONSIVIDAD UNIVERSAL (Móviles, Tablets, Pantallas Reducidas) ===== */
    @media screen and (max-width: 1024px) {
        /* 1. Reactivar el scroll normal general a nivel global de HTML/BODY */
        body, html, 
        [data-testid="stAppViewContainer"], 
        section[data-testid="stMain"], 
        [data-testid="stMainBlockContainer"] {
            overflow-y: auto !important;
            height: auto !important;
            max-height: none !important;
        }
        
        /* Permitir que el content bloque fluya libremente */
        [data-testid="stAppViewBlockContainer"] {
            height: auto !important;
            max-height: none !important;
            padding-bottom: 3rem !important; /* Espacio mínimo final */
        }

        /* 2. Quitar restricciones de altura extremas y fijas para tablas y gráficos */
        div[data-testid="stDataFrame"], 
        div[data-testid="stDataFrame"] > div:first-child, 
        div[data-testid="stDataFrame"] iframe {
            max-height: 70vh !important;
            min-height: 480px !important;
            overflow-y: auto !important;
        }

        div[data-testid="stPlotlyChart"], 
        div[data-testid="stPlotlyChart"] iframe {
            height: auto !important;
            min-height: 380px !important;
        }

        /* 3. Ajustar paddings excesivos en pantallas más pequeñas */
        .block-container,
        [data-testid="stAppViewBlockContainer"] {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 4rem !important; 
        }
        
        .global-footer-container {
            position: relative;
            bottom: 0;
            margin-top: 2rem;
            padding-bottom: 1rem;
        }
    }

    @media screen and (max-width: 768px) {
        /* Layout Mobile Extremo */
        .kpi-grid {
            grid-template-columns: 1fr;
            gap: 0.8rem;
        }
        
        .kpi-card {
            min-height: 120px;
            height: auto;
            padding: 1.5rem 1rem;
        }
        
        .logo-header img {
            height: 30px; /* Reducir logo en móvil */
        }
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

FAVICON_PATH = Path(__file__).parent / "image" / "Favicon.png"

def get_favicon_base64() -> str:
    """Load and encode the favicon as base64 for HTML embedding."""
    if FAVICON_PATH.exists():
        data = FAVICON_PATH.read_bytes()
        return base64.b64encode(data).decode()
    return ""

favicon_b64 = get_favicon_base64()
favicon_img = f'<img src="data:image/png;base64,{favicon_b64}" style="height:28px; width:28px; object-fit:contain;" alt="Icono">' if favicon_b64 else '<span class="material-symbols-rounded">local_pharmacy</span>'




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
# Sidebar — Data Input / Navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    if not st.session_state.data_loaded:
        st.markdown(f'<div class="sidebar-title">{favicon_img} Carga de Datos</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Cargar Archivos</div>', unsafe_allow_html=True)

        st.markdown('''
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.2rem;">
                <div style="color:white; font-size:0.85rem; display:flex; align-items:center; gap:0.4rem;">
                    <span class="material-symbols-rounded" style="font-size:1.1rem; color:var(--cv-gold-light);">inventory_2</span> Movimientos de Inventario
                </div>
                <span class="material-symbols-rounded" style="color:white; font-size:1.0rem; opacity:0.9; cursor:help;" title="Columnas requeridas: fecha, codigo, nombre, bodega, tipo_movimiento, cantidad">help</span>
            </div>
        ''', unsafe_allow_html=True)
        uploaded_movements = st.file_uploader(
            "Movimientos",
            type=["csv", "xlsx", "xls"],
            help="Columnas requeridas: fecha, codigo, nombre, bodega, tipo_movimiento, cantidad",
            key="upload_movements",
            label_visibility="collapsed"
        )

        st.markdown('''
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem; margin-bottom:0.2rem;">
                <div style="color:white; font-size:0.85rem; display:flex; align-items:center; gap:0.4rem;">
                    <span class="material-symbols-rounded" style="font-size:1.1rem; color:var(--cv-gold-light);">vaccines</span> Canastas (Comprometido)
                </div>
                <span class="material-symbols-rounded" style="color:white; font-size:1.0rem; opacity:0.9; cursor:help;" title="Columnas requeridas: codigo, nombre, cantidad_comprometida">help</span>
            </div>
        ''', unsafe_allow_html=True)
        uploaded_kits = st.file_uploader(
            "Canastas",
            type=["csv", "xlsx", "xls"],
            help="Columnas requeridas: codigo, nombre, cantidad_comprometida",
            key="upload_kits",
            label_visibility="collapsed"
        )

        if uploaded_movements is not None:
            df_mov, err_mov = load_movements(uploaded_movements)
            if err_mov:
                st.error(f"{err_mov}")
            else:
                st.session_state.df_movements = df_mov
                st.toast(f"✓ {len(df_mov):,} movimientos", icon="📦")

                if uploaded_kits is not None:
                    df_kits, err_kits = load_kits(uploaded_kits)
                    if err_kits:
                        st.error(f"{err_kits}")
                    else:
                        st.session_state.df_kits = df_kits
                        st.session_state.data_loaded = True
                        st.session_state.show_success_banner = True
                        st.toast(f"✓ {len(df_kits):,} canastas", icon="💊")
                else:
                    st.warning("⚠️ Falta cargar canastas")

        st.markdown('<div class="section-header" style="margin-top: 1.5rem;">Explorar Demo</div>', unsafe_allow_html=True)
        
        if st.button("Datos de Prueba", icon=":material/experiment:", use_container_width=True, type="primary"):
            with st.spinner("Generando datos..."):
                import time
                time.sleep(1) # Simulate loading time
                st.session_state.df_movements = generate_demo_movements()
                st.session_state.df_kits = generate_demo_kits(st.session_state.df_movements)
                st.session_state.data_loaded = True
                st.session_state.show_success_banner = True
                st.toast("Demo cargada", icon="✅")
                st.rerun()
                
    else:
        # Menú Principal State (Data is loaded)
        st.markdown(f'<div class="sidebar-title">{favicon_img} Menú Principal</div>', unsafe_allow_html=True)
        
        st.markdown('''
            <div style="margin-top: 1.5rem; margin-bottom: 0.5rem;">
                <div style="color:var(--cv-gold-light); font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:1px;">Análisis</div>
            </div>
            <style>
            /* Ocultar el marcador nativo redondeado de fondo en radiogroup de Streamlit */
            section[data-testid="stSidebar"] div[role="radiogroup"] > div {
                display: none !important;
            }
            /* Hide the native radio circles */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
                display: none !important;
            }
            /* Style the radio buttons to look like clean menu items */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label {
                position: relative !important;
                margin: 0.2rem 0 0.2rem 0 !important;
                padding: 0.7rem 1.0rem 0.7rem 0.6rem !important;
                background: transparent !important;
                transition: all 0.3s ease-in-out;
                cursor: pointer;
                display: flex;
                z-index: 1; /* Texto por encima del efecto aura */
                overflow: visible !important;
            }
            /* El aura luminosa como un contenedor píldora estirado absoluto */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label::before {
                content: "";
                position: absolute;
                top: 0; bottom: 0;
                left: 0.5rem; /* Inicia más atrás, dándole respiro al icono */
                right: -100px; /* Extensión grande hacia la derecha para asegurar que se corte justo en el límite con el contenido principal */
                background: transparent;
                border-radius: 6px; /* Curvo en todos los lados */
                z-index: -1;
                transition: all 0.3s ease-in-out;
                pointer-events: none;
            }
            /* Al pasar el ratón o activarlo, la luz surge del contenedor absoluto ::before */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover::before,
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked)::before {
                background: rgba(0, 191, 255, 0.15) !important;
                box-shadow: inset 0 0 20px rgba(0, 191, 255, 0.3) !important;
            }
            /* Al pasar el mouse, el texto se vuelve blanquito radiante */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
                color: #FFFFFF !important;
            }
            /* Al pasar el mouse, el ícono también se enciende en amarillo neón */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p span {
                color: #FFD700 !important;
                font-size: 1.4rem !important;
                text-shadow: 0 0 10px rgba(255, 215, 0, 0.8) !important;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] p {
                color: rgba(255,255,255,0.7) !important;
                font-size: 1.05rem; /* Tamaño más grande y legible */
                font-weight: 500;
                transition: color 0.3s ease, text-shadow 0.3s ease;
                white-space: nowrap !important; /* Impide que el texto se rompa en dos líneas */
            }
            /* Only the icon glows yellow and gets bigger */
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
                color: #FFFFFF !important; /* Blanca normal */
                font-weight: 500;
                text-shadow: none !important;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p span {
                color: #FFD700 !important; /* Icono amarillo */
                font-size: 1.4rem !important; /* Icono más grande */
                text-shadow: 0 0 10px rgba(255, 215, 0, 0.8) !important;
            }
            /* Override sidebar text color */
            section[data-testid="stSidebar"] {
                color: #FFFFFF;
            }
            </style>
        ''', unsafe_allow_html=True)

        if 'dashboard_section' not in st.session_state:
            st.session_state.dashboard_section = ":material/table_view: Tabla de Detalle"

        st.session_state.dashboard_section = st.radio(
            "Secciones",
            options=[
                ":material/table_view: Tabla de Detalle", 
                ":material/search: Buscador de Medicamento",
                ":material/analytics: Análisis Específicos",
                ":material/monitoring: Indicadores Clave", 
                ":material/bar_chart: Visualizaciones"
            ],
            label_visibility="collapsed"
        )
        # CSS para anclar el boton Volver al Inicio al fondo del sidebar
        st.markdown('''
            <style>
            /* Nivel 1: stSidebarUserContent - contenedor principal */
            [data-testid="stSidebarUserContent"] {
                display: flex !important;
                flex-direction: column !important;
                height: 100vh !important;
            }
            
            /* Nivel 2: div intermedio que Streamlit genera */
            [data-testid="stSidebarUserContent"] > div {
                display: flex !important;
                flex-direction: column !important;
                flex-grow: 1 !important;
            }

            /* Nivel 3: stVerticalBlock - el bloque que contiene todos los componentes */
            [data-testid="stSidebarUserContent"] > div > div[data-testid="stVerticalBlock"] {
                display: flex !important;
                flex-direction: column !important;
                flex-grow: 1 !important;
            }

            /* Nivel 4: El ultimo stElementContainer (el del boton) se empuja al fondo */
            [data-testid="stSidebarUserContent"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:last-of-type {
                margin-top: auto !important;
                padding-bottom: 2rem !important;
            }
            </style>
        ''', unsafe_allow_html=True)

        if st.button("Volver al Inicio", icon=":material/arrow_back:", help="Limpiar datos y regresar", use_container_width=True, type="primary"):
            st.session_state.df_movements = None
            st.session_state.df_kits = None
            st.session_state.data_loaded = False
            st.rerun()




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
        col_hdr1, col_hdr2 = st.columns([5, 1])
        
        with col_hdr1:
            if logo_b64:
                st.markdown(
                    f"""
                    <div style="display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 1.5rem; margin-top: 0rem; padding-left: 5rem;">
                        <img src="data:image/png;base64,{logo_b64}" alt="Clínica Vida" style="height: 60px;">
                        <div class="main-title" style="text-align: left; font-size: 2.2rem; margin: 0; line-height: 1;">Sistema de Reabastecimiento</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="main-title" style="margin-top: 0rem; text-align: center;">❖ Sistema de Reabastecimiento</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="main-subtitle" style="margin-top: 0.8rem; margin-bottom: 1rem;">Análisis de Inventario &bull; Bodegas 1185 &amp; 1188 &bull; Modelo Consignación</div>',
                unsafe_allow_html=True,
            )
            
        with col_hdr2:
            st.empty() # Arrow button removed from here as per user request (moved back to bottom sidebar)
            
        st.markdown('<div class="gold-bar" style="margin-top: -0.5rem;"></div>', unsafe_allow_html=True)

        # Content Router Based on Sidebar Selection
        if st.session_state.dashboard_section == ":material/monitoring: Indicadores Clave":
            render_kpis(df_reorder)
            
        elif st.session_state.dashboard_section == ":material/table_view: Tabla de Detalle":
            # Pre-generar el archivo para pasarlo a la tabla e integrarlo en el titulo
            excel_buffer = generate_excel_export(df_reorder)
            filename = get_export_filename()
            render_main_table(df_reorder, excel_buffer, filename)
        elif st.session_state.dashboard_section == ":material/search: Buscador de Medicamento":
            render_product_explorer(df_reorder, df_consumption, st.session_state.df_kits)
        elif st.session_state.dashboard_section == ":material/analytics: Análisis Específicos":
            render_specific_analysis(df_reorder, df_consumption, st.session_state.df_kits)
        elif st.session_state.dashboard_section == ":material/bar_chart: Visualizaciones":
            render_charts(df_reorder)
            
        # === Temporary Success Banner ===
        if st.session_state.get('show_success_banner', False):
            st.markdown('''
            <style>
            @keyframes slideOutTopRight {
                0% { opacity: 0; transform: translateY(-20px); }
                10% { opacity: 1; transform: translateY(0); }
                85% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(-20px); display: none; }
            }
            .floating-toast-white {
                position: fixed;
                top: 1rem;
                right: 2rem;
                background: #FFFFFF;
                color: var(--cv-navy);
                border-radius: 8px;
                padding: 0.5rem 1.5rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                display: flex;
                align-items: center;
                gap: 0.8rem;
                z-index: 9999999;
                pointer-events: none; /* Crucial so it doesn't block clicks when invisible */
                animation: slideOutTopRight 4s forwards ease-in-out;
                border-left: 4px solid var(--success);
            }
            </style>
            <div class="floating-toast-white">
                <span class="material-symbols-rounded" style="color: var(--success); font-size: 1.5rem;">check_circle</span> 
                <span style="font-size: 1rem; font-weight: 600;">Datos sincronizados</span>
            </div>
            ''', unsafe_allow_html=True)
            st.session_state.show_success_banner = False

    except Exception as e:
        st.error(f"❌ Error en el procesamiento: {str(e)}")
        st.exception(e)

else:
    # Empty state
    logo_img = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'style="height:80px;margin-bottom:1rem;" '
        f'alt="Clínica Vida">'
    ) if logo_b64 else '<div style="font-size: 4rem; margin-bottom: 0.5rem;"><span class="material-symbols-rounded">local_pharmacy</span></div>'
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; min-height: 80vh; width: 100%;">
            <div style="text-align: center; padding: 3rem; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(43,76,126,0.06); max-width: 850px; width: 100%;">
                {logo_img}
                <h2 style="color: #2B4C7E; margin-bottom: 0.5rem; font-size: 2rem;">Bienvenido al Sistema de Reabastecimiento</h2>
                <p style="color: #556677; font-size: 1.1rem; line-height: 1.5; margin: 0;">
                    Cargue sus archivos de movimientos y canastas desde la barra lateral,
                    o genere datos de prueba para explorar el sistema.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Global Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="global-footer-container" style="padding-bottom: 1rem; text-align: center;">
    <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 400; text-shadow: 0 1px 3px rgba(255,255,255,0.8);">
        &copy; 2026 Nostra Sistema de Reabastecimiento. &bull; <span style="opacity: 0.8;"><b>Powered by Nostra</b> para Clínica Vida.</span>
    </div>
</div>
""", unsafe_allow_html=True)
