"""
real_data_processor.py — Procesador de archivos Excel reales del hospital.

Procesa 3 archivos Excel:
    1. Canastas: inventario reservado en kits
    2. Inventario Mensual: saldo inicial + entradas - salidas por bodega
    3. Consumo Histórico: registros individuales de despacho

Estrategia de detección de columnas (doble):
    1. Primero busca por NOMBRE DE ENCABEZADO (case-insensitive)
    2. Si no encuentra, usa el INDICE DE COLUMNA (posición A=0, B=1, C=2...)
Solo se procesan bodegas 1185 y 1188.
"""

import pandas as pd
import numpy as np
from io import BytesIO


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------
BODEGAS_VALIDAS = {"1185", "1188"}


def _find_column(
    df: pd.DataFrame,
    candidates: list[str],
    label: str,
    fallback_index: int = None,
) -> str:
    """
    Busca una columna en el DataFrame con doble estrategia:
      1. Por nombre de encabezado (case-insensitive) probando la lista de candidatos
      2. Por indice de columna (fallback_index) si no se encuentra por nombre

    Returns: nombre real de la columna encontrada.
    Lanza ValueError si ninguna estrategia funciona.
    """
    # Estrategia 1: buscar por nombre de encabezado
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        key = candidate.lower().strip()
        if key in cols_lower:
            return cols_lower[key]

    # Estrategia 2: fallback por indice de columna
    if fallback_index is not None and 0 <= fallback_index < len(df.columns):
        return df.columns[fallback_index]

    raise ValueError(
        f"No se encontro la columna '{label}'. "
        f"Se buscaron por nombre: {candidates}. "
        f"Indice fallback: {fallback_index}. "
        f"Columnas disponibles ({len(df.columns)}): {list(df.columns)}"
    )


def _read_excel_flexible(file_bytes: bytes) -> pd.DataFrame:
    """Lee un Excel probando openpyxl y xlrd como fallback."""
    buf = BytesIO(file_bytes)
    try:
        df = pd.read_excel(buf, engine="openpyxl")
    except Exception:
        buf.seek(0)
        df = pd.read_excel(buf, engine="xlrd")
    # Limpiar espacios en nombres de columnas
    df.columns = df.columns.astype(str).str.strip()
    return df


# ---------------------------------------------------------------------------
# 1. Parser de Canastas
# ---------------------------------------------------------------------------
def parse_canastas(file_bytes: bytes) -> pd.DataFrame:
    """
    Procesa el archivo de Canastas (inventario reservado en kits).

    Busca columnas por encabezado:
        - CODIGO / Codigo / codigo -> codigo del articulo
        - Descripcion / descripcion -> nombre del articulo (validacion)
        - Total / total -> cantidad reservada

    Returns
    -------
    pd.DataFrame
        Columns: codigo, nombre, cantidad_comprometida
    """
    df = _read_excel_flexible(file_bytes)

    # Buscar columnas: encabezado primero, luego indice (A=0, B=1, H=7)
    col_codigo = _find_column(df, [
        "CODIGO", "Codigo", "codigo", "Código", "COD",
        "codigo del articulo", "Codigo del articulo",
    ], "CODIGO", fallback_index=0)
    col_nombre = _find_column(df, [
        "Descripcion", "descripcion", "Descripción", "DESCRIPCION",
        "Nombre", "nombre", "NOMBRE",
        "Nombre articulo", "nombre articulo", "Nombre Articulo",
    ], "Descripcion", fallback_index=1)
    col_total = _find_column(df, [
        "Total", "total", "TOTAL", "Cantidad", "cantidad",
    ], "Total", fallback_index=7)

    # Extraer solo las columnas necesarias
    result = pd.DataFrame({
        "codigo": df[col_codigo].astype(str).str.strip(),
        "nombre": df[col_nombre].astype(str).str.strip(),
        "cantidad_comprometida": pd.to_numeric(df[col_total], errors="coerce").fillna(0).round(0),
    })

    # Log suma bruta ANTES de filtrar (para diagnostico)
    suma_bruta = result["cantidad_comprometida"].sum()

    # Eliminar filas sin codigo valido
    filas_antes = len(result)
    result = result[result["codigo"].notna() & (result["codigo"] != "") & (result["codigo"] != "nan")]
    filas_filtradas = filas_antes - len(result)
    suma_post_filtro = result["cantidad_comprometida"].sum()

    if filas_filtradas > 0:
        print(f"[CANASTAS] Filas filtradas: {filas_filtradas} (Total perdido: {suma_bruta - suma_post_filtro})")

    # Agrupar por codigo (puede haber multiples entradas del mismo articulo)
    result = result.groupby("codigo", as_index=False).agg({
        "nombre": "first",
        "cantidad_comprometida": "sum",
    })

    result["cantidad_comprometida"] = result["cantidad_comprometida"].round(0).astype(int)
    return result.sort_values("codigo").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Parser de Inventario Mensual
# ---------------------------------------------------------------------------
def parse_inventario_mensual(file_bytes: bytes) -> pd.DataFrame:
    """
    Procesa el archivo de Inventario Mensual.

    Busca columnas por encabezado:
        - salser / bodega -> codigo de bodega (filtrar solo 1185 y 1188)
        - salart / codigo -> codigo del articulo
        - Columna de saldo inicial (busca por posicion C o nombre)
        - Columna de entradas (busca por posicion E o nombre)
        - Columna de salidas (busca por posicion G o nombre)

    Calcula: saldo_actual = saldo_inicial + entradas - salidas

    Returns
    -------
    pd.DataFrame
        Columns: codigo, nombre, saldo_inicial, entradas, salidas, saldo_actual
    """
    df = _read_excel_flexible(file_bytes)

    # Buscar columna de bodega (A=0)
    col_bodega = _find_column(
        df,
        ["salser", "SALSER", "Salser", "bodega", "Bodega", "BODEGA", "Almacen", "almacen"],
        "salser (bodega)",
        fallback_index=0,
    )

    # Buscar columna de codigo de articulo (B=1)
    col_codigo = _find_column(
        df,
        ["salart", "SALART", "Salart", "codigo", "Codigo", "CODIGO", "Código"],
        "salart (codigo articulo)",
        fallback_index=1,
    )

    # Filtrar solo bodegas 1185 y 1188
    df[col_bodega] = df[col_bodega].astype(str).str.strip()
    df = df[df[col_bodega].isin(BODEGAS_VALIDAS)].copy()

    if df.empty:
        raise ValueError(
            f"No se encontraron datos para bodegas {BODEGAS_VALIDAS}. "
            f"Valores encontrados en '{col_bodega}': {df[col_bodega].unique().tolist()}"
        )

    # Saldo inicial (C=2), Entradas (E=4), Salidas (G=6)
    col_saldo = _find_column(
        df,
        ["saldo_inicial", "Saldo Inicial", "saldo inicial", "Saldo_Inicial",
         "saldo", "Saldo", "SALDO", "Inicio"],
        "saldo inicial",
        fallback_index=2,
    )

    col_entradas = _find_column(
        df,
        ["entradas", "Entradas", "ENTRADAS", "entrada", "Entrada",
         "Ingresos", "ingresos"],
        "entradas",
        fallback_index=4,
    )

    col_salidas = _find_column(
        df,
        ["salidas", "Salidas", "SALIDAS", "salida", "Salida",
         "Egresos", "egresos", "Despachos"],
        "salidas",
        fallback_index=6,
    )

    # Nombre/descripcion (opcional) -- en inventario mensual suele ser "art nom"
    try:
        col_nombre = _find_column(
            df,
            ["nombre", "Nombre", "NOMBRE",
             "descripcion", "Descripcion", "DESCRIPCION", "Descripción",
             "Articulo", "articulo",
             "art nom", "Art Nom", "Artnom", "ARTNOM",
             "nom_articulo", "Nom Articulo", "Nombre articulo"],
            "nombre",
        )
    except ValueError:
        col_nombre = None

    # Construir resultado
    result = pd.DataFrame({
        "codigo": df[col_codigo].astype(str).str.strip(),
        "saldo_inicial": pd.to_numeric(df[col_saldo], errors="coerce").fillna(0),
        "entradas": pd.to_numeric(df[col_entradas], errors="coerce").fillna(0),
        "salidas": pd.to_numeric(df[col_salidas], errors="coerce").fillna(0),
    })

    if col_nombre:
        result["nombre"] = df[col_nombre].astype(str).str.strip()
    else:
        result["nombre"] = result["codigo"]

    # Eliminar filas sin codigo valido
    result = result[result["codigo"].notna() & (result["codigo"] != "") & (result["codigo"] != "nan")]

    # Agrupar por codigo (consolidar ambas bodegas)
    result = result.groupby("codigo", as_index=False).agg({
        "nombre": "first",
        "saldo_inicial": "sum",
        "entradas": "sum",
        "salidas": "sum",
    })

    # Calcular saldo actual: inicial + entradas - salidas
    result["saldo_actual"] = (
        result["saldo_inicial"] + result["entradas"] - result["salidas"]
    ).clip(lower=0).astype(int)

    result["saldo_inicial"] = result["saldo_inicial"].astype(int)
    result["entradas"] = result["entradas"].astype(int)
    result["salidas"] = result["salidas"].astype(int)

    return result.sort_values("codigo").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. Parser de Consumo Histórico
# ---------------------------------------------------------------------------
def parse_consumo_historico(file_bytes: bytes, dias_periodo: int = 90) -> pd.DataFrame:
    """
    Procesa el archivo de Consumo Histórico.

    Cada fila es un registro individual de despacho (1 unidad por registro).
    Se agrupa por codigo de articulo contando las filas para obtener el total.

    Busca columnas por encabezado:
        - codigo (col E) -> codigo del articulo
        - cantidad (col F) -> cantidad despachada (usualmente 1)
        - bodega (col J) -> codigo de bodega (filtrar 1185/1188)
        - nombre (col L) -> nombre del articulo

    Parameters
    ----------
    dias_periodo : int
        Numero de dias que abarca el archivo historico (para calcular promedio).

    Returns
    -------
    pd.DataFrame
        Columns: codigo, nombre, total_consumo, consumo_promedio_diario
    """
    df = _read_excel_flexible(file_bytes)

    # Buscar columna de bodega (J=9)
    try:
        col_bodega = _find_column(
            df,
            ["bodega", "Bodega", "BODEGA", "almacen", "Almacen", "ALMACEN",
             "Cod Bodega", "cod_bodega"],
            "bodega",
            fallback_index=9,
        )
        # Filtrar solo bodegas validas
        df[col_bodega] = df[col_bodega].astype(str).str.strip()
        df = df[df[col_bodega].isin(BODEGAS_VALIDAS)].copy()
    except ValueError:
        # Si no hay columna de bodega, usar todos los datos
        pass

    if df.empty:
        raise ValueError("No se encontraron datos de consumo para bodegas 1185/1188")

    # Buscar columna de codigo (E=4)
    col_codigo = _find_column(
        df,
        ["codigo", "Codigo", "CODIGO", "Código", "cod_articulo",
         "Cod Articulo", "cod articulo", "CodArticulo",
         "codigo del articulo", "Codigo del articulo", "CODIGO DEL ARTICULO"],
        "codigo del articulo",
        fallback_index=4,
    )

    # Buscar columna de cantidad (F=5)
    try:
        col_cantidad = _find_column(
            df,
            ["cantidad", "Cantidad", "CANTIDAD", "qty", "Qty", "cant"],
            "cantidad",
            fallback_index=5,
        )
    except ValueError:
        col_cantidad = None  # Si no existe, cada fila cuenta como 1

    # Buscar columna de nombre (L=11) -- en consumo historico suele ser "Nombre articulo"
    try:
        col_nombre = _find_column(
            df,
            ["Nombre articulo", "nombre articulo", "Nombre Articulo", "NOMBRE ARTICULO",
             "nombre", "Nombre", "NOMBRE",
             "descripcion", "Descripcion", "DESCRIPCION", "Descripción",
             "Articulo", "articulo",
             "nom_articulo", "Nom Articulo",
             "art nom", "Art Nom", "Artnom"],
            "nombre del articulo",
            fallback_index=11,
        )
    except ValueError:
        col_nombre = None

    # Construir DataFrame de trabajo
    work = pd.DataFrame({
        "codigo": df[col_codigo].astype(str).str.strip(),
    })

    if col_cantidad:
        work["cantidad"] = pd.to_numeric(df[col_cantidad], errors="coerce").fillna(1)
    else:
        work["cantidad"] = 1

    if col_nombre:
        work["nombre"] = df[col_nombre].astype(str).str.strip()
    else:
        work["nombre"] = work["codigo"]

    # Eliminar filas sin codigo
    work = work[work["codigo"].notna() & (work["codigo"] != "") & (work["codigo"] != "nan")]

    # Agrupar por codigo: sumar cantidades
    result = work.groupby("codigo", as_index=False).agg({
        "nombre": "first",
        "cantidad": "sum",
    }).rename(columns={"cantidad": "total_consumo"})

    result["total_consumo"] = result["total_consumo"].astype(int)

    # Calcular consumo promedio diario
    result["consumo_promedio_diario"] = (
        result["total_consumo"] / max(dias_periodo, 1)
    ).round(2)

    return result.sort_values("codigo").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Pipeline completo con datos reales
# ---------------------------------------------------------------------------
def process_real_pipeline(
    df_inventario: pd.DataFrame,
    df_canastas: pd.DataFrame,
    df_consumo: pd.DataFrame,
    dias_proyeccion: int = 20,
) -> dict:
    """
    Ejecuta el pipeline completo con los 3 archivos procesados.

    Calculo central:
        disponible_real = saldo_actual - cantidad_comprometida (canastas)
        proyeccion = consumo_promedio_diario * dias_proyeccion
        cantidad_a_pedir = max(0, proyeccion - disponible_real)

    Parameters
    ----------
    df_inventario : pd.DataFrame
        Output de parse_inventario_mensual()
    df_canastas : pd.DataFrame
        Output de parse_canastas()
    df_consumo : pd.DataFrame
        Output de parse_consumo_historico()
    dias_proyeccion : int
        Dias a proyectar para calcular el pedido (default 20)

    Returns
    -------
    dict con keys: kpis, reorder, consumption, stock
    """
    # ---- 1. Base: inventario mensual ----
    df = df_inventario[["codigo", "nombre", "saldo_inicial", "entradas", "salidas", "saldo_actual"]].copy()
    df.rename(columns={"saldo_actual": "stock_actual"}, inplace=True)

    # ---- 1b. Enriquecer nombre si el inventario no lo tiene ----
    # Si nombre == codigo, intentar traer nombre de canastas o consumo
    mask_sin_nombre = (df["nombre"] == df["codigo"]) | (df["nombre"].isna()) | (df["nombre"] == "") | (df["nombre"] == "nan")

    if mask_sin_nombre.any():
        # Intentar desde canastas
        if df_canastas is not None and not df_canastas.empty and "nombre" in df_canastas.columns:
            nombre_canastas = df_canastas[["codigo", "nombre"]].rename(columns={"nombre": "nombre_canastas"})
            df = df.merge(nombre_canastas, on="codigo", how="left")
            df.loc[mask_sin_nombre & df["nombre_canastas"].notna(), "nombre"] = df["nombre_canastas"]
            df.drop(columns=["nombre_canastas"], inplace=True)

        # Recalcular mask
        mask_sin_nombre = (df["nombre"] == df["codigo"]) | (df["nombre"].isna()) | (df["nombre"] == "") | (df["nombre"] == "nan")

        # Intentar desde consumo
        if mask_sin_nombre.any() and df_consumo is not None and not df_consumo.empty and "nombre" in df_consumo.columns:
            nombre_consumo = df_consumo[["codigo", "nombre"]].drop_duplicates("codigo").rename(columns={"nombre": "nombre_consumo"})
            df = df.merge(nombre_consumo, on="codigo", how="left")
            df.loc[mask_sin_nombre & df["nombre_consumo"].notna(), "nombre"] = df["nombre_consumo"]
            df.drop(columns=["nombre_consumo"], inplace=True)

    # ---- 2. Merge canastas (comprometido) ----
    if df_canastas is not None and not df_canastas.empty:
        df = df.merge(
            df_canastas[["codigo", "cantidad_comprometida"]],
            on="codigo",
            how="left",
        )
    else:
        df["cantidad_comprometida"] = 0

    df["cantidad_comprometida"] = df["cantidad_comprometida"].fillna(0).astype(int)

    # ---- 3. Merge consumo ----
    if df_consumo is not None and not df_consumo.empty:
        consumo_cols = ["codigo", "total_consumo", "consumo_promedio_diario"]
        available_cols = [c for c in consumo_cols if c in df_consumo.columns]
        df = df.merge(
            df_consumo[available_cols],
            on="codigo",
            how="left",
        )
    else:
        df["total_consumo"] = 0
        df["consumo_promedio_diario"] = 0.0

    df["total_consumo"] = df["total_consumo"].fillna(0).astype(int)
    df["consumo_promedio_diario"] = df["consumo_promedio_diario"].fillna(0.0)

    # ---- 4. Calculos centrales ----

    # Stock disponible = stock actual - comprometido en canastas
    df["stock_disponible"] = (df["stock_actual"] - df["cantidad_comprometida"]).clip(lower=0).astype(int)

    # Proyeccion de demanda
    df["proyeccion_dias"] = (
        df["consumo_promedio_diario"] * dias_proyeccion
    ).round(0).astype(int)

    # Cobertura en dias
    df["cobertura_dias"] = np.where(
        df["consumo_promedio_diario"] > 0,
        (df["stock_disponible"] / df["consumo_promedio_diario"]).round(1),
        np.inf,
    )

    # Cantidad a pedir
    df["cantidad_a_pedir"] = (
        (df["proyeccion_dias"] - df["stock_disponible"]).clip(lower=0).astype(int)
    )

    # Estado de riesgo
    df["estado_riesgo"] = np.where(
        df["cobertura_dias"] < dias_proyeccion,
        "Reabastecer",
        "OK",
    )

    # Renombrar proyeccion para compatibilidad con el frontend
    df.rename(columns={"proyeccion_dias": "proyeccion_20_dias"}, inplace=True)

    # Ordenar por cantidad a pedir (mayor primero)
    df = df.sort_values("cantidad_a_pedir", ascending=False).reset_index(drop=True)

    # ---- 5. KPIs ----
    total_products = len(df)
    total_stock = int(df["stock_actual"].sum())
    total_committed = int(df_canastas["cantidad_comprometida"].sum()) if df_canastas is not None and not df_canastas.empty else 0
    total_available = int(df["stock_disponible"].sum())
    total_to_order = int(df["cantidad_a_pedir"].sum())
    risk_products = len(df[df["estado_riesgo"] == "Reabastecer"])
    risk_pct = round(risk_products / max(total_products, 1) * 100, 1)

    kpis = {
        "total_products": total_products,
        "total_stock": total_stock,
        "total_committed": total_committed,
        "total_available": total_available,
        "total_to_order": total_to_order,
        "risk_products": risk_products,
        "risk_pct": risk_pct,
    }

    # ---- 6. Convertir a JSON-friendly ----
    def _df_to_json(dataframe):
        dataframe = dataframe.copy()
        for col in dataframe.columns:
            if pd.api.types.is_datetime64_any_dtype(dataframe[col]):
                dataframe[col] = dataframe[col].dt.strftime("%Y-%m-%d")
            elif dataframe[col].dtype == object:
                pass
            else:
                dataframe[col] = dataframe[col].replace([np.inf, -np.inf], 9999)
                dataframe[col] = dataframe[col].fillna(0)
        return dataframe.to_dict(orient="records")

    return {
        "kpis": kpis,
        "reorder": _df_to_json(df),
        "consumption": _df_to_json(df_consumo) if df_consumo is not None else [],
        "stock": _df_to_json(df_inventario),
    }
