import React, { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { X, Layers, Waves, Map as MapIcon, Activity, Hexagon, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const modalOverlay = {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)',
    zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '15px',
};
const modalContent = {
    background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a',
    width: '95%', maxWidth: '1200px', maxHeight: '90vh', overflow: 'auto',
    padding: '25px', position: 'relative',
};
const closeBtn = {
    position: 'absolute', top: '15px', right: '15px', background: 'rgba(255,255,255,0.05)',
    border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white', zIndex: 10,
};
const darkLayout = {
    template: 'plotly_dark', paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 50, r: 30, t: 50, b: 50 }, font: { family: 'Space Grotesk, sans-serif' },
};

// ========= HELPER: compute quick stats from an array =========
const stats = (arr) => {
    if (!arr || arr.length === 0) return { min: 0, max: 0, mean: 0, std: 0, n: 0 };
    const valid = arr.filter(v => isFinite(v));
    const n = valid.length;
    if (n === 0) return { min: 0, max: 0, mean: 0, std: 0, n: 0 };
    const min = Math.min(...valid);
    const max = Math.max(...valid);
    const mean = valid.reduce((a, b) => a + b, 0) / n;
    const std = Math.sqrt(valid.reduce((a, b) => a + (b - mean) ** 2, 0) / n);
    return { min, max, mean, std, n };
};

// ========= REUSABLE InfoPanel =========
const InfoPanel = ({ title, items, interpretation, method, wellName }) => (
    <div style={{ marginTop: '15px', background: 'rgba(0,242,255,0.03)', borderRadius: '16px', border: '1px solid rgba(0,242,255,0.08)', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Info size={14} color="#00f2ff" />
            <span style={{ fontSize: '11px', fontWeight: 900, color: '#00f2ff', letterSpacing: '1px' }}>{title}</span>
            {wellName && <span style={{ fontSize: '9px', opacity: 0.4, marginLeft: 'auto' }}>Pozo: {wellName}</span>}
        </div>
        {/* Stats grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px', marginBottom: '12px' }}>
            {items.map((item, i) => (
                <div key={i} style={{ padding: '8px 12px', background: '#0a0a0a', borderRadius: '10px', border: '1px solid #151515' }}>
                    <span style={{ fontSize: '8px', fontWeight: 700, color: '#555', display: 'block', letterSpacing: '0.5px' }}>{item.label}</span>
                    <span style={{ fontSize: '13px', fontWeight: 900, color: item.color || '#fff' }}>{item.value}</span>
                    {item.unit && <span style={{ fontSize: '8px', color: '#666', marginLeft: '3px' }}>{item.unit}</span>}
                </div>
            ))}
        </div>
        {/* Interpretation */}
        {interpretation && (
            <div style={{ padding: '10px 14px', background: 'rgba(74,222,128,0.04)', borderRadius: '10px', border: '1px solid rgba(74,222,128,0.1)', marginBottom: '8px' }}>
                <span style={{ fontSize: '8px', fontWeight: 800, color: '#4ade80', letterSpacing: '1px', display: 'block', marginBottom: '4px' }}>INTERPRETACIÓN</span>
                <p style={{ margin: 0, fontSize: '10px', opacity: 0.7, lineHeight: '1.6' }}>{interpretation}</p>
            </div>
        )}
        {/* Method */}
        {method && (
            <div style={{ padding: '10px 14px', background: 'rgba(251,191,36,0.04)', borderRadius: '10px', border: '1px solid rgba(251,191,36,0.1)' }}>
                <span style={{ fontSize: '8px', fontWeight: 800, color: '#fbbf24', letterSpacing: '1px', display: 'block', marginBottom: '4px' }}>METODOLOGÍA</span>
                <p style={{ margin: 0, fontSize: '10px', opacity: 0.6, lineHeight: '1.6' }}>{method}</p>
            </div>
        )}
    </div>
);

// ============ 3D LITHO-SCANNER CUBE ============
export const LithoCube3D = ({ data, onClose }) => {
    const [colorBy, setColorBy] = useState('GR');
    const scatter = data?.scatter3d;
    if (!scatter) return null;

    const cols = scatter.available_columns || [];
    const colData = scatter.columns_data || {};
    const depths = scatter.depth_values || [];
    const wellName = data?.well_info?.well_name || 'Pozo Activo';

    const xCol = cols.includes('PHI') ? 'PHI' : cols[0];
    const yCol = cols.includes('RHOB') ? 'RHOB' : cols[Math.min(1, cols.length - 1)];

    const xS = stats(colData[xCol]);
    const yS = stats(colData[yCol]);
    const cS = stats(colData[colorBy]);
    const depthRange = depths.length > 0 ? `${depths[0]?.toFixed(0)} – ${depths[depths.length - 1]?.toFixed(0)} ft` : 'N/A';

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    VOLUMETRIC LITHO-SCANNER 3D
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Análisis volumétrico tridimensional de propiedades petrofísicas por profundidad
                </p>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '10px', opacity: 0.5, alignSelf: 'center' }}>Color by:</span>
                    {cols.filter(c => ['GR', 'VSH', 'PHI', 'SW', 'PERM', 'SH', 'RT'].includes(c)).map(c => (
                        <button key={c} onClick={() => setColorBy(c)} style={{
                            padding: '5px 12px', borderRadius: '20px', fontSize: '10px', fontWeight: 700, cursor: 'pointer',
                            background: colorBy === c ? 'rgba(0,242,255,0.15)' : 'rgba(255,255,255,0.03)',
                            border: colorBy === c ? '1px solid #00f2ff' : '1px solid #222', color: colorBy === c ? '#00f2ff' : '#888',
                        }}>{c}</button>
                    ))}
                </div>
                {colData[xCol] && colData[yCol] && (
                    <Plot
                        data={[{
                            type: 'scatter3d', mode: 'markers',
                            x: colData[xCol], y: colData[yCol], z: depths,
                            marker: {
                                size: 3, color: colData[colorBy] || depths,
                                colorscale: 'Jet', opacity: 0.8,
                                colorbar: { title: colorBy, thickness: 12 },
                            },
                            hovertemplate: `${xCol}: %{x:.3f}<br>${yCol}: %{y:.3f}<br>Depth: %{z:.1f}<br>${colorBy}: %{marker.color:.2f}<extra></extra>`,
                        }]}
                        layout={{
                            ...darkLayout, height: 550,
                            title: `Litho-Scanner: ${xCol} vs ${yCol} vs Depth (Color: ${colorBy})`,
                            scene: {
                                xaxis: { title: xCol, backgroundcolor: 'rgba(20,20,20,0.5)', gridcolor: '#333', showbackground: true },
                                yaxis: { title: yCol, backgroundcolor: 'rgba(20,20,20,0.5)', gridcolor: '#333', showbackground: true },
                                zaxis: { title: 'Depth (ft)', autorange: 'reversed', backgroundcolor: 'rgba(20,20,20,0.5)', gridcolor: '#333', showbackground: true },
                                aspectmode: 'cube', bgcolor: '#0a0a0a',
                            },
                        }}
                        config={{ responsive: true }} style={{ width: '100%' }}
                    />
                )}
                <InfoPanel
                    title="RESUMEN DEL ANÁLISIS 3D VOLUMÉTRICO"
                    wellName={wellName}
                    items={[
                        { label: `${xCol} Promedio`, value: xS.mean.toFixed(3), unit: xCol === 'PHI' ? 'frac' : '', color: '#22d3ee' },
                        { label: `${yCol} Promedio`, value: yS.mean.toFixed(3), unit: yCol === 'RHOB' ? 'g/cc' : '', color: '#ef4444' },
                        { label: `${colorBy} Rango`, value: `${cS.min.toFixed(2)} – ${cS.max.toFixed(2)}`, color: '#fbbf24' },
                        { label: 'Rango de Profundidad', value: depthRange, color: '#00f2ff' },
                        { label: 'Puntos 3D', value: depths.length.toLocaleString(), color: '#a78bfa' },
                        { label: `${colorBy} Std Dev`, value: cS.std.toFixed(3), color: '#fb923c' },
                    ]}
                    interpretation={`El cubo 3D muestra ${depths.length} muestras del pozo ${wellName}. ` +
                        `El eje X (${xCol}) varía de ${xS.min.toFixed(3)} a ${xS.max.toFixed(3)} con promedio ${xS.mean.toFixed(3)}. ` +
                        `El eje Y (${yCol}) varía de ${yS.min.toFixed(3)} a ${yS.max.toFixed(3)}. ` +
                        `La variable de color (${colorBy}) tiene un promedio de ${cS.mean.toFixed(2)} con desviación estándar de ${cS.std.toFixed(3)}. ` +
                        (colorBy === 'GR' ? 'Valores altos de GR (>75 API) indican zonas arcillosas; valores bajos (<40 API) indican arenas limpias.' :
                            colorBy === 'PHI' ? 'Zonas con alta porosidad (>15%) representan potencial de reservorio; baja porosidad indica zonas compactas.' :
                                colorBy === 'SW' ? 'Saturación de agua baja (<50%) indica posible presencia de hidrocarburos.' :
                                    `Distribución de ${colorBy} a lo largo del intervalo analizado.`)}
                    method="Litho-Scanner volumétrico: Visualización 3D interactiva de propiedades petrofísicas cruzadas vs profundidad. Los datos provienen directamente de las curvas del archivo LAS procesadas por el motor de cálculo Python. La escala de colores Jet permite identificar zonificación vertical y tendencias de facies."
                />
            </motion.div>
        </div>
    );
};

// ============ LITHOLOGY SECTION (Vsh + Phi fill) ============
export const LithologySection = ({ data, onClose }) => {
    const { curves, depths, well_info, kpis } = data || {};
    if (!curves?.vsh || !curves?.phi) return null;

    const wellName = well_info?.well_name || 'Pozo Activo';
    const vshS = stats(curves.vsh);
    const phiS = stats(curves.phi);
    const depthRange = depths?.length > 0 ? `${depths[0]?.toFixed(0)} – ${depths[depths.length - 1]?.toFixed(0)} ft` : 'N/A';

    // Zonas limpia vs arcillosa
    const cleanCount = curves.vsh.filter(v => v < 0.3).length;
    const shaleCount = curves.vsh.filter(v => v > 0.6).length;
    const cleanPct = ((cleanCount / curves.vsh.length) * 100).toFixed(0);
    const shalePct = ((shaleCount / curves.vsh.length) * 100).toFixed(0);

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    SECCIÓN ESTRATIGRÁFICA Y COMPOSICIÓN
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Evaluación litológica: Volumen de arcilla (Vsh) y Porosidad efectiva (Φ) vs profundidad
                </p>
                <Plot
                    data={[
                        { x: curves.vsh, y: depths, fill: 'tozerox', name: 'Vclay (Vsh)', line: { color: '#22c55e', shape: 'spline', smoothing: 0.3 }, fillcolor: 'rgba(34,197,94,0.3)' },
                        { x: curves.phi, y: depths, fill: 'tozerox', name: 'Porosidad (Φ)', line: { color: '#00f2ff', shape: 'spline', smoothing: 0.3 }, fillcolor: 'rgba(0,242,255,0.2)' },
                    ]}
                    layout={{
                        ...darkLayout, height: 600, title: 'Evaluación Litológica (Smoothed Spline)',
                        yaxis: { autorange: 'reversed', title: 'Profundidad (ft)', gridcolor: '#222' },
                        xaxis: { title: 'Fracción (0-1)', gridcolor: '#222', range: [0, 1] },
                        showlegend: true, legend: { x: 0.6, y: 0.02, bgcolor: 'rgba(0,0,0,0.5)', font: { color: '#ccc', size: 10 } },
                    }}
                    config={{ responsive: true }} style={{ width: '100%' }}
                />
                <InfoPanel
                    title="RESUMEN LITOLÓGICO"
                    wellName={wellName}
                    items={[
                        { label: 'Vsh Promedio', value: (vshS.mean * 100).toFixed(1) + '%', color: '#22c55e' },
                        { label: 'Φ Promedio', value: (phiS.mean * 100).toFixed(1) + '%', color: '#22d3ee' },
                        { label: 'Intervalo', value: depthRange, color: '#00f2ff' },
                        { label: 'Zona Limpia (Vsh<30%)', value: `${cleanPct}%`, unit: `(${cleanCount} muestras)`, color: '#4ade80' },
                        { label: 'Zona Arcillosa (Vsh>60%)', value: `${shalePct}%`, unit: `(${shaleCount} muestras)`, color: '#fbbf24' },
                        { label: 'Net Pay', value: kpis?.net_pay_ft || 0, unit: 'ft', color: '#f472b6' },
                    ]}
                    interpretation={`La sección litológica del pozo ${wellName} muestra que el ${cleanPct}% del intervalo corresponde a arenas limpias (Vsh<30%) aptas para reservorio, ` +
                        `mientras que el ${shalePct}% es arcilla (Vsh>60%). La porosidad efectiva promedio es ${(phiS.mean * 100).toFixed(1)}%, ` +
                        `con un máximo de ${(phiS.max * 100).toFixed(1)}% lo que sugiere ${phiS.max > 0.15 ? 'buen potencial de almacenamiento' : 'reservorio compacto con potencial limitado'}. ` +
                        `El relleno verde (Vclay) indica zonas de sello; el relleno cyan (Porosidad) indica zonas de reservorio.`}
                    method="Vsh calculado con método Linear (GR Index): (GR - GR_min) / (GR_max - GR_min). Porosidad calculada de NPHI o RHOB (ver metadata). Suavizado con interpolación spline cúbica para visualizar tendencias estratigráficas."
                />
            </motion.div>
        </div>
    );
};

import { calculateSynthetic } from '../utils/physics_models';

// ============ SEISMIC 2D SECTION ============
export const SeismicSection = ({ data, onClose }) => {
    // Calculo al vuelo si no viene del backend
    const computedGeo = useMemo(() => {
        if (data?.geophysics?.available) return data.geophysics;

        const wd = data?.well_data;
        if (!wd) return null;

        // Buscar curvas
        const findC = (aliases) => {
            for (const alias of aliases) {
                if (wd[alias]) return wd[alias];
                const key = Object.keys(wd).find(k => k.toUpperCase() === alias);
                if (key) return wd[key];
            }
            return null;
        };

        const depth = findC(['DEPTH', 'DEPT', 'MD']);
        const dt = findC(['DT', 'DTCO', 'DTC', 'SONIC']);
        const rhob = findC(['RHOB', 'RHO', 'DEN', 'DENSITY']);

        if (!depth || !dt) return null; // Necesito al menos Profundidad y Sónico

        const res = calculateSynthetic(depth, dt, rhob); // Usar utilidad nueva
        if (!res) return null;

        // Generar pseudosísmica 2D (repetir traza 50 veces)
        const nx = 50;
        const seismic_2d = [];
        for (let i = 0; i < nx; i++) {
            // Añadir un poco de ruido aleatorio para realismo visual en trazas lejanas
            const noise = i === nx / 2 ? 0 : (Math.random() - 0.5) * 0.1;
            seismic_2d.push(res.seismic.map(s => s + noise));
        }

        return {
            available: true,
            has_dt: true,
            seismic_depths: depth,
            seismic_nx: nx,
            seismic_2d: seismic_2d, // Array de arrays (Trazas) -> Plotly Heatmap quiere Z [y][x] o [x][y]? Check docs. Heatmap Z is usually 2D array.
            synthetic: res.seismic
        };

    }, [data]);

    const geo = computedGeo; // Usar el calculado

    if (!geo?.available) return (
        <div style={modalOverlay} onClick={onClose}>
            <div style={{ ...modalContent, height: 'auto', textAlign: 'center' }}>
                <h3 style={{ color: '#ef4444' }}>Datos Insuficientes</h3>
                <p>Se requiere curva Sónica (DT) para generar sísmica. Cargue un LAS con DT.</p>
                <button onClick={onClose} style={{ marginTop: 20, padding: '10px 20px', background: '#333', color: 'white', border: 'none', borderRadius: 8 }}>Cerrar</button>
            </div>
        </div>
    );

    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const depthRange = geo.seismic_depths?.length > 0 ? `${geo.seismic_depths[0]?.toFixed(0)} – ${geo.seismic_depths[geo.seismic_depths.length - 1]?.toFixed(0)} ft` : 'N/A';
    const synS = stats(geo.synthetic || []);

    // Transponer para Plotly Heatmap (Z debe ser array de arrays donde Z[row] es Y)
    // Mi seismic_2d es [Trace1_Array, Trace2_Array].
    // Plotly espera Z[y_index][x_index] usualmente o Z[row] correpondiente a Y.
    // Si meto Z = seismic_2d (donde cada row es una traza vertical X), entonces Z[x][y]. Plotly heatmap usa 'z' rows mapping to 'y' axis usually? 
    // Corrección rápida: Transponer para asegurar orientacion vertical correcta.
    const zData = geo.seismic_2d[0].map((_, colIndex) => geo.seismic_2d.map(row => row[colIndex]));

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    SECCIÓN SÍSMICA SINTÉTICA 2D (GENERADA EN VIVO)
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Sismograma generado por convolución Ricker 30Hz sobre reflectividad (DT/RHOB)
                </p>
                <Plot
                    data={[{
                        type: 'heatmap',
                        z: zData,
                        x: Array.from({ length: geo.seismic_nx }, (_, i) => i),
                        y: geo.seismic_depths,
                        colorscale: 'RdBu', zmid: 0, showscale: true,
                        colorbar: { title: 'Amplitud', thickness: 12 },
                    }, {
                        type: 'scatter', mode: 'lines',
                        x: Array(geo.seismic_depths.length).fill(geo.seismic_nx / 2),
                        y: geo.seismic_depths,
                        line: { color: '#00f2ff', width: 2, dash: 'dash' }, name: 'Ubicación Pozo',
                    }]}
                    layout={{
                        ...darkLayout, height: 600,
                        title: `Sísmica Sintética 2D`,
                        yaxis: { autorange: 'reversed', title: 'Profundidad MD (ft)', showgrid: false },
                        xaxis: { title: 'Lateral (Trazas Sintéticas)', showgrid: false },
                        showlegend: true, legend: { x: 0.01, y: 0.02, bgcolor: 'rgba(0,0,0,0.5)', font: { color: '#ccc' } },
                    }}
                    config={{ responsive: true }} style={{ width: '100%' }}
                />
                <InfoPanel
                    title="RESUMEN GEOFÍSICO"
                    wellName={wellName}
                    items={[
                        { label: 'Fuente', value: 'Cálculo Live (Frontend)', color: '#4ade80' },
                        { label: 'Profundidad', value: depthRange, color: '#00f2ff' },
                        { label: 'Ondícula', value: 'Ricker 30Hz', color: '#a78bfa' },
                        { label: 'Max Amplitud', value: synS.max.toFixed(4), color: '#ef4444' },
                    ]}
                    interpretation="Este sismograma sintético conecta la petrofísica (pozo) con la geofísica (sísmica). Los eventos de alta amplitud (Rojo/Azul fuerte) indican cambios bruscos de litología o contenido de fluídos (ej. tope de reservorio)."
                    method="1. Cálculo de Velocidad (1E6/DT). 2. Cálculo de Impedancia (V*Rho). 3. Coeficientes de Reflexión. 4. Convolución Wavelet Ricker."
                />
            </motion.div>
        </div>
    );
};

// ============ WELL TIE (Synthetic Seismogram) ============
export const WellTieModal = ({ data, onClose }) => {
    const geo = data?.geophysics;
    if (!geo?.available) return null;

    const depths = geo.seismic_depths;
    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const impS = stats(geo.impedance || []);
    const rcS = stats(geo.reflectivity || []);
    const synS = stats(geo.synthetic || []);

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ ...modalContent, maxWidth: '1400px' }} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    SISMOGRAMA SINTÉTICO — WELL TIE
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Modelo convolucional: Impedancia Acústica → Reflectividad → Wavelet Ricker → Traza Sintética
                </p>
                <Plot
                    data={[
                        { x: geo.impedance, y: depths, xaxis: 'x', yaxis: 'y', type: 'scatter', line: { color: 'yellow', width: 1.2 }, name: 'Impedancia (AI)' },
                        { x: geo.reflectivity, y: depths, xaxis: 'x2', yaxis: 'y', type: 'bar', orientation: 'h', marker: { color: 'cyan' }, name: 'RC', width: 0.3 },
                        { x: geo.synthetic, y: depths, xaxis: 'x3', yaxis: 'y', type: 'scatter', line: { color: 'white', width: 1 }, name: 'Sintético', fill: 'tozerox', fillcolor: 'rgba(0,255,255,0.3)' },
                        { x: geo.wavelet_amp, y: geo.wavelet_t, xaxis: 'x4', yaxis: 'y2', type: 'scatter', line: { color: 'magenta', width: 2 }, name: 'Wavelet Ricker' },
                    ]}
                    layout={{
                        ...darkLayout, height: 650, showlegend: true,
                        legend: { x: 0.45, y: 1.12, orientation: 'h', bgcolor: 'rgba(0,0,0,0.5)', font: { color: '#ccc', size: 9 } },
                        title: 'Modelo Convolucional Completo',
                        grid: { rows: 1, columns: 4, pattern: 'independent' },
                        xaxis: { title: 'AI (kg/m²s)', domain: [0, 0.22] },
                        xaxis2: { title: 'RC', domain: [0.25, 0.42] },
                        xaxis3: { title: 'Amplitud', domain: [0.45, 0.78] },
                        xaxis4: { title: 'Wavelet', domain: [0.82, 1] },
                        yaxis: { autorange: 'reversed', title: 'Profundidad (ft)', gridcolor: '#222' },
                        yaxis2: { title: 'Tiempo (s)', anchor: 'x4' },
                        annotations: [
                            { x: 0.11, y: 1.06, xref: 'paper', yref: 'paper', text: '① IMPEDANCIA', showarrow: false, font: { color: 'yellow', size: 10 } },
                            { x: 0.33, y: 1.06, xref: 'paper', yref: 'paper', text: '② REFLECTIVIDAD', showarrow: false, font: { color: 'cyan', size: 10 } },
                            { x: 0.61, y: 1.06, xref: 'paper', yref: 'paper', text: '③ SINTÉTICO', showarrow: false, font: { color: 'white', size: 10 } },
                            { x: 0.91, y: 1.06, xref: 'paper', yref: 'paper', text: '④ WAVELET', showarrow: false, font: { color: 'magenta', size: 10 } },
                        ],
                    }}
                    config={{ responsive: true }} style={{ width: '100%' }}
                />
                <InfoPanel
                    title="RESUMEN WELL TIE — SISMOGRAMA SINTÉTICO"
                    wellName={wellName}
                    items={[
                        { label: 'AI Promedio', value: impS.mean.toFixed(0), unit: 'kg/m²s', color: '#fbbf24' },
                        { label: 'AI Rango', value: `${impS.min.toFixed(0)} – ${impS.max.toFixed(0)}`, color: '#fbbf24' },
                        { label: 'RC Máx', value: rcS.max.toFixed(4), color: '#22d3ee' },
                        { label: 'RC Mín', value: rcS.min.toFixed(4), color: '#22d3ee' },
                        { label: 'Sintético Amplitud', value: `±${synS.max.toFixed(4)}`, color: '#fff' },
                        { label: 'Fuente DT', value: geo.has_dt ? 'Sónico Real' : 'Gardner Est.', color: geo.has_dt ? '#4ade80' : '#fb923c' },
                    ]}
                    interpretation={`El sismograma sintético del pozo ${wellName} muestra el proceso completo de Well Tie. ` +
                        `La Impedancia Acústica promedio es ${impS.mean.toFixed(0)} kg/m²s (rango: ${impS.min.toFixed(0)}-${impS.max.toFixed(0)}). ` +
                        `Los coeficientes de reflexión (RC) varían de ${rcS.min.toFixed(4)} a ${rcS.max.toFixed(4)} — ` +
                        `${Math.abs(rcS.max) > 0.1 ? 'se observan contrastes de impedancia fuertes (posibles cambios litológicos importantes)' : 'los contrastes son moderados, sugiriendo transiciones graduales'}. ` +
                        `La traza sintética fue generada mediante convolución con wavelet Ricker, lista para correlación con sísmica real.`}
                    method={"① Impedancia Acústica: AI = RHOB × Vp (donde Vp = 10⁶/DT o estimado por Gardner). " +
                        "② Coeficientes de Reflexión: RC[i] = (AI[i+1] - AI[i]) / (AI[i+1] + AI[i]). " +
                        "③ Wavelet Ricker: f(t) = (1 - 2π²f²t²) × exp(-π²f²t²), frecuencia central = 25 Hz. " +
                        "④ Convolución: Sintético = RC * Ricker (convolución en modo same)."}
                />
            </motion.div>
        </div>
    );
};

// ============ WELL TRAJECTORY 3D ============
export const WellTrajectory3D = ({ data, onClose }) => {
    const [colorBy, setColorBy] = useState('GR');
    const [spiral, setSpiral] = useState(true);
    const scatter = data?.scatter3d;
    if (!scatter) return null;

    const cols = scatter.available_columns || [];
    const colData = scatter.columns_data || {};
    const depths = scatter.depth_values || [];
    const n = depths.length;
    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const cS = stats(colData[colorBy] || []);

    let xArr, yArr;
    if (spiral) {
        const t = Array.from({ length: n }, (_, i) => (i / n) * 8 * Math.PI);
        xArr = t.map(v => 30 * Math.sin(v));
        yArr = t.map(v => 30 * Math.cos(v));
    } else {
        xArr = new Array(n).fill(0);
        yArr = new Array(n).fill(0);
    }

    const depthRange = depths.length > 0 ? `${depths[0]?.toFixed(0)} – ${depths[depths.length - 1]?.toFixed(0)} ft` : 'N/A';
    const totalDepth = depths.length > 0 ? (depths[depths.length - 1] - depths[0]).toFixed(0) : 0;

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    TRAYECTORIA 3D DEL POZO Y PROPIEDADES
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Trayectoria del pozo coloreada por propiedad petrofísica seleccionada
                </p>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <label style={{ fontSize: '10px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                        <input type="checkbox" checked={spiral} onChange={() => setSpiral(!spiral)} /> Desviación Espacial
                    </label>
                    <span style={{ fontSize: '10px', opacity: 0.5 }}>| Color:</span>
                    {cols.filter(c => ['GR', 'VSH', 'PHI', 'SW', 'RT', 'PERM'].includes(c)).map(c => (
                        <button key={c} onClick={() => setColorBy(c)} style={{
                            padding: '4px 10px', borderRadius: '20px', fontSize: '9px', fontWeight: 700, cursor: 'pointer',
                            background: colorBy === c ? 'rgba(0,242,255,0.15)' : 'transparent',
                            border: colorBy === c ? '1px solid #00f2ff' : '1px solid #222', color: colorBy === c ? '#00f2ff' : '#666',
                        }}>{c}</button>
                    ))}
                </div>
                <Plot
                    data={[{
                        type: 'scatter3d', mode: 'markers',
                        x: xArr, y: yArr, z: depths,
                        marker: {
                            size: 4, color: colData[colorBy] || depths,
                            colorscale: 'Jet', opacity: 0.8,
                            colorbar: { title: colorBy, thickness: 12 },
                        },
                        hovertemplate: `Depth: %{z:.1f} ft<br>${colorBy}: %{marker.color:.2f}<extra></extra>`,
                    }]}
                    layout={{
                        ...darkLayout, height: 550,
                        title: `Trayectoria: ${wellName} (Color: ${colorBy})`,
                        scene: {
                            xaxis: { title: 'X (m)' }, yaxis: { title: 'Y (m)' },
                            zaxis: { title: 'MD/TVD (ft)', autorange: 'reversed' },
                            aspectmode: 'manual', aspectratio: { x: 1, y: 1, z: 3 },
                        },
                    }}
                    config={{ responsive: true }} style={{ width: '100%' }}
                />
                <InfoPanel
                    title="RESUMEN DE TRAYECTORIA"
                    wellName={wellName}
                    items={[
                        { label: 'Profundidad Total', value: `${totalDepth} ft`, color: '#00f2ff' },
                        { label: 'Rango MD', value: depthRange, color: '#a78bfa' },
                        { label: `${colorBy} Promedio`, value: cS.mean.toFixed(2), color: '#fbbf24' },
                        { label: `${colorBy} Máx`, value: cS.max.toFixed(2), color: '#ef4444' },
                        { label: 'Muestras', value: n.toLocaleString(), color: '#22d3ee' },
                        { label: 'Modo', value: spiral ? 'Deviated' : 'Vertical', color: '#4ade80' },
                    ]}
                    interpretation={`La trayectoria del pozo ${wellName} cubre ${totalDepth} ft de profundidad con ${n} puntos de muestreo. ` +
                        `La propiedad ${colorBy} varía de ${cS.min.toFixed(2)} a ${cS.max.toFixed(2)} (media: ${cS.mean.toFixed(2)}). ` +
                        (spiral ? 'Nota: La geometría X-Y es esquemática para visualización 3D; la profundidad (Z) y los colores son DATOS REALES.' :
                            'Visualización vertical estricta — cada punto representa datos reales a la profundidad indicada.')}
                    method="La trayectoria se construye proyectando las muestras del LAS en un modelo 3D. Si se activa 'Desviación Espacial', la geometría X-Y simula drift lateral con función sinusoidal. Los datos de profundidad y propiedades son 100% reales del archivo LAS."
                />
            </motion.div>
        </div>
    );
};
