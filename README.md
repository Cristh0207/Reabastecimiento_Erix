# Nostra BI - Sistema de Reabastecimiento Clinica Vida

Sistema de optimizacion y control de reabastecimiento de medicamentos e insumos medicos para las bodegas 1185 y 1188 de Clinica Vida.

Aplicacion 100% client-side (React + JavaScript), sin backend. Todo el procesamiento ocurre en el navegador.

---

## Que hace el sistema

Recibe 3 archivos Excel exportados del ERP y calcula automaticamente que productos pedir, en que cantidades, basandose en consumo historico y stock actual.

### Archivos de entrada

| # | Archivo | Que contiene | Columnas clave |
|---|---------|-------------|----------------|
| 1 | **Inventario Mensual** | Stock al inicio del mes + movimientos del mes corriente (entradas/salidas). Las salidas reflejan concepto 104 (cargo a paciente) | A=bodega, B=codigo, C=saldo_inicial, E=entradas, G=salidas |
| 2 | **Canastas (Kits)** | Stock comprometido en kits de procedimientos. No disponible para pedido | A=codigo, B=nombre, H=total |
| 3 | **Consumo Historico (3 meses)** | Facturacion de los ultimos 3 meses. Conceptos 104 y 105 | C=servicio, G=codigo, K=cantidad, L=nombre, O=fecha, P=concepto |

### Logica de calculo

```
1. stock_actual = saldo_inicial + entradas - salidas  (inventario, ya incluye concepto 104)
2. stock_real = stock_actual - consumo_105_mes         (restar consumo interno del mes, no reflejado en salidas)
3. stock_disponible = stock_real - canastas             (canastas = stock estatico, no disponible)
4. consumo_promedio_diario = total_consumo_3M / 90      (promedio robusto de 3 meses, conceptos 104+105)
5. proyeccion = consumo_promedio_diario * dias          (demanda proyectada)
6. cantidad_a_pedir = MAX(0, proyeccion - stock_disponible)
```

**Filtros aplicados:**
- Solo bodegas 1185 y 1188
- Solo conceptos 104 (cargo a paciente) y 105 (consumo interno)
- Mes corriente se detecta automaticamente por la columna de fecha (col O)

**Casos especiales:**
- Producto en consumo pero NO en inventario: se agrega con stock 0 y genera pedido
- Producto sin consumo historico: no genera pedido (sin demanda = sin base de calculo)

### KPIs en pantalla

| KPI | Descripcion |
|-----|-------------|
| Total Productos | Referencias unicas procesadas |
| Inventario Actual | Suma de stock_actual de todos los productos |
| Comprometido en Kits | Total de unidades en canastas (no disponible) |
| Stock Disponible | Inventario real disponible despues de ajustes |
| Unidades a Pedir | Total de unidades que necesitan reabastecimiento |
| Productos en Riesgo | Porcentaje de productos con cobertura menor a dias proyectados |
| Consumo Paciente (Mes) | Total concepto 104 del mes corriente (dato real) |
| Consumo Interno (Mes) | Total concepto 105 del mes corriente (dato real) |

### Exportacion

El Excel exportado contiene solo productos que necesitan pedido:
- Codigo
- Producto
- Cantidad a Pedir

---

## Estructura del proyecto

```
Reabastecimiento_Erix/
  frontend/
    src/
      services/
        dataService.js        # Toda la logica de procesamiento (parsers + pipeline + export)
      components/
        App.jsx                # Componente principal
        Dashboard.jsx          # Panel de graficas y tabla
        Sidebar.jsx            # Panel lateral con inputs de archivos
        KpiCards.jsx            # Tarjetas de indicadores
        Charts.jsx             # Graficas (barras, Pareto, distribucion)
      index.css                # Estilos corporativos Clinica Vida
    vercel.json                # Configuracion SPA para Vercel
    package.json
```

---

## Ejecucion local

**Requisitos:** Node.js 18+

```bash
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5173` en el navegador.

---

## Deploy en Vercel (gratis)

1. Subir el repositorio a GitHub
2. Ir a [vercel.com](https://vercel.com) > Login con GitHub
3. **Add New Project** > importar el repositorio
4. Configurar:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Click **Deploy**

No se necesitan variables de entorno. No hay backend. Todo corre en el navegador.

---

## Tecnologias

- **React 18** + **Vite** - Interfaz de usuario
- **xlsx (SheetJS)** - Lectura/escritura de archivos Excel en el navegador
- **Recharts** - Graficas interactivas
- **Vercel** - Hosting estatico gratuito