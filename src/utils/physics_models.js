
// ==========================================
// 1. DRILLING PHYSICS - DOG LEG SEVERITY (DLS)
// ==========================================
/**
 * Calcula la severidad de la pata de perro (DLS) en grados/100 pies.
 * Basado en la fórmula de Lubinski (Estándar API).
 * 
 * @param {number} md1 - Profundidad Medida 1 (ft)
 * @param {number} inc1 - Inclinación 1 (grados)
 * @param {number} azi1 - Azimut 1 (grados)
 * @param {number} md2 - Profundidad Medida 2 (ft)
 * @param {number} inc2 - Inclinación 2 (grados)
 * @param {number} azi2 - Azimut 2 (grados)
 */
export const calculateDLS = (md1, inc1, azi1, md2, inc2, azi2) => {
    // Convertir a radianes
    const r1 = (inc1 * Math.PI) / 180;
    const r2 = (inc2 * Math.PI) / 180;
    const a1 = (azi1 * Math.PI) / 180;
    const a2 = (azi2 * Math.PI) / 180;

    const dMD = md2 - md1;
    if (dMD <= 0) return 0;

    // Ángulo de curvatura (Dog Leg Angle)
    // dl = arccos( cos(i1)cos(i2) + sin(i1)sin(i2)cos(a2-a1) )
    let arg = Math.cos(r1) * Math.cos(r2) + Math.sin(r1) * Math.sin(r2) * Math.cos(a2 - a1);

    // Clamp por seguridad numérica
    if (arg > 1) arg = 1;
    if (arg < -1) arg = -1;

    const dl = Math.acos(arg); // Radianes

    // DLS en grados/100ft
    const dls = (dl * (180 / Math.PI)) * (100 / dMD);

    return dls;
};


// ==========================================
// 2. GEOPHYSICS - SYNTHETIC SEISMOGRAM
// ==========================================
/**
 * Genera una ondícula de Ricker (Mexican Hat).
 * @param {number} freq - Frecuencia dominante (Hz), típico 30Hz
 * @param {number} dt - Muestreo temporal (s), típico 0.001 (1ms)
 * @param {number} length - Longitud de la onda (s), típico 0.1s
 */
const rickerWavelet = (freq, dt, length) => {
    const numSamples = Math.floor(length / dt);
    const wavelet = [];
    const center = numSamples / 2;

    for (let i = 0; i < numSamples; i++) {
        const t = (i - center) * dt;
        const arg = Math.PI * freq * t;
        const arg2 = arg * arg;
        // Fórmula Ricker: (1 - 2*pi^2*f^2*t^2) * exp(-pi^2*f^2*t^2)
        const val = (1 - 2 * arg2) * Math.exp(-arg2);
        wavelet.push(val);
    }
    return wavelet;
};

/**
 * Calcula un sismograma sintético usando DT (Sónico) y RHOB (Densidad).
 * 
 * @param {Array} depth - Array de profundidad (ft o m)
 * @param {Array} dt - Array de Sónico (us/ft)
 * @param {Array} rhob - Array de Densidad (g/cc). Si es null, usa Gardner.
 */
export const calculateSynthetic = (depth, dt, rhob = null) => {
    if (!dt || dt.length === 0) return null;

    const impedance = [];
    const reflectivity = [];
    const time = []; // Tiempo doble (TWT)

    // 1. Impedancia Acústica (Z = V * rho)
    let accumTime = 0;

    for (let i = 0; i < dt.length; i++) {
        const v = 1000000 / dt[i]; // Velocidad ft/s (DT en us/ft)
        const rho = rhob ? rhob[i] : 0.23 * Math.pow(v, 0.25); // Gardner si no hay RHOB

        // Impedancia
        const z = v * rho;
        impedance.push(z);

        // Tiempo de viaje (Integración sónico)
        // DT es us/ft. Depth step.
        if (i > 0) {
            const dDepth = depth[i] - depth[i - 1];
            // Tiempo en segundos (ida y vuelta x2)
            const dtSec = (dt[i] / 1000000) * dDepth;
            accumTime += dtSec * 2;
        }
        time.push(accumTime);
    }

    // 2. Coeficientes de Reflexión (RC)
    // RC = (Z2 - Z1) / (Z2 + Z1)
    reflectivity.push(0); // Primer punto 0
    for (let i = 1; i < impedance.length; i++) {
        const z1 = impedance[i - 1];
        const z2 = impedance[i];
        const rc = (z2 + z1) !== 0 ? (z2 - z1) / (z2 + z1) : 0;
        reflectivity.push(rc);
    }

    // 3. Convolución con Ricker 30Hz
    const wavelet = rickerWavelet(30, 0.002, 0.1); // 30Hz, 2ms, 100ms long

    // Convolución simple 1D
    const seismic = new Array(reflectivity.length).fill(0);
    const halfWave = Math.floor(wavelet.length / 2);

    for (let i = 0; i < reflectivity.length; i++) {
        if (Math.abs(reflectivity[i]) < 0.0001) continue; // Optimizar ceros

        for (let j = 0; j < wavelet.length; j++) {
            const idx = i + j - halfWave;
            if (idx >= 0 && idx < seismic.length) {
                seismic[idx] += reflectivity[i] * wavelet[j];
            }
        }
    }

    // Normalizar para visualización (-1 a 1)
    const maxAmp = Math.max(...seismic.map(Math.abs)) || 1;
    const seismicNorm = seismic.map(s => s / maxAmp);

    return { impedance, reflectivity, seismic: seismicNorm, time };
};
