# Estándar de Análisis de Archivos LAS con Python (Workflow Jupyter)

Este documento resume las mejores prácticas de la industria para el manejo, procesamiento y análisis de registros de pozos (Logs) utilizando entornos modernos de Python. Esta es la base lógica sobre la que se construye el motor `backend_api.py` de DataTerra.

## 1. Introducción: ¿Por qué Jupyter/Python para archivos LAS?
Los archivos **LAS (Log ASCII Standard)** son el estándar universal para datos de subsuelo (versión 2.0 es la más común). Tradicionalmente se analizaban en software costoso y cerrado. El uso de **Jupyter Notebooks (y Python)** ofrece:
*   **Interactividad:** Ejecución de código celda por celda para inspección inmediata.
*   **Reproducibilidad:** El código documenta exactamente qué limpieza se hizo a los datos.
*   **Flexibilidad:** Acceso a librerías de Machine Learning (`scikit-learn`) y Estadística (`pandas`).

---

## 2. Flujo de Trabajo Técnico (Pipeline)

El proceso estándar descrito por expertos de la industria sigue estos 4 pasos cruciales:

### A. Carga y Exploración (`lasio`)
*   **Herramienta:** Librería `lasio`.
*   **Acción:** Leer el archivo crudo (`lasio.read(archivo)`).
*   **Objetivo:** Explorar las secciones de metadatos sin tocar los datos aún:
    *   *~Warning / Version*: Versión del estándar.
    *   *~Well*: Cabezal del pozo (Ubicación, Operadora, Profundidad Inicial/Final).
    *   *~Curve*: Qué curvas existen y sus unidades (mportante para detectar si PHI está en % o v/v).
    *   *~Parameter*: Parámetros de corrida (Lodo, temperatura).

### B. Conversión a Estructura Tabular (`pandas`)
*   **El paso crítico:** Convertir el objeto LAS a un **DataFrame**.
*   **Código:** `df = las.df()`.
*   **Ventaja:** Convierte una estructura de texto secuencial en una tabla SQL-like donde:
    *   El índice es la Profundidad (DEPT).
    *   Las columnas son las Curvas (GR, RHOB, NPHI).
    *   Permite operaciones vectorizadas (restar dos curvas en una sola línea de código).

### C. Manipulación y Limpieza (Data Cleaning)
Antes de visualizar, los datos requieren higiene:
1.  **Filtrado de Nulos:** Manejo de valores `-999.25` (estándar de nulo en LAS).
2.  **Normalización de Curvas:** (e.g., renombrar `CGR` a `GR`).
3.  **Conversión de Unidades:** Detectar si Porosidad > 1.0 (está en %) y dividir por 100. *Este es un error común que distorsiona las visualizaciones.*
4.  **Cálculo de Curvas Derivadas:** Crear nuevas columnas (e.g., `df['VSH']`) usando fórmulas matemáticas sobre las columnas existentes.

### D. Visualización y Control de Calidad
*   Generar "Tracks" (pistas) visuales.
*   Histogramas para ver la distribución de datos (QC de rangos).
*   Crossplots (Gráficos cruzados) para identificación litológica (e.g., NPHI vs RHOB).

---

## 3. Beneficios Clave Aplicados en DataTerra

Nuestro sistema **SaaS** automatiza este flujo que normalmente haría un petrofísico manualmente en un Notebook:

| Tarea Manual en Jupyter | Automatización en DataTerra |
| :--- | :--- |
| `lasio.read('archivo.las')` | **Carga Drag & Drop** en el Dashboard. |
| `df.describe()` | **Tabla de Estadísticas** generada automáticamente. |
| `plt.plot(df['GR'])` | **Visualizador Web Interactivo** (React/Recharts). |
| Detección visual de Pay | **ReservoirDetector** (Algoritmo Python automático). |
| Edición de Curvas | **Normalizador Automático** en el Backend. |

---

## 4. Referencias
*   Librerías Core: `lasio`, `pandas`, `numpy`.
*   Estándar: CWLS (Canadian Well Logging Society) LAS 2.0.
