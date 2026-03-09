# Frontend - Sistema de Reabastecimiento

Este directorio contiene el código fuente de la interfaz de usuario (Cliente) del Sistema de Reabastecimiento de Clínica Vida, desarrollada utilizando herramientas web modernas y un enfoque SPA (Single Page Application).

## Stack Tecnológico
*   **Framework:** React 18
*   **Build Tool:** Vite (reemplazo ultrarrápido a Create React App)
*   **Estilos:** Vanilla CSS (CSS puro) apoyado en variables CSS globales para el Design System y Flexbox/CSS Grid para el layout responsivo.
*   **Gráficos:** Recharts (Librería de visualización de datos basada en D3.js y componentes React).

## Arquitectura y Layout

El diseño visual está concebido bajo el concepto **"Fit-to-Screen" en Escritorio**, lo cual significa que el contenedor principal (`body`) nunca mostrará una barra de scroll lateral en monitores grandes. En su lugar, el scroll es *interno*, aplicado únicamente a la tabla de datos (`.data-table-wrapper`). Esto mejora sustancialmente la experiencia administrativa al mantener siempre fijos los KPIs y la cabecera. En contraste, en pantallas móviles (`<768px`) la estructura muta a un documento de scroll vertical estándar para maximizar el área táctil.

### Componentes Clave (`src/components/`)
*   **`App.jsx`:** Componente orquestador. Maneja el estado principal (`data`, `loading`, carga de archivos) y gestiona las llamadas HTTP asíncronas vía `fetch` contra el Backend REST.
*   **`Sidebar.jsx`:** Menú de navegación lateral responsivo. Incluye efectos de neón "Aura Cyan" utilizando pseudo-elementos (`::before`). En móviles se oculta bajo un menú tipo hamburguesa con un *overlay* de opacidad.
*   **`Dashboard.jsx`:** Orquesta la vista cuando existen datos cargados, condicionalmente inyectando el componente de tabla o de gráficos en el Flex Container reservado (para mantener el height dinámico `100vh`).
*   **`DataTable.jsx`:** Componente analítico pesado. Encargado de mostrar las métricas críticas de cada insumo con un buscador predictivo en memoria del cliente y sistema simple de reordenamiento (sort) de filas.
*   **`Charts.jsx`:** Integración de la librería *Recharts* envolviendo los componentes en envoltorios *ResponsiveContainer*.

## Comandos Útiles

```bash
# Instalación de dependencias (solo la primera vez)
npm install

# Levantar entorno de desarrollo con Hot Module Replacement (HMR) en el puerto por defecto 5173
npm run dev

# Compilar para producción (generará la carpeta estática 'dist/')
npm run build

# Previsualizar la build de producción en local
npm run preview
```

## Consideraciones de Integración
Por defecto, la constante `API_BASE` dentro de `App.jsx` apunta a `http://localhost:8000`. Cuidado al desplegar en producción; esta variable requerirá externalizarse a variables de entorno (`.env`) en Vite en el contexto de despliegue real en el servidor.
