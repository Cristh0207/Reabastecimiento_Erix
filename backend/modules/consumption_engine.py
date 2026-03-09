"""
consumption_engine.py — Análisis de consumo y proyección.

Skills:
    - skill_consumption_analysis: Computes average daily consumption over trailing window.
    - skill_projection_engine: Projects demand for a coverage period.

Consumption = SUM(salidas) in last 90 days / 90
Projection  = consumo_promedio_diario × coverage_days
"""

import pandas as pd
import numpy as np


def calculate_consumption(
    df_movements: pd.DataFrame,
    days: int = 90,
) -> pd.DataFrame:
    """
    Calculate average daily consumption per product over the last *days* days.

    Logic
    -----
    1. Determine the most recent date in the dataset.
    2. Filter exits (salidas) from the last `days` days.
    3. consumo_promedio_diario = total_salidas / days

    Parameters
    ----------
    df_movements : pd.DataFrame
        Validated movements DataFrame.
    days : int
        Trailing window in days (default 90).

    Returns
    -------
    pd.DataFrame
        Columns: codigo, nombre, total_salidas, consumo_promedio_diario
    """
    df = df_movements.copy()

    # Most recent date in the dataset
    fecha_max = df["fecha"].max()
    fecha_min = fecha_max - pd.Timedelta(days=days)

    # Filter: exits only, within the window
    mask = (
        (df["tipo_movimiento"] == "salida")
        & (df["fecha"] > fecha_min)
        & (df["fecha"] <= fecha_max)
    )
    exits = df.loc[mask]

    # Aggregate total exits per product
    consumption = (
        exits.groupby("codigo", as_index=False)
        .agg(
            nombre=("nombre", "first"),
            total_salidas=("cantidad", "sum"),
        )
    )

    # Average daily consumption
    consumption["consumo_promedio_diario"] = (
        consumption["total_salidas"] / days
    ).round(2)

    # Ensure all products from movements are represented (even zero-consumption)
    all_products = df[["codigo", "nombre"]].drop_duplicates()
    consumption = all_products.merge(consumption, on=["codigo", "nombre"], how="left")
    consumption["total_salidas"] = consumption["total_salidas"].fillna(0).astype(int)
    consumption["consumo_promedio_diario"] = consumption["consumo_promedio_diario"].fillna(0.0)

    return consumption.sort_values("codigo").reset_index(drop=True)


def calculate_projection(
    df_consumption: pd.DataFrame,
    coverage_days: int = 20,
) -> pd.DataFrame:
    """
    Calculate the projected demand for a coverage period.

    Logic
    -----
    proyeccion_20_dias = consumo_promedio_diario × coverage_days

    Parameters
    ----------
    df_consumption : pd.DataFrame
        Output of calculate_consumption().
    coverage_days : int
        Number of days to project (default 20).

    Returns
    -------
    pd.DataFrame
        Same as input with additional column: proyeccion_20_dias
    """
    df = df_consumption.copy()
    df["proyeccion_20_dias"] = (
        df["consumo_promedio_diario"] * coverage_days
    ).round(0).astype(int)

    return df
