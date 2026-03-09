# Backend - Sistema de Reabastecimiento

Este directorio conforma el motor analítico e interfaz de programación (API) del Sistema de Reabastecimiento de Clínica Vida. Se encarga de recibir, procesar y despachar los cálculos de inventario y reabastecimiento en milisegundos.

## Stack Tecnológico y Dependencias
*   **Framework API Server:** FastAPI (Alta performance, basado en Starlette y Pydantic, soporte asíncrono nativo).
*   **Servidor ASGI:** Uvicorn.
*   **Motor de Datos:** Pandas y NumPy (procesamiento vectorial de dataframes en memoria).
*   **Parser de Archivos de Oficina:** `openpyxl` (lectura/escritura del formato `.xlsx`).
*   **Manejo de Formularios/Archivos:** `python-multipart`.

## Arquitectura de Procesamiento de Datos

El motor de cálculo, originalmente un script monolítico en arquitecturas previas, fue convertido en un servidor RESTful puro *stateless*. Las lógicas especializadas habitan en la carpeta `/modules`:

1.  **`inventory_engine.py` (`calculate_stock`):** Realiza operaciones de agregación y agrupación (Group By) sobre miles de movimientos de inventario (`ENTRADA`, `SALIDA`) determinando el stock consolidado actual.
2.  **`consumption_engine.py`:** Calcula la media móvil de consumo histórico base/día aislando métricas de días de inactividad, logrando un ratio proyectivo para futuras consumiciones.
3.  **`reorder_engine.py`:** Orquestación y *join* de datasets (Integración Stock-Consumo-Canastas comprometidas). Decide de manera transaccional, en cada fila de datos de med/insumo, el estado de riesgo semántico ("Reabastecer" vs "Todo OK") y las sumas algebraicas finales algebraicas de `stock - compromiso = disponible`.
4.  **`demo_generator.py`:** Scripts para recrear DataFrames en crudo con datos sintéticos logísticamente coherentes para fines de demostración bajo demanda.

## Endpoints Principales REST (FastAPI DOCS)

El servidor expone *Swagger UI* de forma nativa. Al levantar el servidor, navega a `http://localhost:8000/docs`.

*   `GET /health`: Endpoint Ping-Pong para validación de Liveness.
*   `POST /api/upload/movements`: Receptor multipart asíncrono pasivo que procesa la carga del binario de Movimientos en un buffer temporal y lo convierte a Pandas DF interno (`df_mov_global`).
*   `POST /api/upload/kits`: Idéntico mecanismo para captar las Canastas Quirúrgicas comprometidas (`df_canastas_global`).
*   `POST /api/process`: Invocación al pipeline analítico. Llama secuencialmente a los engines y retorna la carga útil total en un JSON pre-compilado listo para la UI visual.
*   `GET /api/demo`: Puente al `demo_generator`. Rellena las variables globales en memoria RAM con matrices sintéticas y corre inmediatamente un proceso para devolver el payload JSON.
*   `GET /api/export`: Disparador para compilar a binario XLS y despachar al navegador el archivo vía un objeto `StreamingResponse` (MIME Types of MS Excel).

## Comandos Útiles e Inicialización

Se asume la utilización de un entorno virtual (`venv` o `conda`).

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 3. Instalar librerías determinísticas
pip install -r requirements.txt

# 4. Levantar entorno dev
python -m uvicorn main:app --reload --port 8000
```
