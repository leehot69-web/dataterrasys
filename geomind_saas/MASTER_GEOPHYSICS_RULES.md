# Manual de Referencia Técnica: Geofísica y Ciencia de Datos Aplicada

Este documento define los estándares técnicos para el desarrollo de GeoMind, integrando fundamentos de geofísica, ciencia de datos y mejores prácticas de la industria (SEG, SPE, AAPG, Swung).

## 1. Fundamentos de Adquisición y Procesamiento (Estándares SEG)
Para garantizar la integridad científica, el software debe adherirse a los estándares del **SEG Technical Standards Committee**.

*   **Fuentes de Verdad:** 
    *   *Seismic Data Analysis* (Öz Yilmaz).
    *   *Encyclopedic Dictionary of Applied Geophysics* (Robert Sheriff).
    *   **SEG Wiki** para algoritmos estándar.
*   **Validación:** Uso de datos sintéticos del **SEG Advanced Modeling (SEAM)** para probar algoritmos nuevos antes de desplegarlos.
*   **Código:** Referenciar *Geophysical Software and Algorithms* (Revista Geophysics) para implementaciones numéricas complejas.

## 2. Manejo de Datos y Estructuras (LAS & Sísmica)
La gestión de índices y metadatos es crítica. No se deben usar arrays crudos que pierdan el contexto geológico.

*   **xarray sobre NumPy:** 
    *   Para datos multidimensionales (sísmica, registros múltiples), usar `xarray.DataArray` o `Dataset`.
    *   **Regla:** Los datos deben ser indexables por sus coordenadas físicas reales (Profundidad MD, TVD, Tiempo TWT) y no solo por índices de matriz `ii, jj`.
*   **Preservación de Metadatos:**
    *   Los objetos de datos deben conservar cabezales originales (UWI, coordenadas, parámetros de adquisición) en los atributos del objeto (`.attrs`).
*   **Interoperabilidad:** Facilidad de conversión fluida entre `xarray` y `pandas.DataFrame` para exportación y visualización tabular.

## 3. Metodologías de Exploración (SPE & AAPG)
El análisis no es solo matemático, debe tener sentido geológico e ingenieril.

*   **Terminología:** Adherirse al **Petroleum Engineering Handbook** y **OnePetro** para nombres de variables y unidades.
*   **Reproducibilidad:** Los flujos de trabajo deben ser auditables. Si un usuario obtiene un Vshale de 0.4, debe ser claro qué parámetros (GR_matrix, GR_sand) se usaron.
*   **Contexto Geológico:** Integrar conceptos de **AAPG Datapages** (mapas de facies, ambientes depositacionales) en las visualizaciones (ej. no solo mostrar curvas, sino interpretar litologías).

## 4. Stack Tecnológico para Automatización (Python)
Las herramientas seleccionadas deben ser robustas y escalables.

*   **xarray:** Para manejo de cubos sísmicos y registros de pozo alineados por profundidad. Habilita selección semántica: `pozo.sel(depth=2500)`.
*   **redflag:** **MANDATORIO para ML.**
    *   Detectar desbalance de clases (ej. muchas lutitas, pocas arenas).
    *   Monitorear correlación en profundidad (autocorrelación) para evitar fugas de datos en splits de entrenamiento/test.
    *   Usar métricas como *Wasserstein distance* para validar que los datos de entrenamiento se parecen a los datos de producción.
*   **Dask:** Para procesar archivos SEGY grandes o lotes de miles de pozos sin saturar la RAM (Out-of-core computing).
*   **Scikit-learn Pipelines:** Integrar pasos de limpieza (`ImbalanceDetector`, `OutlierDetector`) dentro del pipeline de predicción.

## 5. Integridad y Auditoría (Quality Control)
El software debe proteger al usuario de errores geológicos comunes.

*   **Data Entrance Exam:** Al cargar un LAS o SEGY, ejecutar un chequeo automático:
    *   ¿Curvas con valores nulos o negativos imposibles (ej. Densidad < 0)?
    *   ¿Unidades incorrectas (m/m3 vs g/cc)?
*   **Lógica de Negocio Geológica:**
    *   No permitir cálculos de Sw si la Porosidad es 0.
    *   Alertar si se aplican modelos de areniscas en zonas de carbonatos.
*   **Open Source:** Mantener alineación con la comunidad **Software Underground (Swung)** para adoptar librerías modernas y seguras.

---
*Este documento es la autoridad técnica para cualquier decisión de arquitectura o algoritmo en GeoMind.*
