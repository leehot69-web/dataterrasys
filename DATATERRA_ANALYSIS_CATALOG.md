# 📖 DATATERRA — Catálogo Completo de Análisis Petrofísicos
### Versión 2.0 | Febrero 2026
### Plataforma de Inteligencia de Subsuelo

---

> **Propósito**: Este documento cataloga cada módulo analítico de DataTerra,
> describiendo su fundamento científico, entradas, salidas y estado de implementación.
> Sirve como referencia técnica interna y como base para documentación de producto.

---

## 📑 ÍNDICE

| #  | Módulo                                    | Categoría        | Estado        |
|:---|:------------------------------------------|:-----------------|:--------------|
| 01 | Carga y Parsing de Archivos LAS           | Datos            | ✅ Producción |
| 02 | Normalización de Curvas (Aliasing)        | Datos            | ✅ Producción |
| 03 | Estandarización de Unidades               | Datos            | ✅ Producción |
| 04 | Auditoría Forense de Datos                | Calidad          | ✅ Producción |
| 05 | Volumen de Arcilla (Vsh)                  | Petrofísica      | ✅ Producción |
| 06 | Porosidad Efectiva (PHI)                  | Petrofísica      | ✅ Producción |
| 07 | Saturación de Agua — Archie               | Petrofísica      | ✅ Producción |
| 08 | Saturación de Agua — Simandoux            | Petrofísica      | ✅ Producción |
| 09 | Permeabilidad — Timur-Coates              | Petrofísica      | ✅ Producción |
| 10 | Permeabilidad — Log-Linear Poro-Perm      | Petrofísica      | ✅ Producción |
| 11 | Permeabilidad — Morris-Biggs              | Petrofísica      | ✅ Producción |
| 12 | Detección de Pay Zones                    | Reservorio       | ✅ Producción |
| 13 | Calidad de Roca (RQI) — Radar 5 Ejes     | Reservorio       | ✅ Producción |
| 14 | Litho-Scanner 3D (Cubo Volumétrico)       | Geología         | ✅ Producción |
| 15 | Electrofacies — PCA + K-Means Clustering  | Machine Learning | ✅ Producción |
| 16 | PCA (Análisis de Componentes Principales) | Machine Learning | ✅ Producción |
| 17 | Crossplot NPHI-RHOB (Efecto Gas)          | Petrofísica      | 🔶 Pendiente  |
| 18 | Impedancia Acústica                       | Geofísica        | ✅ Producción |
| 19 | Coeficientes de Reflexión                 | Geofísica        | ✅ Producción |
| 20 | Ondícula Ricker                           | Geofísica        | ✅ Producción |
| 21 | Sismograma Sintético                      | Geofísica        | ✅ Producción |
| 22 | Well Tie (Dynamic Time Warping)           | Geofísica        | 🔶 Pendiente  |
| 23 | Dog-Leg Severity (DLS)                    | Perforación      | ✅ Producción |
| 24 | Análisis Nodal (IPR vs VLP)               | Producción       | ✅ Producción |
| 25 | Pronóstico Arps — Declinación Exponencial | Producción       | ✅ Producción |
| 26 | Pronóstico Arps — Declinación Hiperbólica | Producción       | ✅ Producción |
| 27 | OOIP (Petróleo Original en Sitio)         | Producción       | ✅ Producción |
| 28 | Histogramas de Distribución               | Estadística      | ✅ Producción |
| 29 | Correlación de Pearson                    | Estadística      | ✅ Producción |
| 30 | 4D Bubble Plot                            | Estadística      | ✅ Producción |
| 31 | Sombreado Litológico en Track             | Visualización    | 🔶 Pendiente  |
| 32 | Correlación Multi-Pozo                    | Visualización    | 🔶 Pendiente  |
| 33 | Exportación LAS 2.0                       | Exportación      | ✅ Producción |
| 34 | Exportación PDF Técnico                   | Exportación      | ✅ Producción |
| 35 | Exportación HTML Responsivo               | Exportación      | ✅ Producción |
| 36 | Exportación CSV                           | Exportación      | ✅ Producción |

---

## CATEGORÍA 1: GESTIÓN DE DATOS

---

### 01. Carga y Parsing de Archivos LAS
**Estado**: ✅ Producción  
**Categoría**: Datos  
**Clase**: `DataLoader`  
**Archivo**: `petro_core_web.py`  

**Descripción**:  
El formato Log ASCII Standard (LAS) es el estándar predominante de la industria (CWLS)
para el intercambio de datos de geociencias. Este módulo lee archivos LAS 2.0 y los
convierte en DataFrames de pandas para análisis computacional. Maneja múltiples
codificaciones (UTF-8, Latin-1) para compatibilidad con archivos generados por
diferentes servicios de wireline (Schlumberger, Halliburton, Baker Hughes).

**Entradas**: Archivo `.LAS` (binario o texto)  
**Salidas**: Objeto `lasio`, DataFrame `pandas` con curvas como columnas  
**Curvas Soportadas**: Todas las registradas en el archivo  
**Dependencias**: `lasio`, `pandas`  

**Limitación Actual**: Procesa un archivo a la vez (no multi-pozo).

---

### 02. Normalización de Curvas (Aliasing)
**Estado**: ✅ Producción  
**Categoría**: Datos  
**Clase**: `CurveNormalizer`  
**Archivo**: `petro_core_web.py`  

**Descripción**:  
Los diferentes proveedores de wireline usan mnemónicos distintos para la misma curva
(ej: GAMMA, GAPI, GAM, GRC, SGR → todos son Gamma Ray). Este módulo mapea
automáticamente cualquier nombre de curva a un mnemónico estándar usando una base
de datos de alias que cubre los principales servicios:

| Curva Estándar | Alias Reconocidos                                               |
|:---------------|:----------------------------------------------------------------|
| GR             | GR, GAMMA, GAPI, GAM, CGR, GAMMARAY, G_RAY, GRC, SGR, NGT     |
| NPHI           | NPHI, NEU, TNPH, PHIN, CN, CNCF, NPOR, NEUTRON                |
| RHOB           | RHOB, DEN, RHOZ, DENSITY, ZDEN, BDEN, FDC                      |
| RT             | RT, RES, RD, ILD, LLD, RESISTIVITY, AT90, RDEEP, HRLD, HDRS   |
| DT             | DT, DTC, DTCO, AC, SONIC, DT4P, DT_COMP, DTCO_LS              |

**Entradas**: DataFrame con columnas de nombres arbitrarios  
**Salidas**: DataFrame con columnas renombradas a estándar  

---

### 03. Estandarización de Unidades
**Estado**: ✅ Producción  
**Categoría**: Datos  
**Archivo**: `backend_api.py` (PASO 1B)

**Descripción**:  
Asegura consistencia dimensional automática. Detecta la unidad por rango estadístico
(mediana) y convierte a estándar petrofísico:

| Curva | Detección                  | Conversión Automática           |
|:------|:---------------------------|:--------------------------------|
| NPHI  | mediana > 1.0 → está en % | ÷ 100 → v/v decimal            |
| RHOB  | mediana > 100 → kg/m³     | ÷ 1000 → g/cm³                 |
| DT    | mediana > 300 → μs/m      | ÷ 3.2808 → μs/ft               |

**Salidas**: Lista `unit_conversions` en JSON con {curve, from, to, factor}.
**Impacto**: Garantiza cálculos de impedancia, porosidad y densidad correctos.

---

### 04. Auditoría Forense de Datos
**Estado**: ✅ Producción  
**Categoría**: Calidad  
**Clase**: `DataQualityAuditor`  
**Archivo**: `petro_core_web.py`  

**Descripción**:  
Implementa un "Entrance Exam" tipo SEG Standard Audit que certifica que los datos
fueron leídos completamente y que cada cálculo posterior tiene trazabilidad. Genera
un log forense que incluye:

- ✅ Total de líneas cargadas (confirmación de lectura completa)
- 📏 Cobertura de profundidad (inicio, fin, metraje total)
- 🔍 Detección de curvas esenciales (GR, NPHI, RHOB, RT)
- ⚙️ Confirmación de cada cálculo ejecutado (VSH, PHI, SW, PERM, FACIES, DLS)
- 📊 Porcentaje de datos válidos por curva crítica
- ⚠️ Alertas automáticas si la integridad de datos baja de 90%

**Entradas**: DataFrame procesado  
**Salidas**: Lista de mensajes de auditoría (texto enriquecido)  
**Estándar de Referencia**: SEG Data Quality Standards  

---

## CATEGORÍA 2: PETROFÍSICA DETERMINÍSTICA

---

### 05. Volumen de Arcilla (Vsh)
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  
**Clase**: `PetrofisicaCore.calcular_vsh()`  
**Archivo**: `petro_core_web.py`  

**Descripción**:  
El Volumen de Arcilla es el primer parámetro calculado y la base de todas las
correcciones posteriores. Cuantifica la fracción de minerales arcillosos presentes
en la formación, afectando directamente la porosidad efectiva y la saturación.

**Métodos Implementados**:

1. **Lineal** (IGR directo):
   ```
   Vsh = (GR_log - GR_min) / (GR_max - GR_min)
   ```

2. **Larionov (Terciario)** — Para formaciones jóvenes no consolidadas:
   ```
   Vsh = 0.083 × (2^(3.7 × IGR) - 1)
   ```

3. **Steiber** — Modelo más conservador, recomendado para arenas arcillosas:
   ```
   Vsh = IGR / (3 - 2 × IGR)
   ```

**GR_min y GR_max**: Se calculan automáticamente usando percentiles P05 y P95
de la curva GR, eliminando la necesidad de selección manual y reduciendo el
impacto de valores atípicos (spikes, washouts).

**Entradas**: Curva GR, método ('linear', 'larionov', 'steiber')  
**Salidas**: Curva VSH (0.0 = arena limpia, 1.0 = lutita pura)  
**Rango Válido**: 0.0 – 1.0 (clipeado)  

---

### 06. Porosidad Efectiva (PHI)
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  

**Descripción**:  
La porosidad cuantifica el espacio vacío en la roca disponible para almacenar
fluidos (hidrocarburos o agua). DataTerra calcula la porosidad usando la mejor
combinación de datos disponible:

**Método primario** — Densidad-Neutrón (si NPHI y RHOB están presentes):
```
PHI = (NPHI + PHI_density) / 2
PHI_density = (RHOB_matrix - RHOB_log) / (RHOB_matrix - RHOB_fluid)
```
Donde: `RHOB_matrix = 2.65 g/cm³` (cuarzo), `RHOB_fluid = 1.0 g/cm³` (agua).

**Método fallback** — Sónico (si solo DT está disponible):
```
PHI_sonic = (DT_log - DT_matrix) / (DT_fluid - DT_matrix)
```
Donde: `DT_matrix = 55.5 μs/ft` (arena), `DT_fluid = 189 μs/ft`.

**Corrección por Arcilla**: La porosidad efectiva corrige por el volumen de arcilla:
```
PHI_effective = PHI_total × (1 - VSH)
```

**Entradas**: NPHI, RHOB (o DT como fallback), VSH  
**Salidas**: Curva PHI (v/v, 0.0 – 0.40)  

---

### 07. Saturación de Agua — Modelo de Archie
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  
**Clase**: `PetrofisicaCore.calcular_sw()`  

**Descripción**:  
El modelo clásico de Archie (1942) estima la saturación de agua en formaciones
limpias (sin arcilla significativa). Es la base de toda la evaluación de
hidrocarburos en petrofísica convencional.

**Fórmula**:
```
Sw = [(a × Rw) / (PHI^m × Rt)]^(1/n)
```

**Parámetros**:
| Parámetro | Símbolo | Valor Default | Descripción                              |
|:----------|:--------|:--------------|:-----------------------------------------|
| Tortuosidad | a    | 1.0           | Factor de cementación (Humble: 0.62)     |
| Cementación | m    | 2.0           | Exponente de porosidad (rango: 1.8–2.2)  |
| Saturación  | n    | 2.0           | Exponente de saturación                  |
| Rw          | Rw   | 0.05 Ω·m     | Resistividad del agua de formación       |

**Entradas**: RT, PHI, Rw, a, m, n  
**Salidas**: Curva SW (v/v, 0.0 – 1.0)  
**Limitación**: No es preciso en arenas arcillosas (usar Simandoux).  

---

### 08. Saturación de Agua — Modelo de Simandoux
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  
**Clase**: `PetrofisicaCore.calcular_sw_simandoux()`  

**Descripción**:  
Para reservorios con contenido arcilloso significativo (Vsh > 15%), el modelo de
Archie subestima la saturación de hidrocarburos porque la arcilla aporta
conductividad adicional que se confunde con agua. Simandoux (1963) corrige este
efecto incorporando la resistividad de la arcilla:

**Fórmula**:
```
1/Rt = (Vsh × Sw) / Rsh + (PHI^m × Sw^n) / (a × Rw)
```

**Resuelve cuadráticamente para Sw**, proporcionando una estimación más precisa
en zonas de baja resistividad donde Archie puede omitir pay zones productivas.

**Parámetros adicionales**:
| Parámetro | Símbolo | Valor Default | Descripción                     |
|:----------|:--------|:--------------|:--------------------------------|
| Rsh       | Rsh     | 2.0 Ω·m      | Resistividad de la lutita       |

**Entradas**: RT, PHI, VSH, Rw, Rsh, a, m, n  
**Salidas**: Curva SW corregida por arcilla  
**Ventaja**: Reduce falsos negativos en reservorios arcillosos.  

---

### 09. Permeabilidad — Timur-Coates (Free-Fluid)
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  
**Clase**: `PetrofisicaCore.calcular_permeabilidad()`  

**Descripción**:  
Estima la capacidad de flujo del medio poroso usando la relación entre porosidad
y saturación de agua irreducible (Swirr). Este modelo considera la geometría del
poro y la distribución de fluidos.

**Fórmula**:
```
K = C × PHI^4 × [(1 - Swirr) / Swirr]²
```
Donde `C` es una constante de calibración (typical: 10,000 para areniscas).

**Entradas**: PHI, SW_irreducible  
**Salidas**: Curva K (mD, rango: 0.001 – 50,000)  

---

### 10. Permeabilidad — Log-Linear Poro-Perm
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  

**Descripción**:  
Modelo de regresión log-lineal calibrado para areniscas del tipo sandstone,
que proporciona una estimación rápida sin necesidad de datos de saturación
irreducible.

**Fórmula**:
```
K = 10^(14 × PHI - 1.5)
```

**Calibración**: Derivada de correlaciones publicadas para formaciones clásticas
del Terciario. Los coeficientes (a=14, b=-1.5) representan una calibración
genérica que puede ajustarse con datos de núcleo.

**Entradas**: PHI  
**Salidas**: Curva PERM (mD, clipeada 0.001 – 50,000)  

---

### 11. Permeabilidad — Morris-Biggs
**Estado**: ✅ Producción  
**Categoría**: Petrofísica  
**Archivo**: `backend_api.py` (después de Timur-Coates)

**Descripción**:  
Modelo que relaciona permeabilidad con porosidad efectiva y saturación de agua
irreducible. Curva PERM_MB generada con comparación automática de los 3 métodos.

**Fórmula** (para arenas):
```
K = 62,500 × PHI³ × Swirr
```

**Salidas**: Curva `PERM_MB`, objeto `perm_comparison` con promedios comparativos.  
**Ventaja**: El JSON de respuesta incluye `perm_comparison.timur_coates_avg`,
`perm_comparison.morris_biggs_avg`, y `perm_comparison.log_linear_avg`.

---

## CATEGORÍA 3: EVALUACIÓN DE RESERVORIO

---

### 12. Detección de Pay Zones
**Estado**: ✅ Producción  
**Categoría**: Reservorio  
**Clase**: `ReservoirDetector.detect_prospect_intervals()`  

**Descripción**:  
Identifica automáticamente los intervalos productivos del pozo usando umbrales
(cut-offs) sobre tres parámetros críticos. Solo las profundidades que cumplen
TODOS los criterios simultáneamente se clasifican como "pay":

**Criterios de Cut-off**:
| Parámetro | Cut-off   | Lógica                           |
|:----------|:----------|:---------------------------------|
| VSH       | < 0.40    | Zona con arcilla aceptable       |
| PHI       | > 0.08    | Porosidad mínima para almacenar  |
| SW        | < 0.60    | Saturación de HC significativa   |

**Salidas**: DataFrame con columnas: Top (ft), Base (ft), Thickness (ft), Quality.  
**Aplicación**: Cálculo de Net Pay, planificación de completación.

---

### 13. Calidad de Roca (RQI) — Radar Multidimensional
**Estado**: ✅ Producción  
**Categoría**: Reservorio  

**Descripción**:  
Evalúa la calidad del reservorio en 5 dimensiones simultáneas, presentadas como
un gráfico de radar (spider chart) con scoring de 0 a 100%:

| Eje               | Qué Mide                                          | Fórmula de Score                     |
|:-------------------|:---------------------------------------------------|:-------------------------------------|
| Porosidad          | Capacidad de almacenamiento                        | PHI_avg / 0.25 × 100                |
| Saturación HC      | Contenido de hidrocarburos                         | (1 - SW_avg) / 0.70 × 100           |
| Limpieza           | Inverso de arcillosidad                            | (1 - VSH_avg) / 1.0 × 100           |
| Potencial Económico| Viabilidad de producción                           | Score combinado de K y Net Pay       |
| Calidad de Datos   | Confiabilidad de las mediciones                    | % datos válidos (no-null)            |

**Clasificación Final**:
| Score Global | Categoría  | Recomendación                        |
|:-------------|:-----------|:-------------------------------------|
| 80 – 100%    | Excelente  | Completación prioritaria             |
| 60 – 79%     | Buena      | Interés secundario; estimulación     |
| 40 – 59%     | Regular    | Marginal; riesgo de agua             |
| < 40%        | Pobre      | No productiva; sello o barrera       |

---

## CATEGORÍA 4: GEOLOGÍA Y VISUALIZACIÓN 3D

---

### 14. Litho-Scanner 3D (Cubo Volumétrico)
**Estado**: ✅ Producción  
**Categoría**: Geología  

**Descripción**:  
Cubo volumétrico 3D interactivo construido con Plotly que permite visualizar
heterogeneidades espaciales del reservorio. Cada punto del cubo representa una
muestra de profundidad, con coordenadas basadas en propiedades petrofísicas.

**Ejes del Cubo**:
- **X**: Porosidad (PHI)
- **Y**: Densidad (RHOB)
- **Z**: Profundidad (DEPT)

**Código de Colores** (seleccionable):
- GR (arcillosidad)
- VSH (volumen de arcilla)
- PHI (porosidad)
- SW (saturación)
- K (permeabilidad)

**Interactividad**: Rotación 3D, zoom, hover con datos punto a punto.

---

### 17. Crossplot NPHI-RHOB (Efecto Gas)
**Estado**: 🔶 Pendiente  
**Categoría**: Petrofísica  

**Descripción**:  
El crossplot de Porosidad Neutrón vs Densidad es la herramienta principal para
identificar litología y detectar la presencia de gas. Cuando un punto cae a la
IZQUIERDA de la línea de arena (NPHI bajo, RHOB bajo), indica "efecto de gas":

```
                NPHI →
    0.45   0.30   0.15   0.00  -0.05
     |      |      |      |      |
2.0 ─┤──────┤──────┤──────┤──────┤─ GAS ZONE ↑
     │            ╱                
2.2 ─┤──────────╱── Arena ────────┤
     │        ╱                    
2.4 ─┤──────╱───── Caliza ────────┤
     │    ╱                        
2.6 ─┤──╱──────── Dolomita ───────┤
     │╱                            
2.8 ─┤────────────────────────────┤
```

**Líneas de Referencia**: Cuarzo (2.65), Caliza (2.71), Dolomita (2.87).
**Salida**: Gráfico crossplot con overlay litológico y colores por VSH o profundidad.

---

## CATEGORÍA 5: MACHINE LEARNING

---

### 15. Electrofacies — PCA + K-Means Clustering
**Estado**: ✅ Producción  
**Categoría**: Machine Learning  
**Dependencia**: `scikit-learn` (KMeans, PCA, StandardScaler)

**Descripción**:  
Clasificación automática de litología usando PCA para reducción de dimensionalidad
seguido de K-Means en el espacio transformado. Utiliza hasta 6 curvas.

**Flujo de Trabajo Mejorado**:
1. **Selección de Features**: GR, PHI, RHOB, NPHI, RT, DT (las disponibles)
2. **Normalización**: StandardScaler (media=0, desviación=1)
3. **PCA**: Reduce a 3 componentes principales con varianza explicada
4. **K-Means**: 4 clusters sobre PCA, 10 inicializaciones, semilla fija (42)
5. **Asignación Litológica**: Ordenada por GR promedio del centroide

**Clasificación Resultante**:
| Cluster | Nombre           | GR Promedio | Interpretación                  |
|:--------|:-----------------|:------------|:--------------------------------|
| 0       | Arena Limpia     | Más bajo    | Reservorio de alta calidad      |
| 1       | Arena Arcillosa  | Bajo-Medio  | Reservorio con corrección       |
| 2       | Lutita           | Medio-Alto  | Sello o barrera                 |
| 3       | Carbonato/Tight  | Más alto    | Zona densa o carbonato          |

**Salidas**: Distribución por facies, curvas FACIES y FACIES_NAME, método: 'PCA + K-Means'.

---

### 16. PCA (Análisis de Componentes Principales)
**Estado**: ✅ Producción  
**Categoría**: Machine Learning  
**Archivo**: `backend_api.py` (PASO 3B integrado con Electrofacies)

**Descripción**:  
Reducción de dimensionalidad previa al clustering. PCA identifica los vectores
que capturan la mayor variabilidad litológica.

**Proceso**:
```
Datos Originales (N curvas) → PCA (3 comp) → K-Means → Facies clasificadas
```

**Salidas JSON** (`pca_analysis`):
- `variance_explained`: % por componente (ej: [52.1, 28.3, 12.4])
- `cumulative_variance`: total acumulado (ej: 92.8%)
- `loadings`: qué curva domina cada PC con pesos
- `pc1`, `pc2`, `pc3`: coordenadas sampled para scatter
- `labels` / `facies_names`: clasificación por punto

**Impacto**: Mejor separación de clusters + datos listos para scatter plot en frontend.

---

## CATEGORÍA 6: GEOFÍSICA SINTÉTICA

---

### 18. Impedancia Acústica
**Estado**: ✅ Producción  
**Categoría**: Geofísica  
**Clase**: `GeophysicsEngine.calcular_impedancia()`  

**Descripción**:  
La impedancia acústica (Z) es el producto de la densidad por la velocidad de
propagación del sonido en la roca. Es la propiedad fundamental que controla
las reflexiones sísmicas.

**Fórmula**:
```
Z = ρ × Vp
Vp = 1,000,000 / DT   (DT en μs/ft → Vp en ft/s)
```

**Entradas**: RHOB (g/cm³), DT (μs/ft)  
**Salidas**: Curva AI (kg/m²·s)  

---

### 19. Coeficientes de Reflexión
**Estado**: ✅ Producción  
**Clase**: `GeophysicsEngine.coeficientes_reflexion()`  

**Descripción**:  
En cada interfaz entre dos capas geológicas con impedancias diferentes, parte de
la energía sísmica se refleja. El coeficiente de reflexión cuantifica esta fracción:

**Fórmula**:
```
RC(i) = (Z(i+1) - Z(i)) / (Z(i+1) + Z(i))
```

**Rango**: -1.0 a +1.0 (típicamente -0.3 a +0.3 en formaciones sedimentarias).  
**Entradas**: Curva de Impedancia Acústica  
**Salidas**: Serie de Coeficientes de Reflexión  

---

### 20. Ondícula Ricker
**Estado**: ✅ Producción  
**Clase**: `GeophysicsEngine.ricker_wavelet()`  

**Descripción**:  
La ondícula Ricker (Mexican Hat) es la forma de onda más utilizada en geofísica
de exploración para la convolución de sismogramas sintéticos. Su forma depende
únicamente de la frecuencia central dominante.

**Fórmula**:
```
ψ(t) = (1 - 2π²f²t²) × e^(-π²f²t²)
```

**Parámetros**:
| Parámetro | Default  | Descripción                        |
|:----------|:---------|:-----------------------------------|
| freq      | 25 Hz    | Frecuencia central dominante       |
| length    | 0.1 s    | Duración total de la ondícula      |
| dt        | 0.002 s  | Intervalo de muestreo (500 Hz)     |

**Salida**: Array numpy con la forma de onda Ricker.

---

### 21. Sismograma Sintético
**Estado**: ✅ Producción  
**Clase**: `GeophysicsEngine.generar_sintetico()`  

**Descripción**:  
Convolución de la serie de reflectividad con la ondícula Ricker para generar
una traza sísmica sintética. Esta traza permite correlacionar los datos del pozo
(escala ~15 cm) con los datos sísmicos (escala ~10 m).

**Fórmula**:
```
Sintético(t) = ∫ Reflectividad(τ) × Ondícula(t - τ) dτ
```
Implementado como convolución discreta con `numpy.convolve()`.

**Entradas**: Serie RC, Wavelet Ricker  
**Salidas**: Traza sísmica sintética + sección 2D  

---

### 22. Well Tie (Dynamic Time Warping)
**Estado**: 🔶 Pendiente  
**Categoría**: Geofísica  

**Descripción**:  
Técnica de alineación temporal que ajusta el sismograma sintético para que
coincida con la sísmica real del pozo. Utiliza Dynamic Time Warping (DTW) para
encontrar la mejor correspondencia entre la traza del pozo y la traza
sísmica extraída.

**Proceso**:
1. Generar sintético (ya implementado)
2. Cargar traza sísmica real (nuevo input)
3. Aplicar DTW para calcular el shift óptimo
4. Generar curva tiempo-profundidad calibrada

**Impacto**: Permite conversión tiempo↔profundidad de alta precisión.

---

## CATEGORÍA 7: INGENIERÍA DE PERFORACIÓN

---

### 23. Dog-Leg Severity (DLS)
**Estado**: ✅ Producción  
**Categoría**: Perforación  

**Descripción**:  
Calcula la severidad de curvatura del pozo usando la fórmula del Minimum
Curvature Method. Clasifica cada punto por su nivel de riesgo operativo.

**Fórmula**:
```
DLS = arccos[cos(Inc₂ - Inc₁) - sin(Inc₁)×sin(Inc₂)×(1 - cos(Azi₂ - Azi₁))] × (100 / ΔMD)
```

**Clasificación de Riesgo**:
| Severidad | Rango DLS       | Riesgo                                          |
|:----------|:----------------|:------------------------------------------------|
| Bajo      | < 3°/100ft      | Operación normal                                |
| Medio     | 3° – 6°/100ft   | Monitoreo de desgaste; torque moderado          |
| Alto      | 6° – 10°/100ft  | Key seating; fatiga de sarta                    |
| Crítico   | > 10°/100ft     | Falla mecánica posible; riesgo de sidetrack     |

**Nota Actual**: Usa datos simulados de inclinación/azimut. Pendiente integrar
datos reales de survey del archivo LAS (curvas INC, AZI si presentes).

---

## CATEGORÍA 8: PRODUCCIÓN Y ECONOMÍA

---

### 24. Análisis Nodal (IPR vs VLP)
**Estado**: ✅ Producción  
**Clase**: `analyze_nodal_system()`  
**Archivo**: `backend_api.py`  

**Descripción**:  
Calcula el punto de operación del pozo encontrando la intersección entre la curva
de capacidad del reservorio (IPR — Inflow Performance Relationship) y la curva
de la tubería de producción (VLP — Vertical Lift Performance).

**Modelos**:
- **IPR**: Vogel (para Pwf < Pb) y lineal (para Pwf > Pb)
- **VLP**: Gradiente de presión en tubería con corrección por dirección y GOR

**Entradas**: K, h, Pr, Pwh, Tubing ID, MD, TVD, WC, GOR, API, skin  
**Salidas**: Qo óptimo (STB/d), Pwf operativa, curvas IPR y VLP completas  

---

### 25. Pronóstico Arps — Declinación Exponencial
**Estado**: ✅ Producción  
**Clase**: `SimulationEngine.simular_produccion()`  

**Descripción**:  
Proyecta la producción futura asumiendo que la tasa de producción declina
proporcionalmente a la producción acumulada (modelo más conservador de Arps).

**Fórmula**:
```
Q(t) = Qi × e^(-D × t)
```
Donde: `Qi` = tasa inicial, `D` = tasa de declinación (default 15%/año).

**Salidas**: Producción anual (bbl), ingresos acumulados ($), tabla a 10 años.

---

### 26. Pronóstico Arps — Declinación Hiperbólica
**Estado**: ✅ Producción  
**Categoría**: Producción  
**Archivo**: `backend_api.py` (PASO 11)

**Descripción**:  
Modelo realista junto con la exponencial. Calcula 120 meses de producción
con curva hiperbólica usando b=0.5, Di=15%, Qi=8% del OIP.

**Fórmula**:
```
Q(t) = Qi / (1 + b × Di × t)^(1/b)
```

**Salidas JSON** (`production.hyperbolic`):
- `months`, `barrels`: curva de producción hiperbólica
- `b_factor`, `di_percent`, `qi_stb`: parámetros usados
- `cumulative_10y`: producción acumulada a 10 años

**Campo `decline_methods`**: `['Exponencial', 'Hiperbólica']` — ambas disponibles.

---

### 27. OOIP (Petróleo Original en Sitio)
**Estado**: ✅ Producción  
**Categoría**: Producción  
**Archivo**: `backend_api.py` (PASO 11)

**Descripción**:  
Calcula OOIP con fórmula completa API, con desglose de parámetros.

**Fórmula Completa (API estándar)**:
```
OOIP = 7758 × A × h × φ × (1 - Sw) / Bo
```

**Salidas JSON** (`production.ooip_breakdown`):
| Variable | Valor Default | Descripción                        |
|:---------|:-------------|:-----------------------------------|
| A        | 40 acres     | Área de drenaje                    |
| h        | Calculado    | Espesor neto pay (sum pay zones)   |
| φ        | Calculado    | Porosidad promedio en pay          |
| Sw       | Calculado    | Saturación de agua en pay          |
| Bo       | 1.2 bbl/STB  | Factor volumétrico de formación    |

Todos los parámetros y resultados se exportan en el JSON para trazabilidad.
**Mejora futura**: Permitir al usuario ingresar A y Bo específicos del campo.

---

## CATEGORÍA 9: ESTADÍSTICA AVANZADA

---

### 28. Histogramas de Distribución
**Estado**: ✅ Producción  

**Descripción**:  
Genera histogramas de frecuencia para cada curva del dataset, permitiendo
identificar distribuciones bimodales (mezcla de litologías), sesgos en los
datos y valores atípicos.

**Salida**: N histogramas interactivos (Plotly) con estadísticas overlay
(media, mediana, desviación estándar).

---

### 29. Correlación de Pearson
**Estado**: ✅ Producción  

**Descripción**:  
Calcula la matriz de correlación lineal entre todas las curvas del dataset y
la visualiza como un heatmap de colores. Identifica relaciones causales:

**Correlaciones Típicas Esperadas**:
| Par de Curvas | Correlación Esperada | Interpretación                    |
|:--------------|:---------------------|:----------------------------------|
| NPHI ↔ RHOB   | Negativa fuerte     | Normal (porosidad ↑ = densidad ↓) |
| GR ↔ VSH      | Positiva fuerte     | Derivación directa                |
| PHI ↔ K       | Positiva moderada   | A mayor porosidad, mayor perm     |
| RT ↔ SW       | Negativa fuerte     | HC bajan la saturación de agua    |

---

### 30. 4D Bubble Plot
**Estado**: ✅ Producción  

**Descripción**:  
Visualización simultánea de 4 variables en un solo gráfico de dispersión:
- **Eje X**: Variable 1 (ej: Porosidad)
- **Eje Y**: Variable 2 (ej: Permeabilidad)
- **Tamaño de burbuja**: Variable 3 (ej: Saturación HC)
- **Color de burbuja**: Variable 4 (ej: Profundidad)

Permite identificar clústeres de alta calidad de roca de forma visual e intuitiva.

---

## CATEGORÍA 10: EXPORTACIÓN Y REPORTES

---

### 33. Exportación LAS 2.0
**Estado**: ✅ Producción  
**Clase**: `LASExporter.export_pandas_to_las()`  

**Descripción**:  
Genera un archivo LAS 2.0 válido a partir del DataFrame procesado, incluyendo
las curvas calculadas (VSH, PHI, SW, K, FACIES). El archivo resultante es
compatible con software industrial: Petrel (Schlumberger), Kingdom (IHS),
Techlog (Schlumberger), Interactive Petrophysics (LR Senergy).

---

### 34-36. Exportación PDF / HTML / CSV
**Estado**: ✅ Producción  

**Formatos disponibles**:
| Formato | Uso Principal                            | Incluye                    |
|:--------|:-----------------------------------------|:---------------------------|
| PDF     | Impresión técnica, auditorías            | Gráficos + tablas + KPIs   |
| HTML    | Visualización rápida en navegador        | Interactivo, responsivo    |
| CSV     | Importación a Excel, Spotfire, Tableau   | Solo datos tabulares       |

---

## 📊 RESUMEN EJECUTIVO

| Métrica                    | Valor         |
|:---------------------------|:--------------|
| **Total de Módulos**       | 36            |
| **Implementados**          | 32 (89%)      |
| **Parciales**              | 0 (0%)        |
| **Pendientes**             | 4 (11%)       |
| **Categorías Cubiertas**   | 10/10         |
| **Score de Completitud**   | **~87%**      |

---

## 🗺️ ROADMAP DE DESARROLLO

### ~~Fase 1 — Quick Wins (Backend)~~ ✅ COMPLETADA
- [x] Estandarización de Unidades (#03)
- [x] PCA previo a K-Means (#16)
- [x] Declinación Hiperbólica (#26)
- [x] OOIP completo con Bo y A (#27)
- [x] Morris-Biggs (#11)

### Fase 2 — Módulos Nuevos (SIGUIENTE)
- [ ] Crossplot NPHI-RHOB (#17)
- [ ] DLS con datos reales de INC/AZI (#23 mejora)
- [ ] Well Tie / DTW (#22)

### Fase 3 — Visualización Premium
- [ ] Sombreado Litológico (#31)
- [ ] Correlación Multi-Pozo (#32)
- [ ] Mapa Interactivo de Pozos (Plotly/Leaflet)

---

*Documento generado por DataTerra Intelligence Engine — Febrero 2026*
*Referencia: CWLS LAS Standard, SPE Papers, Schlumberger Oilfield Review*
