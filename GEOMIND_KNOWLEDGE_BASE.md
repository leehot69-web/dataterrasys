# GEOMIND KNOWLEDGE BASE: NODAL ANALYSIS & AI ARCHITECTURE

**Versión:** 1.0.0  
**Fecha de Actualización:** 2026-02-16  
**Alcance:** Ingeniería de Producción, Física de Yacimientos, Arquitectura de Datos para IA.

---

## 1. ESTÁNDARES Y NORMATIVA (SPE / API)

El sistema debe adherirse estrictamente a los siguientes estándares para garantizar la interoperabilidad y la integridad física de los cálculos.

| Norma | Descripción | Aplicación en GeoMind |
| :--- | :--- | :--- |
| **API RP 14B** | Diseño, instalación y operación de sistemas de válvulas de seguridad de subsuelo. | Validación de metadatos de completación en archivos `.DLIS` o `.JSON`. |
| **API 5CT** | Especificaciones para casing y tubing. | Base de datos de diámetros internos/externos para cálculos de pérdidas de presión. |
| **SPE 12345** | Estándar de intercambio de datos de producción. | Esquema de nombres para variables de producción ($q_o, q_w, q_g$). |
| **PRODML** | Production Markup Language (Energistics). | Formato de intercambio XML para datos de flujo y completación. |

---

## 2. FUNDAMENTOS FÍSICOS: ANÁLISIS NODAL (IPR / VLP)

El núcleo del análisis nodal es la intersección entre la capacidad de aporte del yacimiento (IPR) y la capacidad de transporte de la tubería (VLP).

### 2.1 Ecuaciones de IPR (Inflow Performance Relationship)

#### A. Ley de Darcy (Flujo Monofásico / Laminar)
Para yacimientos subsaturados ($P_r > P_b$) donde el flujo es lineal y Darcy es válido:

$$
q_l = \frac{k h (P_r - P_{wf})}{141.2 B \mu (\ln(r_e/r_w) + S)}
$$

Donde:
*   $q_l$: Tasa de líquido (STB/d)
*   $k$: Permeabilidad (mD)
*   $h$: Espesor neto (ft)
*   $P_r$: Presión del yacimiento (psi)
*   $P_{wf}$: Presión de fondo fluyente (psi)
*   $B$: Factor volumétrico de formación (rb/stb)
*   $\mu$: Viscosidad (cp)
*   $S$: Skin (adimensional)

#### B. Ecuación de Vogel (Yacimientos Saturados)
Cuando $P_{wf} < P_b$, se libera gas en el yacimiento y la relación IPR se curva.

$$
\frac{q_o}{(q_o)_{max}} = 1 - 0.2 \left( \frac{P_{wf}}{P_r} \right) - 0.8 \left( \frac{P_{wf}}{P_r} \right)^2
$$

*   **(q_o)_{max}**: Tasa máxima teórica cuando $P_{wf} = 0$.

#### C. Ecuación de Fetkovich (Flujo Turbulento / Gas)
Para pozos de gas o flujo de alta velocidad (no-Darcy):

$$
q_g = C (P_r^2 - P_{wf}^2)^n
$$

*   $n$: Exponente de turbulencia ($0.5 \le n \le 1.0$). Si $n=1$, flujo laminar; si $n=0.5$, flujo completamente turbulento.

---

### 2.2 Correlaciones de Flujo Multifásico (VLP - Vertical Lift Performance)

El cálculo de la caída de presión en la tubería ($\Delta P_{total}$) es la suma de tres componentes:

$$
\Delta P_{total} = \Delta P_{elevación} + \Delta P_{fricción} + \Delta P_{aceleración}
$$

$$
\frac{dP}{dL} = \frac{\rho_m g \sin(\theta)}{144 g_c} + \frac{f \rho_m v_m^2}{2 g_c D} + \frac{\rho_m v_m dv_m}{g_c dL}
$$

#### A. Correlación de Beggs & Brill (1973)
La correlación estándar para flujo inclinado y direccional. Considera regímenes de flujo (Segregated, Intermittent, Distributed).

**Procedimiento de Cálculo:**
1.  Calcular los números adimensionales de Froude ($N_{Fr}$) y Líquido ($N_L$).
2.  Determinar el régimen de flujo horizontal.
3.  Calcular los *Holdups* ($H_L(0)$) y factores de fricción.
4.  Aplicar el factor de corrección por inclinación $C$ para obtener el Holdup inclinado $H_L(\theta) = H_L(0) \cdot \psi$.

#### B. Correlación de Hagedorn & Brown
Optimizada para flujo vertical en tuberías de producción. No considera regímenes de flujo, usa un número de viscosidad líquida.

---

## 3. ARQUITECTURA DE DATOS E IA

Para que el módulo de IA pueda interpretar y validar datos de producción, se define el siguiente esquema estricto.

### 3.1 Diccionario de Mnemónicos (Dataset Schema)

| Variable | Mnemónico | Unidad | Tipo de Dato | Rango Típico | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Profundidad Medida** | `MD` | ft | float | $0 - 30,000$ | Profundidad a lo largo del pozo. |
| **Profundidad Vertical** | `TVD` | ft | float | $0 - 30,000$ | Profundidad vertical verdadera. |
| **Presión de Cabezal** | `WHP` / `THP` | psi | float | $0 - 15,000$ | Wellhead Pressure / Tubing Head Pressure. |
| **Presión de Fondo** | `BHP` / `Pwf` | psi | float | $0 - 20,000$ | Bottom Hole Pressure. |
| **Tasa de Aceite** | `Qo` | stb/d | float | $\ge 0$ | Oil Rate. |
| **Tasa de Gas** | `Qg` | Mscf/d | float | $\ge 0$ | Gas Rate. |
| **Tasa de Agua** | `Qw` | stb/d | float | $\ge 0$ | Water Rate. |
| **Corte de Agua** | `WC` / `BSW` | % | float | $0 - 100$ | Water Cut / Basic Sediment & Water. |
| **Relación Gas-Aceite** | `GOR` | scf/stb | float | $\ge 0$ | Gas Oil Ratio. |
| **Diámetro Tubing** | `ID_tbg` | inch | float | $1.5 - 7.0$ | Diámetro interno del tubing. |

### 3.2 Estrategia de Limpieza de Datos (Data Cleaning Logic)

Antes de cualquier entrenamiento o inferencia, aplicar el siguiente filtro lógico:

1.  **Detección de Valores Físicamente Imposibles:**
    *   Si `WC > 100` o `WC < 0` $\rightarrow$ Marcar como `NaN` o error.
    *   Si `Pwf > Pr` (en producción) $\rightarrow$ Error de física (posible inyección o sensor dañado).
    *   Si `Qo = 0` y `Pwf` varía drásticamente $\rightarrow$ Posible pozo cerrado o sensor a la deriva.

2.  **Consistencia PVT:**
    *   Verificar que `GOR_producido` sea consistente con el `Rs` (solubilidad) del PVT a la presión de separador.
    *   $$GOR_{prod} \approx R_s + \text{Gas Libre}$$

3.  **Outlier Detection (Isolation Forest):**
    *   Aplicar algoritmo `IsolationForest` sobre el vector $[Q_o, WHP, WC]$ para detectar anomalías operativas (slugging severo, bacheo).

---

## 4. ALGORITMOS NUMÉRICOS PARA SOLUCIÓN (MOTOR DE CÁLCULO)

### 4.1 Solución del Sistema Nodal (Intersección IPR / VLP)
Para encontrar el punto de operación (Tasa Operativa $Q_{op}$ y Presión de Fondo $P_{wf,op}$), se debe igualar la presión de oferta y demanda.

$$ P_{wf}(IPR) = P_{wf}(VLP) $$

Dado que las funciones son no lineales, se usa el método de **Newton-Raphson**:

1.  Definir función objetivo: $F(Q) = P_{wf, IPR}(Q) - P_{wf, VLP}(Q)$.
2.  Buscar $Q$ tal que $F(Q) = 0$.
3.  Iteración:
    $$ Q_{new} = Q_{old} - \frac{F(Q_{old})}{F'(Q_{old})} $$

### 4.2 Sensibilidades
Para generar las gráficas de "Sensitivity Analysis" (ej. efecto del diámetro del tubing o skin):
1.  Fijar un rango de valores para la variable de sensibilidad (ej. Tubing ID: 2.375", 2.875", 3.5").
2.  Para cada valor, re-calcular la curva VLP completa.
3.  Superponer las múltiples curvas VLP sobre la IPR fija.
4.  Identificar los nuevos puntos de intersección.

---

## 5. ESTRATEGIA DE CHUNKING PARA RAG (AI CONTEXT)

Para alimentar este conocimiento al modelo de lenguaje (LLM), los documentos deben fragmentarse lógicamente:

*   **Chunk Size:** 512 tokens.
*   **Overlap:** 50 tokens.
*   **Metadata Tags:** Cada chunk debe etiquetarse con:
    *   `topic`: [IPR, VLP, PVT, CORRELATIONS]
    *   `source`: [API_14B, SPE_PAPER, BEGGS_BRILL]
    *   `complexity`: [BASIC, INTERMEDIATE, ADVANCED]

Esto permite que, si el usuario pregunta *"¿Cómo afecta el skin a la producción?"*, la IA recupere específicamente los chunks de IPR y Ecuación de Darcy, ignorando los de tuberías verticales.

---

**Fin del Documento Maestro.**
