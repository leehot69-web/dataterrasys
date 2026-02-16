# Plan de Acción Prioritario - Petrofísica App

## 🎯 Objetivo Inmediato: "El Reto de los 10 Minutos"
Implementar módulos de Geofísica y Perforación usando los datos existentes del LAS.

### 1. Cálculo de DLS (Dog-Leg Severity) - Perforación
**Tiempo estimado:** 5 min.
**Lógica:**
- Usar la trayectoria 3D existente (Inc, Azi, MD).
- Aplicar fórmula de curvatura: `DLS = acos(...) * (100 / DeltaMD)`.
- **Output:** Curva de DLS a lo largo del pozo para detectar "patas de perro" (curvas bruscas).
- **Visualización:** Añadir semáforo (Verde < 3°/100ft, Rojo > 3°/100ft).

### 2. Sismograma Sintético - Geofísica
**Tiempo estimado:** 5-10 min.
**Lógica:**
- **Inputs:** Curva Sónico (DT) y Densidad (RHOB/DEN). Si falta RHOB, usar Gardner (rho = 0.23 * V^0.25).
- **Proceso:**
  1. Calcular Velocidad (V = 1,000,000 / DT).
  2. Calcular Impedancia Acústica (Z = V * Rho).
  3. Calcular Coeficientes de Reflexión (RC = (Z2-Z1)/(Z2+Z1)).
  4. Generar Ondícula de Ricker (Frecuencia 30Hz).
  5. Convolucionar: `Sismograma = RC * Ricker`.
- **Output:** Nueva curva "SEISMIC" para visualizar.

### 3. Decline Curve Analysis (DCA)
**Tiempo estimado:** 1 hora (Este lleva UI).
- Crear modal simple de simulación económica.
- Input: Caudal Inicial (qi) del Nodal Analysis.
- Input: Tasa de declinación anual (Di).
- Output: Tabla de producción a 5/10 años.

## 💾 Despliegue
- Subir código a repositorios Git (Backend y Frontend).

---
*Este archivo sirve de contexto principal para la próxima sesión.*
