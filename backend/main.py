"""
main.py — Backend API (FastAPI) para el Sistema de Reabastecimiento.

Expone endpoints REST para:
    - Subir 3 archivos Excel (Inventario Mensual, Canastas, Consumo Histórico)
    - Procesar el pipeline de reabastecimiento con datos reales
    - Generar datos demo para pruebas rápidas
    - Exportar el pedido sugerido como Excel
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import numpy as np
from io import BytesIO
from typing import Optional

# Módulos de lógica de negocio
from modules.real_data_processor import (
    parse_canastas,
    parse_inventario_mensual,
    parse_consumo_historico,
    process_real_pipeline,
)

# Módulos legacy (para datos demo)
from modules.inventory_engine import calculate_stock
from modules.consumption_engine import calculate_consumption, calculate_projection
from modules.reorder_engine import calculate_reorder, generate_excel_export, get_export_filename
from modules.demo_generator import generate_demo_movements, generate_demo_kits

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sistema de Reabastecimiento API",
    description="API REST para el sistema de inventario Clínica Vida",
    version="3.0.0",
)

# CORS: permitir que el frontend React se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_file_bytes(file: UploadFile) -> bytes:
    """Lee los bytes crudos del archivo subido."""
    name = file.filename.lower()
    if not name.endswith((".xlsx", ".xls")):
        raise HTTPException(400, f"Formato no soportado: {name}. Use .xlsx o .xls")
    return file.file.read()


def _read_upload_legacy(file: UploadFile) -> pd.DataFrame:
    """Lee un archivo CSV o Excel subido via HTTP (legacy para demo)."""
    name = file.filename.lower()
    contents = file.file.read()
    buffer = BytesIO(contents)

    if name.endswith(".csv"):
        df = pd.read_csv(buffer)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(buffer, engine="openpyxl")
    else:
        raise HTTPException(400, f"Formato no soportado: {name}. Use .csv o .xlsx")

    df.columns = df.columns.str.strip().str.lower()
    return df


def _df_to_json(df: pd.DataFrame) -> list:
    """Convierte DataFrame a lista de diccionarios, manejando tipos especiales."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        elif df[col].dtype == object:
            pass
        else:
            df[col] = df[col].replace([np.inf, -np.inf], 9999)
            df[col] = df[col].fillna(0)
    return df.to_dict(orient="records")


def _process_pipeline_legacy(df_movements: pd.DataFrame, df_kits: Optional[pd.DataFrame]):
    """Ejecuta el pipeline LEGACY (con movimientos sintéticos)."""
    df_stock = calculate_stock(df_movements)
    df_consumption = calculate_consumption(df_movements, days=90)
    df_consumption = calculate_projection(df_consumption, coverage_days=20)
    df_reorder = calculate_reorder(df_stock, df_consumption, df_kits)

    total_products = len(df_reorder)
    total_stock = int(df_reorder["stock_actual"].sum())
    total_committed = int(df_reorder["cantidad_comprometida"].sum())
    total_available = int(df_reorder["stock_disponible"].sum())
    total_to_order = int(df_reorder["cantidad_a_pedir"].sum())
    risk_products = len(df_reorder[df_reorder["estado_riesgo"] == "Reabastecer"])
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

    return {
        "kpis": kpis,
        "reorder": _df_to_json(df_reorder),
        "consumption": _df_to_json(df_consumption),
        "stock": _df_to_json(df_stock),
    }


# ---------------------------------------------------------------------------
# Estado en memoria
# ---------------------------------------------------------------------------
_state = {
    # Datos reales (3 archivos)
    "df_inventario": None,
    "df_canastas": None,
    "df_consumo": None,
    # Datos legacy (demo)
    "df_movements": None,
    "df_kits": None,
    # Resultado procesado (para exportar)
    "df_reorder": None,
    "mode": None,  # "real" o "demo"
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


# ---- Upload de archivos reales ----

@app.post("/api/upload/inventario")
async def upload_inventario(file: UploadFile = File(...)):
    """Subir y procesar archivo de Inventario Mensual (saldo + entradas + salidas)."""
    try:
        file_bytes = _read_file_bytes(file)
        df = parse_inventario_mensual(file_bytes)
        _state["df_inventario"] = df
        return {
            "message": f"{len(df):,} productos cargados del inventario mensual",
            "rows": len(df),
            "columns": list(df.columns),
        }
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(400, detail=f"Error procesando archivo de inventario: {str(e)}")


@app.post("/api/upload/canastas")
async def upload_canastas(file: UploadFile = File(...)):
    """Subir y procesar archivo de Canastas (inventario reservado)."""
    try:
        file_bytes = _read_file_bytes(file)
        df = parse_canastas(file_bytes)
        _state["df_canastas"] = df
        return {
            "message": f"{len(df):,} articulos en canastas cargados",
            "rows": len(df),
        }
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(400, detail=f"Error procesando archivo de canastas: {str(e)}")


@app.post("/api/upload/consumo")
async def upload_consumo(file: UploadFile = File(...)):
    """Subir y procesar archivo de Consumo Histórico."""
    try:
        file_bytes = _read_file_bytes(file)
        df = parse_consumo_historico(file_bytes)
        _state["df_consumo"] = df
        return {
            "message": f"{len(df):,} articulos con consumo historico cargados",
            "rows": len(df),
        }
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(400, detail=f"Error procesando archivo de consumo: {str(e)}")


# ---- Procesamiento ----

@app.post("/api/process")
def process(dias_proyeccion: int = Query(default=20, ge=1, le=365)):
    """
    Ejecutar pipeline completo con los datos cargados.

    Si hay archivos reales cargados, usa el pipeline real.
    Si solo hay datos demo, usa el pipeline legacy.
    """
    # Intentar pipeline real primero
    if _state["df_inventario"] is not None:
        if _state["df_canastas"] is None:
            raise HTTPException(400, detail="Falta el archivo de Canastas")
        if _state["df_consumo"] is None:
            raise HTTPException(400, detail="Falta el archivo de Consumo Histórico")

        result = process_real_pipeline(
            df_inventario=_state["df_inventario"],
            df_canastas=_state["df_canastas"],
            df_consumo=_state["df_consumo"],
            dias_proyeccion=dias_proyeccion,
        )
        _state["mode"] = "real"
        _state["df_reorder"] = result.get("reorder", [])
        return result

    # Fallback: pipeline legacy (datos demo)
    if _state["df_movements"] is not None:
        result = _process_pipeline_legacy(_state["df_movements"], _state["df_kits"])
        _state["mode"] = "demo"
        return result

    raise HTTPException(400, detail="No hay datos cargados. Suba los 3 archivos o use Datos de Prueba.")


# ---- Demo ----

@app.get("/api/demo")
def demo():
    """Generar datos demo y ejecutar pipeline legacy."""
    df_movements = generate_demo_movements(n_products=500, n_days=90, seed=42)
    df_kits = generate_demo_kits(df_movements, fraction=0.20, seed=42)

    _state["df_movements"] = df_movements
    _state["df_kits"] = df_kits
    _state["mode"] = "demo"

    result = _process_pipeline_legacy(df_movements, df_kits)
    result["message"] = "Datos demo generados: 500 productos, 90 dias"
    return result


# ---- Exportar ----

@app.get("/api/export")
def export_excel():
    """Descargar Excel con pedido sugerido."""
    if _state["mode"] == "real" and _state["df_reorder"] is not None:
        # Exportar desde datos reales
        reorder_list = _state["df_reorder"]
        if isinstance(reorder_list, list):
            df_reorder = pd.DataFrame(reorder_list)
        else:
            df_reorder = reorder_list

        buffer = generate_excel_export(df_reorder)
        filename = get_export_filename()
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # Fallback legacy
    if _state["df_movements"] is None:
        raise HTTPException(400, detail="No hay datos procesados")

    df_stock = calculate_stock(_state["df_movements"])
    df_consumption = calculate_consumption(_state["df_movements"], days=90)
    df_consumption = calculate_projection(df_consumption, coverage_days=20)
    df_reorder = calculate_reorder(df_stock, df_consumption, _state["df_kits"])

    buffer = generate_excel_export(df_reorder)
    filename = get_export_filename()

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
