# Nostra BI - Sistema de Reabastecimiento Clínica Vida

Bienvenido al repositorio del Sistema de Reabastecimiento desarrollado por Nostra para la Clínica Vida. 

Este sistema es una herramienta integral diseñada para optimizar y automatizar el proceso de gestión de inventarios y control de reabastecimiento de medicamentos e insumos médicos, específicamente para las bodegas 1185 y 1188.

## ¿Qué hace este sistema?

El sistema ayuda al personal operativo y directivo a tomar decisiones informadas sobre qué productos deben ser pedidos, en qué cantidades y en qué momento, minimizando el riesgo de quedarse sin stock (ruptura de inventario).

### Características Principales:

*   **Visión Unificada:** Consolida los movimientos de inventario diarios y el stock comprometido en canastas (kits de procedimientos) para dar una imagen precisa del inventario real disponible.
*   **Proyección Inteligente:** Analiza el consumo promedio diario histórico de cada producto para proyectar la demanda futura y calcular el número de días de cobertura.
*   **Gestión de Alertas Visuales:** Resalta automáticamente qué productos están por debajo del nivel óptimo de inventario y requieren ser reabastecidos con urgencia.
*   **Exportación Automatizada:** Permite consolidar y descargar con un solo click un informe en Excel (`pedido_reabastecimiento.xlsx`) listo para ser procesado por compras.
*   **Diseño Corporativo e Innovador:** Interfaz de usuario moderna, rápida y amigable, con modo escritorio optimizado ("pantalla fija") y diseño adaptativo para celulares, adaptada a la marca corporativa de Clínica Vida.

## Estructura del Proyecto

Este software está dividido en dos partes principales (arquitectura Cliente-Servidor) para asegurar su velocidad y escalabilidad futura a más módulos de la clínica:

1.  **Frontend (El rostro del sistema):** La interfaz visual donde los usuarios interactúan. Lee más sobre ella en la carpeta `frontend/`.
2.  **Backend (El cerebro del sistema):** El motor matemático y base de procesamiento que recibe los archivos Excel descargados del ERP, realiza los cálculos logísticos y envía la información al Frontend. Lee más en la carpeta `backend/`.

## Empezando Rápidamente
Para desarrolladores o personal técnico que busque arrancar el sistema en su equipo local:

1. Enciende el motor de procesamiento (Backend) usando Python.
2. Enciende la interfaz visual (Frontend) usando Node.js.
3. El sistema estará disponible entrando a `http://localhost:5173` desde el navegador.

*Para detalles técnicos de configuración, referirse a los archivos README dentro de cada carpeta (`backend/README.md` y `frontend/README.md`).*