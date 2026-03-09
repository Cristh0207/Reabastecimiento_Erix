"""
reorder_engine.py — Motor de cálculo de reabastecimiento.

Skills:
    - skill_reorder_engine: Merges stock, consumption, and kits to compute reorder quantities.
    - skill_excel_export: Generates the downloadable Excel file.

Full pipeline:
    stock_disponible = stock_actual - cantidad_comprometida
    cobertura_dias   = stock_disponible / consumo_promedio_diario
    cantidad_a_pedir = max(0, proyeccion_20 - stock_disponible)
    estado_riesgo    = "Reabastecer" if cobertura < 20 else "OK"
"""

import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime


def calculate_reorder(
    df_stock: pd.DataFrame,
    df_consumption: pd.DataFrame,
    df_kits: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate reorder quantities for all products.

    Parameters
    ----------
    df_stock : pd.DataFrame
        From inventory_engine.calculate_stock(). Columns: codigo, nombre, stock_actual.
    df_consumption : pd.DataFrame
        From consumption_engine.calculate_projection(). Columns include:
        codigo, nombre, consumo_promedio_diario, proyeccion_20_dias.
    df_kits : pd.DataFrame
        From data_loader.load_kits(). Columns: codigo, nombre, cantidad_comprometida.

    Returns
    -------
    pd.DataFrame
        Full reorder analysis with all calculated columns.
    """
    # Start from stock
    df = df_stock[["codigo", "nombre", "stock_actual"]].copy()

    # Merge consumption
    consumption_cols = ["codigo", "consumo_promedio_diario", "proyeccion_20_dias"]
    df = df.merge(
        df_consumption[consumption_cols],
        on="codigo",
        how="left",
    )
    df["consumo_promedio_diario"] = df["consumo_promedio_diario"].fillna(0.0)
    df["proyeccion_20_dias"] = df["proyeccion_20_dias"].fillna(0).astype(int)

    # Merge kits (committed stock)
    kits_cols = ["codigo", "cantidad_comprometida"]
    if df_kits is not None and not df_kits.empty:
        df = df.merge(
            df_kits[kits_cols],
            on="codigo",
            how="left",
        )
    else:
        df["cantidad_comprometida"] = 0

    df["cantidad_comprometida"] = df["cantidad_comprometida"].fillna(0).astype(int)

    # --- Core calculations ---

    # Available stock
    df["stock_disponible"] = (df["stock_actual"] - df["cantidad_comprometida"]).clip(lower=0).astype(int)

    # Coverage in days
    df["cobertura_dias"] = np.where(
        df["consumo_promedio_diario"] > 0,
        (df["stock_disponible"] / df["consumo_promedio_diario"]).round(1),
        np.inf,
    )

    # Quantity to order
    df["cantidad_a_pedir"] = (
        (df["proyeccion_20_dias"] - df["stock_disponible"]).clip(lower=0).astype(int)
    )

    # Risk status
    df["estado_riesgo"] = np.where(
        df["cobertura_dias"] < 20,
        "Reabastecer",
        "OK",
    )

    # Sort by quantity to order (descending) for practical use
    df = df.sort_values("cantidad_a_pedir", ascending=False).reset_index(drop=True)

    return df


def generate_excel_export(df_reorder: pd.DataFrame) -> BytesIO:
    """
    Generate an Excel file with the suggested reorder.

    skill_excel_export: Filters products with cantidad_a_pedir > 0
    and exports to a formatted Excel workbook.

    Parameters
    ----------
    df_reorder : pd.DataFrame
        Full reorder DataFrame.

    Returns
    -------
    BytesIO
        In-memory Excel file ready for download.
    """
    # Filter only products that need reordering
    pedido = df_reorder.loc[
        df_reorder["cantidad_a_pedir"] > 0,
        ["codigo", "nombre", "cantidad_a_pedir"],
    ].copy()

    pedido = pedido.sort_values("cantidad_a_pedir", ascending=False).reset_index(drop=True)

    # Write to Excel in memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pedido.to_excel(writer, index=False, sheet_name="Pedido Sugerido")

        # Auto-adjust column widths
        worksheet = writer.sheets["Pedido Sugerido"]
        for i, col in enumerate(pedido.columns):
            max_length = max(
                pedido[col].astype(str).map(len).max(),
                len(col),
            ) + 3
            worksheet.column_dimensions[chr(65 + i)].width = max_length

    buffer.seek(0)
    return buffer


def get_export_filename() -> str:
    """Generate the export filename with current date."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"pedido_reabastecimiento_{today}.xlsx"
