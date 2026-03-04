"""
data_loader.py — Carga y validación de archivos de entrada.

Skills:
    - skill_data_validation: Validates required columns, types, and business rules.

Supports CSV and Excel files for both movements and kits data.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------
MOVEMENTS_REQUIRED_COLUMNS = {
    "fecha",
    "codigo",
    "nombre",
    "bodega",
    "tipo_movimiento",
    "cantidad",
}

KITS_REQUIRED_COLUMNS = {
    "codigo",
    "nombre",
    "cantidad_comprometida",
}

VALID_BODEGAS = {1185, 1188, "1185", "1188"}
VALID_MOVIMIENTOS = {"entrada", "salida"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_file(uploaded_file) -> pd.DataFrame:
    """Read a CSV or Excel file from a Streamlit UploadedFile object."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file, engine="openpyxl")
    else:
        raise ValueError(
            f"Formato no soportado: {name}. Use archivos .csv o .xlsx"
        )


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip column names."""
    df.columns = df.columns.str.strip().str.lower()
    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def load_movements(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load and validate the inventory movements file.

    Returns
    -------
    (DataFrame | None, error_message | None)
    """
    try:
        df = _read_file(uploaded_file)
        df = _normalize_columns(df)

        # --- Validate required columns ---
        missing = MOVEMENTS_REQUIRED_COLUMNS - set(df.columns)
        if missing:
            return None, f"Columnas faltantes en movimientos: {', '.join(sorted(missing))}"

        # --- Type conversions ---
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        if df["fecha"].isna().any():
            n_bad = df["fecha"].isna().sum()
            return None, f"{n_bad} registros tienen fechas inválidas."

        df["codigo"] = df["codigo"].astype(str).str.strip()
        df["nombre"] = df["nombre"].astype(str).str.strip()
        df["bodega"] = df["bodega"].astype(str).str.strip()
        df["tipo_movimiento"] = df["tipo_movimiento"].astype(str).str.strip().str.lower()
        df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")

        if df["cantidad"].isna().any():
            return None, "Existen valores no numéricos en la columna 'cantidad'."

        # --- Business rules ---
        invalid_bodegas = set(df["bodega"].unique()) - {"1185", "1188"}
        if invalid_bodegas:
            return None, f"Bodegas no válidas encontradas: {invalid_bodegas}. Solo se permiten 1185 y 1188."

        invalid_mov = set(df["tipo_movimiento"].unique()) - VALID_MOVIMIENTOS
        if invalid_mov:
            return None, f"Tipos de movimiento no válidos: {invalid_mov}. Solo se permiten 'entrada' y 'salida'."

        if (df["cantidad"] < 0).any():
            return None, "La columna 'cantidad' contiene valores negativos."

        return df, None

    except Exception as e:
        return None, f"Error al cargar movimientos: {str(e)}"


def load_kits(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load and validate the kits (committed stock) file.

    Returns
    -------
    (DataFrame | None, error_message | None)
    """
    try:
        df = _read_file(uploaded_file)
        df = _normalize_columns(df)

        # --- Validate required columns ---
        missing = KITS_REQUIRED_COLUMNS - set(df.columns)
        if missing:
            return None, f"Columnas faltantes en kits: {', '.join(sorted(missing))}"

        # --- Type conversions ---
        df["codigo"] = df["codigo"].astype(str).str.strip()
        df["nombre"] = df["nombre"].astype(str).str.strip()
        df["cantidad_comprometida"] = pd.to_numeric(
            df["cantidad_comprometida"], errors="coerce"
        )

        if df["cantidad_comprometida"].isna().any():
            return None, "Valores no numéricos en 'cantidad_comprometida'."

        if (df["cantidad_comprometida"] < 0).any():
            return None, "'cantidad_comprometida' contiene valores negativos."

        # Aggregate duplicates
        df = (
            df.groupby("codigo", as_index=False)
            .agg({"nombre": "first", "cantidad_comprometida": "sum"})
        )

        return df, None

    except Exception as e:
        return None, f"Error al cargar kits: {str(e)}"
