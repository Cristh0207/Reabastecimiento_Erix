/**
 * dataService.js — Procesamiento de archivos Excel 100% client-side.
 *
 * Reemplaza el backend Python (real_data_processor.py + demo_generator.py + main.py).
 * Usa la librería xlsx (SheetJS) para leer/escribir archivos Excel en el navegador.
 *
 * Estrategia de detección de columnas (doble):
 *   1. Primero busca por NOMBRE DE ENCABEZADO (case-insensitive)
 *   2. Si no encuentra, usa el INDICE DE COLUMNA (posición A=0, B=1, C=2...)
 *
 * Solo se procesan bodegas 1185 y 1188.
 */

import * as XLSX from 'xlsx'

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------
const BODEGAS_VALIDAS = new Set(['1185', '1188'])

// ---------------------------------------------------------------------------
// Utilidades internas
// ---------------------------------------------------------------------------

/**
 * Lee un archivo Excel (File object del input) y retorna un array de objetos.
 * Cada objeto es una fila con claves = encabezados.
 */
function _readExcel(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target.result)
                const workbook = XLSX.read(data, { type: 'array' })
                const sheetName = workbook.SheetNames[0]
                const sheet = workbook.Sheets[sheetName]

                // Obtener rango de la hoja
                const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1')
                const totalCols = range.e.c + 1

                // Leer como JSON con headers
                const rows = XLSX.utils.sheet_to_json(sheet, { defval: '' })

                // También guardar los nombres de columnas originales
                const headers = []
                for (let c = 0; c < totalCols; c++) {
                    const cell = sheet[XLSX.utils.encode_cell({ r: range.s.r, c })]
                    headers.push(cell ? String(cell.v).trim() : `Col_${c}`)
                }

                resolve({ rows, headers, totalCols })
            } catch (err) {
                reject(err)
            }
        }
        reader.onerror = reject
        reader.readAsArrayBuffer(file)
    })
}

/**
 * Busca una columna por nombre de encabezado (case-insensitive) con fallback por índice.
 * @param {string[]} headers - Encabezados reales del archivo
 * @param {string[]} candidates - Nombres candidatos a buscar
 * @param {number|null} fallbackIndex - Índice de columna como fallback
 * @returns {string|null} - Nombre real del encabezado encontrado
 */
function _findColumn(headers, candidates, fallbackIndex = null) {
    const headersLower = {}
    headers.forEach(h => { headersLower[h.toLowerCase().trim()] = h })

    for (const candidate of candidates) {
        const key = candidate.toLowerCase().trim()
        if (headersLower[key] !== undefined) {
            return headersLower[key]
        }
    }

    // Fallback por índice
    if (fallbackIndex !== null && fallbackIndex >= 0 && fallbackIndex < headers.length) {
        return headers[fallbackIndex]
    }

    return null
}

/**
 * Obtiene el valor numérico de una celda, retornando 0 si no es número.
 */
function _num(val) {
    const n = Number(val)
    return isNaN(n) ? 0 : n
}

/**
 * Agrupa un array de objetos por una clave.
 */
function _groupBy(arr, key) {
    const groups = {}
    arr.forEach(item => {
        const k = String(item[key] || '').trim()
        if (!k || k === 'undefined' || k === 'null' || k === 'NaN') return
        if (!groups[k]) groups[k] = []
        groups[k].push(item)
    })
    return groups
}

// ---------------------------------------------------------------------------
// 1. Parser de Canastas
// ---------------------------------------------------------------------------
export async function parseCanastas(file) {
    const { rows, headers } = await _readExcel(file)

    // Buscar columnas: encabezado primero, luego índice (A=0, B=1, H=7)
    const colCodigo = _findColumn(headers, [
        'CODIGO', 'Codigo', 'codigo', 'Código', 'COD',
        'codigo del articulo', 'Codigo del articulo',
    ], 0)

    const colNombre = _findColumn(headers, [
        'Descripcion', 'descripcion', 'Descripción', 'DESCRIPCION',
        'Nombre', 'nombre', 'NOMBRE',
        'Nombre articulo', 'nombre articulo', 'Nombre Articulo',
    ], 1)

    const colTotal = _findColumn(headers, [
        'Total', 'total', 'TOTAL', 'Cantidad', 'cantidad',
    ], 7)

    if (!colCodigo || !colTotal) {
        throw new Error(`No se encontraron columnas requeridas en Canastas. Encabezados: ${headers.join(', ')}`)
    }

    // Agrupar por código y sumar Total
    const groups = {}
    let sumaBruta = 0

    rows.forEach(row => {
        const codigo = String(row[colCodigo] || '').trim()
        const total = Math.round(_num(row[colTotal]))
        const nombre = colNombre ? String(row[colNombre] || '').trim() : codigo

        sumaBruta += total

        if (!codigo || codigo === 'undefined' || codigo === 'NaN') return

        if (!groups[codigo]) {
            groups[codigo] = { codigo, nombre, cantidad_comprometida: 0 }
        }
        groups[codigo].cantidad_comprometida += total
        if (!groups[codigo].nombre || groups[codigo].nombre === codigo) {
            groups[codigo].nombre = nombre
        }
    })

    const result = Object.values(groups)
        .filter(r => r.cantidad_comprometida > 0 || r.codigo)
        .sort((a, b) => a.codigo.localeCompare(b.codigo))

    console.log(`[CANASTAS] Suma bruta Excel: ${sumaBruta}, Suma agrupada: ${result.reduce((s, r) => s + r.cantidad_comprometida, 0)}, Artículos: ${result.length}`)

    return result
}

// ---------------------------------------------------------------------------
// 2. Parser de Inventario Mensual
// ---------------------------------------------------------------------------
export async function parseInventarioMensual(file) {
    const { rows, headers } = await _readExcel(file)

    // Buscar columnas (A=bodega, B=codigo, C=saldo, E=entradas, G=salidas)
    const colBodega = _findColumn(headers, [
        'salser', 'SALSER', 'Salser', 'bodega', 'Bodega', 'BODEGA', 'Almacen', 'almacen',
    ], 0)

    const colCodigo = _findColumn(headers, [
        'salart', 'SALART', 'Salart', 'codigo', 'Codigo', 'CODIGO', 'Código',
    ], 1)

    const colSaldo = _findColumn(headers, [
        'saldo_inicial', 'Saldo Inicial', 'saldo inicial', 'Saldo_Inicial',
        'saldo', 'Saldo', 'SALDO', 'Inicio',
    ], 2)

    const colEntradas = _findColumn(headers, [
        'entradas', 'Entradas', 'ENTRADAS', 'entrada', 'Entrada',
        'Ingresos', 'ingresos',
    ], 4)

    const colSalidas = _findColumn(headers, [
        'salidas', 'Salidas', 'SALIDAS', 'salida', 'Salida',
        'Egresos', 'egresos', 'Despachos',
    ], 6)

    const colNombre = _findColumn(headers, [
        'nombre', 'Nombre', 'NOMBRE',
        'descripcion', 'Descripcion', 'DESCRIPCION', 'Descripción',
        'Articulo', 'articulo',
        'art nom', 'Art Nom', 'Artnom', 'ARTNOM', 'artnom',
        'nom_articulo', 'Nom Articulo', 'Nombre articulo',
    ], null)

    if (!colCodigo) {
        throw new Error(`No se encontró columna de código en Inventario. Encabezados: ${headers.join(', ')}`)
    }

    // Filtrar por bodegas 1185 y 1188, agrupar por código
    const groups = {}

    rows.forEach(row => {
        // Filtrar bodega si existe la columna
        if (colBodega) {
            const bodega = String(row[colBodega] || '').trim()
            if (!BODEGAS_VALIDAS.has(bodega)) return
        }

        const codigo = String(row[colCodigo] || '').trim()
        if (!codigo || codigo === 'undefined' || codigo === 'NaN') return

        const saldo = _num(row[colSaldo])
        const entradas = _num(row[colEntradas])
        const salidas = _num(row[colSalidas])
        const nombre = colNombre ? String(row[colNombre] || '').trim() : codigo

        if (!groups[codigo]) {
            groups[codigo] = { codigo, nombre, saldo_inicial: 0, entradas: 0, salidas: 0 }
        }
        groups[codigo].saldo_inicial += saldo
        groups[codigo].entradas += entradas
        groups[codigo].salidas += salidas
        if (nombre && nombre !== codigo) groups[codigo].nombre = nombre
    })

    const result = Object.values(groups).map(r => ({
        ...r,
        saldo_inicial: Math.round(r.saldo_inicial),
        entradas: Math.round(r.entradas),
        salidas: Math.round(r.salidas),
        saldo_actual: Math.max(0, Math.round(r.saldo_inicial + r.entradas - r.salidas)),
    })).sort((a, b) => a.codigo.localeCompare(b.codigo))

    console.log(`[INVENTARIO] Productos: ${result.length}, Stock total: ${result.reduce((s, r) => s + r.saldo_actual, 0)}`)

    return result
}

// ---------------------------------------------------------------------------
// 3. Parser de Consumo Histórico
// ---------------------------------------------------------------------------
export async function parseConsumoHistorico(file, diasPeriodo = 90) {
    const { rows, headers } = await _readExcel(file)

    // Columnas reales: C=bodega(2), G=codigo(6), K=cantidad(10), L=nombre(11), P=concepto(15)
    const colBodega = _findColumn(headers, [
        'servicio', 'Servicio', 'SERVICIO',
        'bodega', 'Bodega', 'BODEGA', 'almacen', 'Almacen', 'ALMACEN',
        'Cod Bodega', 'cod_bodega',
    ], 2)

    const colCodigo = _findColumn(headers, [
        'codigo', 'Codigo', 'CODIGO', 'Código', 'cod_articulo',
        'Cod Articulo', 'cod articulo', 'CodArticulo',
        'codigo del articulo', 'Codigo del articulo',
    ], 6)

    const colCantidad = _findColumn(headers, [
        'cantidad', 'Cantidad', 'CANTIDAD', 'qty', 'Qty', 'cant',
    ], 10)

    const colNombre = _findColumn(headers, [
        'Nombre articulo', 'nombre articulo', 'Nombre Articulo', 'NOMBRE ARTICULO',
        'nombre', 'Nombre', 'NOMBRE',
        'descripcion', 'Descripcion', 'DESCRIPCION', 'Descripción',
        'Articulo', 'articulo',
        'nom_articulo', 'Nom Articulo',
        'art nom', 'Art Nom', 'Artnom',
    ], 11)

    const colConcepto = _findColumn(headers, [
        'concepto', 'Concepto', 'CONCEPTO', 'Cod Concepto', 'cod_concepto',
    ], 15)

    if (!colCodigo) {
        throw new Error(`No se encontró columna de código en Consumo. Encabezados: ${headers.join(', ')}`)
    }

    // Conceptos válidos: 104 (cargo a paciente) y 105 (consumo interno)
    const CONCEPTOS_VALIDOS = new Set(['104', '105'])

    // Agrupar por código, separando consumo por concepto
    const groups = {}
    let totalFilas = 0
    let filasConcepto = 0

    rows.forEach(row => {
        totalFilas++

        // Filtrar por bodega
        if (colBodega) {
            const bodega = String(row[colBodega] || '').trim()
            if (!BODEGAS_VALIDAS.has(bodega)) return
        }

        // Filtrar por concepto 104 o 105
        if (colConcepto) {
            const concepto = String(row[colConcepto] || '').trim()
            if (!CONCEPTOS_VALIDOS.has(concepto)) return
        }

        filasConcepto++

        const codigo = String(row[colCodigo] || '').trim()
        if (!codigo || codigo === 'undefined' || codigo === 'NaN') return

        const cantidad = colCantidad ? _num(row[colCantidad]) : 1
        const nombre = colNombre ? String(row[colNombre] || '').trim() : codigo
        const concepto = colConcepto ? String(row[colConcepto] || '').trim() : '104'

        if (!groups[codigo]) {
            groups[codigo] = { codigo, nombre, total_consumo: 0, consumo_104: 0, consumo_105: 0 }
        }
        groups[codigo].total_consumo += cantidad
        if (concepto === '104') groups[codigo].consumo_104 += cantidad
        if (concepto === '105') groups[codigo].consumo_105 += cantidad
        if (nombre && nombre !== codigo) groups[codigo].nombre = nombre
    })

    const result = Object.values(groups).map(r => ({
        ...r,
        total_consumo: Math.round(r.total_consumo),
        consumo_104: Math.round(r.consumo_104),
        consumo_105: Math.round(r.consumo_105),
        consumo_promedio_diario: Math.round((r.total_consumo / Math.max(diasPeriodo, 1)) * 100) / 100,
        consumo_105_diario: Math.round((r.consumo_105 / Math.max(diasPeriodo, 1)) * 100) / 100,
    })).sort((a, b) => a.codigo.localeCompare(b.codigo))

    const total104 = result.reduce((s, r) => s + r.consumo_104, 0)
    const total105 = result.reduce((s, r) => s + r.consumo_105, 0)
    console.log(`[CONSUMO] Filas totales: ${totalFilas}, Filas concepto 104/105: ${filasConcepto}`)
    console.log(`[CONSUMO] Productos: ${result.length}, Consumo Paciente(104): ${total104}, Consumo Interno(105): ${total105}`)

    return result
}

// ---------------------------------------------------------------------------
// Pipeline completo con datos reales
// ---------------------------------------------------------------------------
export function processRealPipeline(inventario, canastas, consumo, diasProyeccion = 20) {
    // Días transcurridos del mes actual (para estimar consumo interno 105)
    const hoy = new Date()
    const diasDelMes = hoy.getDate()

    // 1. Base: inventario mensual
    const codigoMap = {}
    inventario.forEach(r => {
        codigoMap[r.codigo] = {
            codigo: r.codigo,
            nombre: r.nombre,
            saldo_inicial: r.saldo_inicial,
            entradas: r.entradas,
            salidas: r.salidas,
            stock_actual: r.saldo_actual,
            cantidad_comprometida: 0,
            total_consumo: 0,
            consumo_promedio_diario: 0,
            consumo_104: 0,
            consumo_105: 0,
            ajuste_consumo_interno: 0,
        }
    })

    // 1b. Enriquecer nombre si inventario no lo tiene
    const canastasMap = {}
    if (canastas && canastas.length > 0) {
        canastas.forEach(r => {
            canastasMap[r.codigo] = r
            if (codigoMap[r.codigo] && codigoMap[r.codigo].nombre === r.codigo && r.nombre && r.nombre !== r.codigo) {
                codigoMap[r.codigo].nombre = r.nombre
            }
        })
    }

    const consumoMap = {}
    if (consumo && consumo.length > 0) {
        consumo.forEach(r => {
            consumoMap[r.codigo] = r
            if (codigoMap[r.codigo] && codigoMap[r.codigo].nombre === r.codigo && r.nombre && r.nombre !== r.codigo) {
                codigoMap[r.codigo].nombre = r.nombre
            }
        })
    }

    // 2. Merge canastas (comprometido)
    Object.keys(codigoMap).forEach(codigo => {
        if (canastasMap[codigo]) {
            codigoMap[codigo].cantidad_comprometida = canastasMap[codigo].cantidad_comprometida
        }
    })

    // 3. Merge consumo (con detalle 104/105)
    Object.keys(codigoMap).forEach(codigo => {
        if (consumoMap[codigo]) {
            codigoMap[codigo].total_consumo = consumoMap[codigo].total_consumo
            codigoMap[codigo].consumo_promedio_diario = consumoMap[codigo].consumo_promedio_diario
            codigoMap[codigo].consumo_104 = consumoMap[codigo].consumo_104 || 0
            codigoMap[codigo].consumo_105 = consumoMap[codigo].consumo_105 || 0

            // Ajuste: consumo interno (105) NO está reflejado en las salidas del inventario
            // Estimamos el consumo interno del mes corriente usando el promedio diario de 105
            const consumo105Diario = consumoMap[codigo].consumo_105_diario || 0
            codigoMap[codigo].ajuste_consumo_interno = Math.round(consumo105Diario * diasDelMes)
        }
    })

    // 4. Cálculos centrales
    const df = Object.values(codigoMap).map(r => {
        // Stock real = saldo_actual - consumo interno estimado del mes (no reflejado en salidas)
        const stock_real = Math.max(0, r.stock_actual - r.ajuste_consumo_interno)
        // Disponible = stock real - comprometido en canastas
        const stock_disponible = Math.max(0, stock_real - r.cantidad_comprometida)
        const proyeccion_dias = Math.round(r.consumo_promedio_diario * diasProyeccion)
        const cobertura_dias = r.consumo_promedio_diario > 0
            ? Math.round((stock_disponible / r.consumo_promedio_diario) * 10) / 10
            : Infinity
        const cantidad_a_pedir = Math.max(0, proyeccion_dias - stock_disponible)
        const estado_riesgo = cobertura_dias < diasProyeccion ? 'Reabastecer' : 'OK'

        return {
            ...r,
            stock_real,
            stock_disponible,
            proyeccion_20_dias: proyeccion_dias,
            cobertura_dias: cobertura_dias === Infinity ? 9999 : cobertura_dias,
            cantidad_a_pedir,
            estado_riesgo,
        }
    })

    // Ordenar por cantidad_a_pedir (mayor primero)
    df.sort((a, b) => b.cantidad_a_pedir - a.cantidad_a_pedir)

    // 5. KPIs
    const totalProducts = df.length
    const totalStock = df.reduce((s, r) => s + r.stock_actual, 0)
    const totalCommitted = canastas ? canastas.reduce((s, r) => s + r.cantidad_comprometida, 0) : 0
    const totalAjusteInterno = df.reduce((s, r) => s + r.ajuste_consumo_interno, 0)
    const totalAvailable = df.reduce((s, r) => s + r.stock_disponible, 0)
    const totalToOrder = df.reduce((s, r) => s + r.cantidad_a_pedir, 0)
    const riskProducts = df.filter(r => r.estado_riesgo === 'Reabastecer').length
    const riskPct = Math.round((riskProducts / Math.max(totalProducts, 1)) * 1000) / 10
    const consumoPacienteTotal = consumo ? consumo.reduce((s, r) => s + (r.consumo_104 || 0), 0) : 0
    const consumoInternoTotal = consumo ? consumo.reduce((s, r) => s + (r.consumo_105 || 0), 0) : 0

    return {
        kpis: {
            total_products: totalProducts,
            total_stock: totalStock,
            total_committed: totalCommitted,
            total_ajuste_interno: totalAjusteInterno,
            total_available: totalAvailable,
            total_to_order: totalToOrder,
            risk_products: riskProducts,
            risk_pct: riskPct,
            consumo_paciente_total: consumoPacienteTotal,
            consumo_interno_total: consumoInternoTotal,
            dias_mes_corriente: diasDelMes,
        },
        reorder: df,
        consumption: consumo || [],
        stock: inventario,
    }
}

// ---------------------------------------------------------------------------
// Generador de datos demo
// ---------------------------------------------------------------------------
const CATEGORIAS = [
    ['Analgésico', ['Paracetamol', 'Ibuprofeno', 'Diclofenaco', 'Ketorolaco', 'Tramadol',
        'Naproxeno', 'Metamizol', 'Celecoxib', 'Meloxicam', 'Acetaminofén']],
    ['Antibiótico', ['Amoxicilina', 'Azitromicina', 'Ciprofloxacino', 'Cefalexina', 'Clindamicina',
        'Metronidazol', 'Levofloxacino', 'Doxiciclina', 'Ampicilina', 'Gentamicina']],
    ['Antiinflamatorio', ['Dexametasona', 'Prednisolona', 'Betametasona', 'Hidrocortisona',
        'Prednisona', 'Metilprednisolona', 'Budesonida', 'Fluticasona', 'Triamcinolona', 'Deflazacort']],
    ['Cardiovascular', ['Enalapril', 'Losartán', 'Amlodipino', 'Atenolol', 'Metoprolol',
        'Valsartán', 'Hidroclorotiazida', 'Furosemida', 'Espironolactona', 'Carvedilol']],
    ['Gastrointestinal', ['Omeprazol', 'Ranitidina', 'Metoclopramida', 'Loperamida',
        'Pantoprazol', 'Esomeprazol', 'Lansoprazol', 'Sucralfato', 'Domperidona', 'Bismuto']],
    ['Anestésico', ['Lidocaína', 'Bupivacaína', 'Propofol', 'Ketamina', 'Sevoflurano',
        'Fentanilo', 'Remifentanilo', 'Midazolam', 'Rocuronio', 'Atracurio']],
    ['Material Quirúrgico', ['Sutura Vicryl', 'Sutura Seda', 'Sutura Nylon', 'Gasa Estéril',
        'Vendaje Elástico', 'Guante Quirúrgico', 'Jeringa 10ml', 'Jeringa 5ml', 'Catéter IV', 'Sonda Foley']],
    ['Solución IV', ['Solución Salina 0.9%', 'Dextrosa 5%', 'Lactato Ringer', 'Solución Hartmann',
        'Manitol 20%', 'Albúmina 5%', 'Gelatina Succinilada', 'Solución Glucosada 10%', 'Bicarbonato Sodio', 'Cloruro Potasio']],
    ['Hemostático', ['Ácido Tranexámico', 'Vitamina K', 'Protamina', 'Fibrinógeno',
        'Complejo Protrombínico', 'Desmopresina', 'Aprotinina', 'Ácido Aminocaproico', 'Trombina Tópica', 'Celulosa Oxidada']],
    ['Otros', ['Heparina', 'Enoxaparina', 'Warfarina', 'Insulina NPH', 'Insulina Rápida',
        'Salbutamol', 'Bromuro Ipratropio', 'Oxígeno Medicinal', 'Adrenalina', 'Atropina']],
]

// Generador pseudo-aleatorio con semilla
function _seededRng(seed) {
    let s = seed
    return () => {
        s = (s * 1103515245 + 12345) & 0x7fffffff
        return s / 0x7fffffff
    }
}

export function generateDemoData(nProducts = 500, nDays = 90, seed = 42) {
    const rng = _seededRng(seed)
    const concentrations = ['50mg', '100mg', '250mg', '500mg', '1g', '5ml', '10ml', '20ml', '500ml', '1L', '']
    const allNames = []
    CATEGORIAS.forEach(([, names]) => {
        names.forEach(name => allNames.push(name))
    })

    // Generar catálogo de productos
    const products = []
    for (let i = 0; i < nProducts; i++) {
        const baseName = allNames[i % allNames.length]
        const suffix = i >= allNames.length ? ` ${Math.floor(i / allNames.length) + 1}` : ''
        const conc = concentrations[Math.floor(rng() * concentrations.length)]
        products.push({
            codigo: `MED-${String(i + 1001).padStart(5, '0')}`,
            nombre: `${baseName}${suffix} ${conc}`.trim(),
        })
    }

    // Generar inventario
    const inventario = products.map(p => {
        const profile = rng()
        let dailyMean
        if (profile < 0.15) dailyMean = 8 + rng() * 17
        else if (profile < 0.60) dailyMean = 2 + rng() * 6
        else dailyMean = 0.2 + rng() * 1.8

        const initialStock = Math.round(dailyMean * (25 + rng() * 20))
        const totalSalidas = Math.round(dailyMean * nDays * (0.8 + rng() * 0.4))
        const totalEntradas = Math.round(dailyMean * nDays * (0.3 + rng() * 0.5))

        return {
            codigo: p.codigo,
            nombre: p.nombre,
            saldo_inicial: initialStock,
            entradas: totalEntradas,
            salidas: totalSalidas,
            saldo_actual: Math.max(0, initialStock + totalEntradas - totalSalidas),
        }
    })

    // Generar canastas (20% de productos)
    const nKits = Math.round(nProducts * 0.2)
    const kitIndices = new Set()
    while (kitIndices.size < nKits) {
        kitIndices.add(Math.floor(rng() * nProducts))
    }
    const canastas = [...kitIndices].map(i => ({
        codigo: products[i].codigo,
        nombre: products[i].nombre,
        cantidad_comprometida: Math.round(5 + rng() * 75),
    }))

    // Generar consumo con split concepto 104/105
    const consumo = products.map(p => {
        const totalConsumo = Math.round(rng() * 500 + 10)
        const pct105 = rng() * 0.3  // 0-30% es consumo interno
        const consumo105 = Math.round(totalConsumo * pct105)
        const consumo104 = totalConsumo - consumo105
        return {
            codigo: p.codigo,
            nombre: p.nombre,
            total_consumo: totalConsumo,
            consumo_104: consumo104,
            consumo_105: consumo105,
            consumo_promedio_diario: Math.round((totalConsumo / nDays) * 100) / 100,
            consumo_105_diario: Math.round((consumo105 / nDays) * 100) / 100,
        }
    })

    // Procesar pipeline
    return processRealPipeline(inventario, canastas, consumo, 20)
}

// ---------------------------------------------------------------------------
// Exportar a Excel
// ---------------------------------------------------------------------------
export function exportToExcel(reorderData) {
    const today = new Date().toISOString().split('T')[0]

    // Preparar datos para el Excel
    const exportRows = reorderData.map(r => ({
        'Código': r.codigo,
        'Producto': r.nombre,
        'Stock Actual': r.stock_actual,
        'Comprometido Kits': r.cantidad_comprometida,
        'Ajuste C. Interno': r.ajuste_consumo_interno || 0,
        'Stock Real': r.stock_real || r.stock_actual,
        'Disponible': r.stock_disponible,
        'Consumo Paciente (3M)': r.consumo_104 || 0,
        'Consumo Interno (3M)': r.consumo_105 || 0,
        'Consumo/Día': r.consumo_promedio_diario,
        'Cobertura (Días)': r.cobertura_dias >= 9999 ? 'Sin consumo' : r.cobertura_dias,
        'Proyección': r.proyeccion_20_dias,
        'Cantidad a Pedir': r.cantidad_a_pedir,
        'Estado': r.estado_riesgo,
    }))

    const ws = XLSX.utils.json_to_sheet(exportRows)

    // Ajustar ancho de columnas
    ws['!cols'] = [
        { wch: 12 },  // Código
        { wch: 35 },  // Producto
        { wch: 12 },  // Stock Actual
        { wch: 15 },  // Comprometido Kits
        { wch: 15 },  // Ajuste C. Interno
        { wch: 12 },  // Stock Real
        { wch: 12 },  // Disponible
        { wch: 18 },  // Consumo Paciente
        { wch: 18 },  // Consumo Interno
        { wch: 12 },  // Consumo/Día
        { wch: 15 },  // Cobertura
        { wch: 12 },  // Proyección
        { wch: 15 },  // Cantidad a Pedir
        { wch: 12 },  // Estado
    ]

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Pedido Reabastecimiento')

    // Descargar
    XLSX.writeFile(wb, `pedido_reabastecimiento_${today}.xlsx`)
}
