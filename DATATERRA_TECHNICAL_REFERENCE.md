# DataTerra — Referencia Técnica Interna (Base de Datos de Conocimiento)

> Última Actualización: 2026-02-16
> Este documento sirve como referencia técnica interna del proyecto. Contiene las fórmulas, métodos, estándares y arquitectura implementados.

---

## 1. Arquitectura del Sistema

```
┌─────────────────────┐     HTTP/JSON     ┌──────────────────────┐
│   FRONTEND (React)  │ ◄──────────────► │   BACKEND (FastAPI)  │
│   Puerto: 3002      │                   │   Puerto: 8000       │
│   Vite + Motion     │                   │   Python 3.x         │
└─────────────────────┘                   └──────────────────────┘
                                                    │
                                          ┌─────────┴──────────┐
                                          │  petro_core_web.py │
                                          │  (Motor Científico) │
                                          └────────────────────┘
```

### Flujo de Datos:
1. Usuario sube archivo `.LAS` → Frontend envía `POST /upload` (FormData)
2. Backend lee con `lasio.read()` → Convierte a `pandas.DataFrame`
3. `CurveNormalizer` estandariza nombres de curvas
4. Pipeline de cálculos (VSH → PHI → SW → PERM → Pay Zones → Electrofacies → DLS)
5. `DataQualityAuditor` genera reporte forense
6. JSON completo se devuelve al Frontend

---

## 2. Librerías Utilizadas

| Librería | Uso | Estado |
|:---|:---|:---|
| `lasio` | Lectura de archivos LAS 2.0 | ✅ Implementado |
| `pandas` | Manipulación de datos tabulares | ✅ Implementado |
| `numpy` | Cálculos numéricos vectorizados | ✅ Implementado |
| `scipy` | Convolución (sísmica sintética) | ✅ Implementado |
| `scikit-learn` | K-Means Clustering (Electrofacies) | ✅ Implementado |
| `FastAPI` | API REST del backend | ✅ Implementado |
| `React` | Interfaz de usuario | ✅ Implementado |
| `motion` (framer) | Animaciones de UI | ✅ Implementado |
| `dlisio` | Lectura de archivos DLIS | ❌ Pendiente |
| `welly` | Multi-pozo y QC avanzado | ❌ Pendiente |
| `missingno` | Visualización de datos faltantes | ❌ Pendiente |
| `plotly` | Gráficos interactivos (zoom/hover) | ❌ Pendiente |

---

## 3. Módulos Científicos Implementados

### 3A. Volumen de Arcilla (VSH) — `PetrofisicaCore.calcular_vsh()`
**Archivo:** `geomind_saas/petro_core_web.py`

**Paso 1: Índice de Gamma Ray (IGR)**
```
IGR = (GR_log - GR_min) / (GR_max - GR_min)
```
- `GR_min` = Percentil 5 (Arena Limpia)
- `GR_max` = Percentil 95 (Lutita Pura)

**Paso 2: Corrección No-Lineal**
| Método | Fórmula | Uso Recomendado |
|:---|:---|:---|
| `linear` | VSH = IGR | Default / General |
| `larionov_tertiary` | VSH = 0.083 × (2^(3.7×IGR) - 1) | Rocas Terciarias (jóvenes) |
| `larionov_older` | VSH = 0.33 × (2^(2×IGR) - 1) | Rocas Mesozoicas/Paleozoicas |
| `steiber` | VSH = IGR / (3 - 2×IGR) | Clásticos consolidados |

**Paso 3:** Clamp resultado entre [0, 1]

---

### 3B. Porosidad (PHI) — `backend_api.py`
**Archivo:** `backend_api.py` (inline)

**Prioridad de Fuentes:**
1. Si existe `NPHI` → `PHI = NPHI` (con auto-detección % vs decimal: si mean > 1.0, divide /100)
2. Si existe `RHOB` → `PHI = (ρ_ma - RHOB) / (ρ_ma - ρ_fl)` donde ρ_ma=2.65, ρ_fl=1.0
3. Fallback → `PHI = 0.15` (constante conservadora)

**Clip:** Siempre `[0, 0.45]`

---

### 3C. Saturación de Agua (SW) — `PetrofisicaCore.calcular_sw()`
**Archivo:** `geomind_saas/petro_core_web.py`

**Modelo Archie:**
```
SW^n = (a × Rw) / (PHI^m × Rt)
SW = ((a × Rw) / (PHI^m × Rt))^(1/n)
```
**Parámetros Default:**
- `a` = 1 (Factor de tortuosidad)
- `m` = 2 (Exponente de cementación)
- `n` = 2 (Exponente de saturación)
- `Rw` = 0.05 Ω·m (Resistividad del agua)

**Clip:** `[0, 1]`

---

### 3D. Permeabilidad (PERM) — `backend_api.py`
**Archivo:** `backend_api.py` (inline)

**Modelo Log-Linear (Poro-Perm):**
```
K = 10^(a × PHI + b)
```
- `a` = 14.0 (Pendiente calibrada para sandstone)
- `b` = -1.5 (Intercepto)

**Clip:** `[0.001, 50000]` mD

---

### 3E. Electrofacies (K-Means) — `backend_api.py`
**Archivo:** `backend_api.py` (inline, usa `sklearn`)

**Algoritmo:** K-Means Clustering con K=4
**Curvas de Entrada:** GR, PHI, RHOB, NPHI (las que estén disponibles, mínimo 2)
**Pre-procesamiento:** `StandardScaler` (normalización Z-score)
**Clasificación por GR:**
| Cluster (ordenado por GR↑) | Nombre |
|:---|:---|
| 1 (GR más bajo) | Arena Limpia |
| 2 | Arena Arcillosa |
| 3 | Lutita |
| 4 (GR más alto) | Carbonato/Tight |

---

### 3F. DLS (Dog-Leg Severity) — `backend_api.py`
**Archivo:** `backend_api.py` (inline)

**Fórmula:**
```
DLS = arccos(cos(Δinc) - sin(inc₁)×sin(inc₂)×(1-cos(Δazi))) × 100 / ΔMD
```
**Clasificación:**
| Rango (°/100ft) | Severidad |
|:---|:---|
| < 3 | Bajo |
| 3 - 6 | Medio |
| 6 - 10 | Alto |
| > 10 | Crítico |

---

### 3G. Detección de Pay Zones — `ReservoirDetector`
**Archivo:** `geomind_saas/petro_core_web.py`

**Cutoffs:**
| Parámetro | Valor | Significado |
|:---|:---|:---|
| `porosity_min` | 0.10 | PHI ≥ 10% |
| `sw_max` | 0.60 | SW ≤ 60% |
| `vshale_max` | 0.50 | VSH ≤ 50% |

**Método:** Run Length Encoding (RLE) para agrupar intervalos contiguos que cumplen criterios.

**Calidad:**
| Condición | Clasificación |
|:---|:---|
| PHI > 0.20 AND SW < 0.30 | Excelente |
| PHI > 0.15 | Bueno |
| Otros | Marginal |

---

## 4. Normalización de Curvas (`CurveNormalizer`)

| Alias Detectado | Curva Estándar |
|:---|:---|
| GR, CGR, SGR, GRGC | GR |
| NPHI, TNPH, PHIN, NPOR | NPHI |
| RHOB, RHOZ, DEN, DENSITY | RHOB |
| RT, ILD, RILM, LLD, RD, MSFL | RT |
| DEPT, DEPTH, MD | DEPT |
| DT, AC, DTCO | DT |
| CALI, HCAL, CAL | CALI |
| SP | SP |
| PEF, PE | PEF |

---

## 5. Auditoría de Calidad (DataQualityAuditor)

El sistema genera un "Forensic Log" que incluye:
1. ✅ **Lectura**: Número exacto de líneas cargadas
2. 📏 **Cobertura**: Rango de profundidad (Start → Stop, footage total)
3. ⚠️ **Curvas Faltantes**: Identifica qué curvas del Triple Combo faltan
4. ⚙️ **Confirmación de Cálculos**: Verifica que VSH, PHI, SW se calcularon
5. ✅ **Integridad GR**: % de datos válidos (no-nulos)

---

## 6. Estándares de la Industria

| Estándar | Descripción |
|:---|:---|
| **LAS 2.0** | Log ASCII Standard (CWLS). Formato más común. |
| **DLIS** | Digital Log Interchange Standard (API, 1991). Binario complejo. |
| **ISO 9000:2015** | Dimensiones de calidad: exactitud, completitud, consistencia, puntualidad, validez, unicidad. |

---

## 7. Módulos Pendientes (Roadmap)

| Módulo | Prioridad | Complejidad | Descripción |
|:---|:---|:---|:---|
| **missingno** (Visualización de Nulls) | Alta | Baja | Mapa de calor de datos faltantes |
| **Regresión Poro-Perm con Core Data** | Alta | Media | Calibrar con datos de laboratorio |
| **Random Forest (Litología)** | Media | Media | Predicción supervisada de tipo de roca |
| **DLIS Support** | Media | Alta | Lectura de archivos binarios complejos |
| **Multi-Pozo (welly)** | Baja | Alta | Comparación entre pozos |
| **TVD (Trayectoria Verdadera)** | Baja | Media | Cálculo de profundidad vertical |
| **Plotly Interactivo** | Media | Media | Zoom, hover, selección en gráficos |
| **Isolation Forest (Outliers)** | Media | Baja | Detección automática de anomalías |
| **Mapa Interactivo de Pozos** | Baja | Media | Plotly/Leaflet con LAT/LON del header LAS (hover con metadatos) |

---

## 8. Referencias Técnicas

- Andy McDonald (Python Petrophysics / YouTube)
- CWLS: Canadian Well Logging Society — LAS Standard
- API RP66: Digital Log Interchange Standard (DLIS)
- Larionov (1969): Non-linear Vshale corrections
- Archie (1942): Water saturation equation
- Timur-Coates: Permeability from NMR/Porosity
- scikit-learn Documentation: KMeans, StandardScaler, RandomForest
