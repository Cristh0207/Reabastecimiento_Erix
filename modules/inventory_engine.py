"""
inventory_engine.py — Cálculo de stock actual consolidado.

Skills:
    - skill_inventory_aggregation: Aggregates entries minus exits across both warehouses.

Stock actual = SUM(entradas) - SUM(salidas), consolidated across bodegas 1185 + 1188.
"""

import pandas as pd
import numpy as np


def calculate_stock(df_movements: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate current consolidated stock from movements.

    Logic
    -----
    For each product (codigo):
        stock_actual = SUM(cantidad where tipo_movimiento == 'entrada')
                     - SUM(cantidad where tipo_movimiento == 'salida')

    Both warehouses (1185, 1188) are consolidated into a single stock figure.

    Parameters
    ----------
    df_movements : pd.DataFrame
        Validated movements DataFrame.

    Returns
    -------
    pd.DataFrame
        Columns: codigo, nombre, stock_actual
    """
    df = df_movements.copy()

    # Separate entries and exits
    df["cantidad_signed"] = np.where(
        df["tipo_movimiento"] == "entrada",
        df["cantidad"],
        -df["cantidad"],
    )

    # Aggregate by product code — consolidate both warehouses
    stock = (
        df.groupby("codigo", as_index=False)
        .agg(
            nombre=("nombre", "first"),
            stock_actual=("cantidad_signed", "sum"),
        )
    )

    # Ensure no negative stock (floor at 0)
    stock["stock_actual"] = stock["stock_actual"].clip(lower=0).astype(int)

    return stock.sort_values("codigo").reset_index(drop=True)


def calculate_stock_by_bodega(df_movements: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate stock broken down by warehouse (for detailed analysis).

    Returns
    -------
    pd.DataFrame
        Columns: codigo, nombre, bodega, stock_actual
    """
    df = df_movements.copy()

    df["cantidad_signed"] = np.where(
        df["tipo_movimiento"] == "entrada",
        df["cantidad"],
        -df["cantidad"],
    )

    stock = (
        df.groupby(["codigo", "bodega"], as_index=False)
        .agg(
            nombre=("nombre", "first"),
            stock_actual=("cantidad_signed", "sum"),
        )
    )

    stock["stock_actual"] = stock["stock_actual"].clip(lower=0).astype(int)

    return stock.sort_values(["codigo", "bodega"]).reset_index(drop=True)
