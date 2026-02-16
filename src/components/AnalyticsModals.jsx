import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { X, Info } from 'lucide-react';
import { motion } from 'framer-motion';

const modalOverlay = {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)',
    zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '15px',
};
const modalContent = {
    background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a',
    width: '95%', maxWidth: '1200px', maxHeight: '90vh', overflow: 'auto', padding: '25px', position: 'relative',
};
const closeBtn = {
    position: 'absolute', top: '15px', right: '15px', background: 'rgba(255,255,255,0.05)',
    border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white', zIndex: 10,
};
const darkLayout = {
    template: 'plotly_dark', paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 50, r: 30, t: 50, b: 50 }, font: { family: 'Space Grotesk, sans-serif' },
};

// ========= Helper: stats =========
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

// ========= InfoPanel =========
const InfoPanel = ({ title, items, interpretation, method, wellName }) => (
    <div style={{ marginTop: '15px', background: 'rgba(0,242,255,0.03)', borderRadius: '16px', border: '1px solid rgba(0,242,255,0.08)', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Info size={14} color="#00f2ff" />
            <span style={{ fontSize: '11px', fontWeight: 900, color: '#00f2ff', letterSpacing: '1px' }}>{title}</span>
            {wellName && <span style={{ fontSize: '9px', opacity: 0.4, marginLeft: 'auto' }}>Pozo: {wellName}</span>}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px', marginBottom: '12px' }}>
            {items.map((item, i) => (
                <div key={i} style={{ padding: '8px 12px', background: '#0a0a0a', borderRadius: '10px', border: '1px solid #151515' }}>
                    <span style={{ fontSize: '8px', fontWeight: 700, color: '#555', display: 'block', letterSpacing: '0.5px' }}>{item.label}</span>
                    <span style={{ fontSize: '13px', fontWeight: 900, color: item.color || '#fff' }}>{item.value}</span>
                    {item.unit && <span style={{ fontSize: '8px', color: '#666', marginLeft: '3px' }}>{item.unit}</span>}
                </div>
            ))}
        </div>
        {interpretation && (
            <div style={{ padding: '10px 14px', background: 'rgba(74,222,128,0.04)', borderRadius: '10px', border: '1px solid rgba(74,222,128,0.1)', marginBottom: '8px' }}>
                <span style={{ fontSize: '8px', fontWeight: 800, color: '#4ade80', letterSpacing: '1px', display: 'block', marginBottom: '4px' }}>INTERPRETACIÓN</span>
                <p style={{ margin: 0, fontSize: '10px', opacity: 0.7, lineHeight: '1.6' }}>{interpretation}</p>
            </div>
        )}
        {method && (
            <div style={{ padding: '10px 14px', background: 'rgba(251,191,36,0.04)', borderRadius: '10px', border: '1px solid rgba(251,191,36,0.1)' }}>
                <span style={{ fontSize: '8px', fontWeight: 800, color: '#fbbf24', letterSpacing: '1px', display: 'block', marginBottom: '4px' }}>METODOLOGÍA</span>
                <p style={{ margin: 0, fontSize: '10px', opacity: 0.6, lineHeight: '1.6' }}>{method}</p>
            </div>
        )}
    </div>
);

// Units map
const UNITS = { GR: 'API', RT: 'Ω·m', NPHI: 'v/v', RHOB: 'g/cc', VSH: 'frac', PHI: 'frac', SW: 'frac', PERM: 'mD', SH: 'frac', DT: 'μs/ft', K: 'mD' };

// ============ HISTOGRAM DISTRIBUTION ============
export const HistogramModal = ({ data, onClose }) => {
    const hists = data?.histograms || {};
    const keys = Object.keys(hists);
    const [selected, setSelected] = useState(keys[0] || 'GR');
    const wellName = data?.well_info?.well_name || 'Pozo Activo';

    if (keys.length === 0) return null;
    const hist = hists[selected];

    const barX = hist ? hist.bin_edges.slice(0, -1).map((v, i) => (v + hist.bin_edges[i + 1]) / 2) : [];
    const totalSamples = hist ? hist.counts.reduce((a, b) => a + b, 0) : 0;
    const maxBin = hist ? Math.max(...hist.counts) : 0;
    const maxBinVal = hist ? barX[hist.counts.indexOf(maxBin)] : 0;
    const unit = UNITS[selected] || '';

    // Descriptive stats from histogram
    const calcMean = () => {
        if (!hist) return 0;
        let sum = 0, count = 0;
        barX.forEach((x, i) => { sum += x * hist.counts[i]; count += hist.counts[i]; });
        return count > 0 ? sum / count : 0;
    };
    const histMean = calcMean();

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    ANÁLISIS DE DISTRIBUCIÓN
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Histograma de distribución estadística de cada propiedad petrofísica
                </p>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '15px', flexWrap: 'wrap' }}>
                    {keys.map(k => (
                        <button key={k} onClick={() => setSelected(k)} style={{
                            padding: '5px 14px', borderRadius: '20px', fontSize: '10px', fontWeight: 700, cursor: 'pointer',
                            background: selected === k ? 'rgba(0,242,255,0.15)' : 'transparent',
                            border: selected === k ? '1px solid #00f2ff' : '1px solid #222', color: selected === k ? '#00f2ff' : '#666',
                        }}>{k}{unit ? ` (${UNITS[k] || ''})` : ''}</button>
                    ))}
                </div>
                {hist && (
                    <Plot
                        data={[{
                            type: 'bar', x: barX, y: hist.counts,
                            marker: { color: barX.map(v => v >= histMean ? '#00d2ff' : '#005577'), line: { color: '#fff', width: 0.3 } },
                            hovertemplate: `${selected}: %{x:.3f} ${unit}<br>Muestras: %{y}<extra></extra>`,
                        }]}
                        layout={{
                            ...darkLayout, height: 450,
                            title: `Distribución: ${selected} (${unit})`,
                            xaxis: { title: `${selected} (${unit})`, gridcolor: '#222' },
                            yaxis: { title: 'Frecuencia (# muestras)', gridcolor: '#222' },
                            bargap: 0.05,
                            shapes: [{ type: 'line', x0: histMean, x1: histMean, y0: 0, y1: maxBin, line: { color: '#fbbf24', width: 2, dash: 'dash' } }],
                            annotations: [{ x: histMean, y: maxBin * 0.95, text: `μ = ${histMean.toFixed(3)}`, showarrow: false, font: { color: '#fbbf24', size: 11 } }],
                        }}
                        config={{ responsive: true }} style={{ width: '100%' }}
                    />
                )}
                <InfoPanel
                    title={`RESUMEN ESTADÍSTICO — ${selected}`}
                    wellName={wellName}
                    items={[
                        { label: 'Curva', value: selected, unit, color: '#00f2ff' },
                        { label: 'Media (μ)', value: histMean.toFixed(3), unit, color: '#fbbf24' },
                        { label: 'Moda (Bin Máx)', value: maxBinVal.toFixed(3), unit, color: '#4ade80' },
                        { label: 'Total Muestras', value: totalSamples.toLocaleString(), color: '#a78bfa' },
                        { label: 'Bins', value: barX.length, color: '#fb923c' },
                        { label: 'Rango', value: `${barX[0]?.toFixed(3)} – ${barX[barX.length - 1]?.toFixed(3)}`, unit, color: '#ef4444' },
                    ]}
                    interpretation={`La distribución de ${selected} en el pozo ${wellName} muestra una media de ${histMean.toFixed(3)} ${unit} con un total de ${totalSamples} muestras. ` +
                        `El valor más frecuente (moda) está en ${maxBinVal.toFixed(3)} ${unit} con ${maxBin} ocurrencias. ` +
                        (selected === 'GR' ? `Valores de GR < 40 API indican arenas limpias; > 75 API indican lutitas. La media de ${histMean.toFixed(0)} API sugiere ${histMean < 60 ? 'predominio de arenas' : 'mezcla arena-arcilla'}.` :
                            selected === 'PHI' ? `Porosidades > 15% son generalmente aceptables para reservorio. La media de ${(histMean * 100).toFixed(1)}% ${histMean > 0.12 ? 'indica buen potencial' : 'sugiere un reservorio compacto'}.` :
                                selected === 'SW' ? `Sw < 50% sugiere zonas con hidrocarburo. La media de ${(histMean * 100).toFixed(1)}% ${histMean < 0.5 ? 'indica potencial HC significativo' : 'sugiere predominio de agua'}.` :
                                    `La línea amarilla punteada marca la media. Barras claras están por encima del promedio.`)}
                    method="Histograma con 40 bins equiespaciados. La línea punteada amarilla muestra la media aritmética (μ). Las barras más oscuras representan valores debajo del promedio; las claras por encima. Datos calculados directamente del archivo LAS por el motor Python."
                />
            </motion.div>
        </div>
    );
};

// ============ RADAR CHART (Rock Quality Index) ============
export const RadarModal = ({ data, onClose }) => {
    const radar = data?.radar;
    if (!radar) return null;

    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const cats = [...radar.categories, radar.categories[0]];
    const scores = [...radar.scores, radar.scores[0]];
    const avgScore = radar.scores.reduce((a, b) => a + b, 0) / radar.scores.length;
    const bestCat = radar.categories[radar.scores.indexOf(Math.max(...radar.scores))];
    const worstCat = radar.categories[radar.scores.indexOf(Math.min(...radar.scores))];

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    ÍNDICE DE CALIDAD DE ROCA (RQI)
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Radar multidimensional de calidad del reservorio — 5 dimensiones normalizadas (0-100%)
                </p>
                <Plot
                    data={[{
                        type: 'scatterpolar', r: scores, theta: cats,
                        fill: 'toself', fillcolor: 'rgba(0,210,255,0.25)',
                        line: { color: '#00d2ff', width: 2 },
                        marker: { size: 8, color: '#4ade80' },
                        hovertemplate: '%{theta}: %{r:.0%}<extra></extra>',
                    }]}
                    layout={{
                        ...darkLayout, height: 450,
                        polar: {
                            radialaxis: { visible: true, range: [0, 1], gridcolor: '#333', tickfont: { color: '#888' }, tickformat: '.0%' },
                            angularaxis: { gridcolor: '#333', tickfont: { color: '#ccc', size: 11 } },
                            bgcolor: 'rgba(0,0,0,0)',
                        },
                        showlegend: false,
                    }}
                    config={{ responsive: true }} style={{ width: '100%' }}
                />
                <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '10px', flexWrap: 'wrap' }}>
                    {radar.categories.map((c, i) => (
                        <div key={i} style={{ textAlign: 'center' }}>
                            <span style={{ fontSize: '9px', opacity: 0.5, display: 'block' }}>{c}</span>
                            <span style={{ fontSize: '16px', fontWeight: 900, color: radar.scores[i] > 0.6 ? '#4ade80' : radar.scores[i] > 0.3 ? '#fbbf24' : '#ef4444' }}>
                                {(radar.scores[i] * 100).toFixed(0)}%
                            </span>
                        </div>
                    ))}
                </div>
                <InfoPanel
                    title="RESUMEN RQI — CALIDAD DEL RESERVORIO"
                    wellName={wellName}
                    items={[
                        { label: 'Score Global', value: `${(avgScore * 100).toFixed(0)}%`, color: avgScore > 0.6 ? '#4ade80' : avgScore > 0.3 ? '#fbbf24' : '#ef4444' },
                        { label: 'Mejor Categoría', value: bestCat, color: '#4ade80' },
                        { label: 'Categoría Débil', value: worstCat, color: '#ef4444' },
                        { label: 'Calidad', value: avgScore > 0.7 ? 'EXCELENTE' : avgScore > 0.5 ? 'BUENO' : avgScore > 0.3 ? 'MODERADO' : 'BAJO', color: avgScore > 0.5 ? '#4ade80' : '#fbbf24' },
                        ...radar.categories.map((c, i) => ({ label: c, value: `${(radar.scores[i] * 100).toFixed(0)}%`, color: radar.scores[i] > 0.6 ? '#4ade80' : '#fbbf24' })),
                    ]}
                    interpretation={`El Índice de Calidad de Roca (RQI) del pozo ${wellName} tiene un score global de ${(avgScore * 100).toFixed(0)}%, clasificado como ${avgScore > 0.7 ? 'EXCELENTE — reservorio de alta calidad con buenas propiedades multidimensionales' : avgScore > 0.5 ? 'BUENO — potencial de reservorio con áreas de mejora' : 'MODERADO/BAJO — requiere evaluación adicional'}. ` +
                        `La categoría más fuerte es "${bestCat}" (${(Math.max(...radar.scores) * 100).toFixed(0)}%) y la más débil es "${worstCat}" (${(Math.min(...radar.scores) * 100).toFixed(0)}%). ` +
                        `Un perfil radar equilibrado (forma circular) indica un reservorio homogéneo; un perfil asimétrico indica heterogeneidad.`}
                    method="Cada dimensión se normaliza (0-1): Porosidad vs max teórico, Saturación HC (1-Sw), Limpieza (1-Vsh), Potencial Económico (K × H × (1-Sw)), Calidad de Datos (% curvas sin NaN). El score global es el promedio de las 5 dimensiones."
                />
            </motion.div>
        </div>
    );
};

// ============ SCATTER CORRELATIONS ============
export const ScatterModal = ({ data, onClose }) => {
    const corr = data?.correlations;
    const scatter = data?.scatter3d;
    if (!corr || !scatter) return null;

    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const cols = corr.columns || [];
    const [xCol, setXCol] = useState(cols[0] || '');
    const [yCol, setYCol] = useState(cols[Math.min(1, cols.length - 1)] || '');

    const colData = scatter.columns_data || {};
    const pair = corr.pairs?.find(p => (p.x === xCol && p.y === yCol) || (p.x === yCol && p.y === xCol));
    const rVal = pair ? pair.r : null;
    const topPair = corr.pairs?.[0];

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    CORRELACIÓN CRUZADA ENTRE PROPIEDADES
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Análisis de dependencia lineal entre curvas petrofísicas — Coeficiente de Pearson (R)
                </p>
                <div style={{ display: 'flex', gap: '15px', marginBottom: '15px', flexWrap: 'wrap' }}>
                    <div>
                        <span style={{ fontSize: '9px', opacity: 0.5 }}>Eje X</span>
                        <select value={xCol} onChange={e => setXCol(e.target.value)} style={{ display: 'block', background: '#111', color: 'white', border: '1px solid #333', borderRadius: '8px', padding: '6px 12px', fontSize: '11px' }}>
                            {cols.map(c => <option key={c} value={c}>{c} ({UNITS[c] || ''})</option>)}
                        </select>
                    </div>
                    <div>
                        <span style={{ fontSize: '9px', opacity: 0.5 }}>Eje Y</span>
                        <select value={yCol} onChange={e => setYCol(e.target.value)} style={{ display: 'block', background: '#111', color: 'white', border: '1px solid #333', borderRadius: '8px', padding: '6px 12px', fontSize: '11px' }}>
                            {cols.map(c => <option key={c} value={c}>{c} ({UNITS[c] || ''})</option>)}
                        </select>
                    </div>
                    {rVal !== null && (
                        <div style={{ alignSelf: 'flex-end', padding: '6px 14px', background: Math.abs(rVal) > 0.7 ? 'rgba(74,222,128,0.1)' : 'rgba(251,191,36,0.1)', borderRadius: '12px', border: `1px solid ${Math.abs(rVal) > 0.7 ? '#4ade80' : '#fbbf24'}40` }}>
                            <span style={{ fontSize: '9px', opacity: 0.5 }}>Pearson R = </span>
                            <span style={{ fontSize: '14px', fontWeight: 900, color: Math.abs(rVal) > 0.7 ? '#4ade80' : '#fbbf24' }}>{rVal}</span>
                        </div>
                    )}
                </div>
                {colData[xCol] && colData[yCol] && (
                    <Plot
                        data={[{
                            type: 'scatter', mode: 'markers',
                            x: colData[xCol], y: colData[yCol],
                            marker: {
                                size: 5, color: colData[yCol],
                                colorscale: [[0, 'darkblue'], [0.33, 'lightblue'], [0.66, 'orange'], [1, 'red']],
                                showscale: true, colorbar: { title: `${yCol} (${UNITS[yCol] || ''})`, thickness: 12 },
                            },
                            hovertemplate: `${xCol}: %{x:.3f}<br>${yCol}: %{y:.3f}<extra></extra>`,
                        }]}
                        layout={{
                            ...darkLayout, height: 450,
                            title: `${xCol} vs ${yCol} ${rVal !== null ? `(R = ${rVal})` : ''}`,
                            xaxis: { title: `${xCol} (${UNITS[xCol] || ''})`, gridcolor: 'rgba(128,128,128,0.2)', showline: true, linewidth: 2, linecolor: 'white', mirror: true },
                            yaxis: { title: `${yCol} (${UNITS[yCol] || ''})`, gridcolor: 'rgba(128,128,128,0.2)', showline: true, linewidth: 2, linecolor: 'white', mirror: true },
                        }}
                        config={{ responsive: true }} style={{ width: '100%' }}
                    />
                )}
                {/* Top correlations */}
                <div style={{ marginTop: '15px' }}>
                    <h4 style={{ fontSize: '11px', fontWeight: 800, opacity: 0.5, marginBottom: '8px' }}>TOP CORRELACIONES ({corr.pairs?.length || 0} pares)</h4>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {corr.pairs?.slice(0, 8).map((p, i) => (
                            <button key={i} onClick={() => { setXCol(p.x); setYCol(p.y); }} style={{
                                padding: '5px 12px', borderRadius: '20px', fontSize: '9px', cursor: 'pointer',
                                background: 'rgba(255,255,255,0.03)', border: '1px solid #222', color: '#aaa',
                            }}>
                                {p.x}↔{p.y}: <span style={{ fontWeight: 900, color: Math.abs(p.r) > 0.7 ? '#4ade80' : '#fbbf24' }}>{p.r}</span>
                            </button>
                        ))}
                    </div>
                </div>
                <InfoPanel
                    title="RESUMEN DE CORRELACIONES"
                    wellName={wellName}
                    items={[
                        { label: 'Par Actual', value: `${xCol} ↔ ${yCol}`, color: '#00f2ff' },
                        { label: 'Pearson R', value: rVal !== null ? rVal.toString() : 'N/A', color: rVal && Math.abs(rVal) > 0.7 ? '#4ade80' : '#fbbf24' },
                        { label: 'Correlación', value: rVal ? (Math.abs(rVal) > 0.7 ? 'FUERTE' : Math.abs(rVal) > 0.4 ? 'MODERADA' : 'DÉBIL') : '-', color: rVal && Math.abs(rVal) > 0.7 ? '#4ade80' : '#fbbf24' },
                        { label: 'Top Correlación', value: topPair ? `${topPair.x}↔${topPair.y} (${topPair.r})` : '-', color: '#a78bfa' },
                        { label: 'Total Pares', value: corr.pairs?.length || 0, color: '#fb923c' },
                        { label: 'Curvas Analizadas', value: cols.length, color: '#22d3ee' },
                    ]}
                    interpretation={rVal !== null ?
                        `El par ${xCol} vs ${yCol} tiene un coeficiente de Pearson R = ${rVal}, indicando una correlación ${Math.abs(rVal) > 0.7 ? 'FUERTE' : Math.abs(rVal) > 0.4 ? 'MODERADA' : 'DÉBIL'}${rVal > 0 ? ' positiva' : ' negativa'}. ` +
                        (Math.abs(rVal) > 0.7 ? `Esto sugiere una relación directa significativa entre estas propiedades — útil para predicción y modelado.` :
                            `Una correlación ${Math.abs(rVal) < 0.3 ? 'muy baja sugiere independencia estadística' : 'moderada sugiere influencia parcial'} entre las variables.`) +
                        ` La correlación más fuerte del dataset es ${topPair?.x}↔${topPair?.y} con R=${topPair?.r}.` :
                        `Seleccione dos variables para analizar su correlación.`}
                    method="Coeficiente de correlación de Pearson: R = Σ((xi-μx)(yi-μy)) / (n·σx·σy). Valores |R|>0.7 = correlación fuerte; 0.4-0.7 = moderada; <0.4 = débil. La escala de color en el scatter sigue los valores del eje Y para identificar clusters y tendencias."
                />
            </motion.div>
        </div>
    );
};

// ============ 4D BUBBLE EXPLORER ============
export const BubbleExplorer = ({ data, onClose }) => {
    const scatter = data?.scatter3d;
    if (!scatter) return null;

    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const cols = scatter.available_columns || [];
    const colData = scatter.columns_data || {};
    const depths = scatter.depth_values || [];

    const [xC, setXC] = useState(cols.includes('NPHI') ? 'NPHI' : cols[0]);
    const [yC, setYC] = useState(cols.includes('RHOB') ? 'RHOB' : cols[Math.min(1, cols.length - 1)]);
    const [sC, setSC] = useState(cols.includes('GR') ? 'GR' : cols[Math.min(2, cols.length - 1)]);

    const sData = colData[sC] || [];
    const sMin = Math.min(...sData.filter(v => isFinite(v)));
    const sMax = Math.max(...sData.filter(v => isFinite(v)));
    const denom = (sMax - sMin) > 0.00001 ? (sMax - sMin) : 1;
    const sizes = sData.map(v => ((v - sMin) / denom) * 30 + 4);

    const xS = stats(colData[xC]);
    const yS = stats(colData[yC]);
    const sS = stats(sData);

    const sel = (label, val, setVal) => (
        <div>
            <span style={{ fontSize: '8px', opacity: 0.4, display: 'block' }}>{label}</span>
            <select value={val} onChange={e => setVal(e.target.value)} style={{ background: '#111', color: 'white', border: '1px solid #333', borderRadius: '8px', padding: '5px 10px', fontSize: '10px' }}>
                {cols.map(c => <option key={c} value={c}>{c} ({UNITS[c] || ''})</option>)}
            </select>
        </div>
    );

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    EXPLORADOR 4D DE PROPIEDADES
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    4 dimensiones: Eje X + Eje Y + Profundidad (Z) + Tamaño/Color de esfera
                </p>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '15px', flexWrap: 'wrap' }}>
                    {sel('Eje X', xC, setXC)}
                    {sel('Eje Y', yC, setYC)}
                    {sel('Tamaño/Color', sC, setSC)}
                </div>
                {colData[xC] && colData[yC] && (
                    <Plot
                        data={[{
                            type: 'scatter3d', mode: 'markers',
                            x: colData[xC], y: colData[yC], z: depths,
                            marker: {
                                size: sizes, color: colData[sC] || depths,
                                colorscale: [[0, 'rgb(255,128,0)'], [1, 'rgb(0,128,255)']],
                                opacity: 0.85, line: { width: 0 },
                                colorbar: { title: `${sC} (${UNITS[sC] || ''})`, thickness: 12 },
                            },
                            hovertemplate: `${xC}: %{x:.3f}<br>${yC}: %{y:.3f}<br>Depth: %{z:.1f} ft<br>${sC}: %{marker.color:.3f}<extra></extra>`,
                        }]}
                        layout={{
                            ...darkLayout, height: 550,
                            title: `4D Explorer: ${xC} × ${yC} × Depth (Size: ${sC})`,
                            scene: {
                                xaxis: { title: `${xC} (${UNITS[xC] || ''})`, backgroundcolor: 'rgba(20,20,20,0.5)', gridcolor: 'gray', showbackground: true },
                                yaxis: { title: `${yC} (${UNITS[yC] || ''})`, backgroundcolor: 'rgba(20,20,20,0.5)', gridcolor: 'gray', showbackground: true },
                                zaxis: { title: 'Depth (ft)', backgroundcolor: 'rgba(20,20,20,0.5)', gridcolor: 'gray', showbackground: true },
                                bgcolor: '#0a0a0a', aspectmode: 'cube',
                            },
                        }}
                        config={{ responsive: true }} style={{ width: '100%' }}
                    />
                )}
                <InfoPanel
                    title="RESUMEN EXPLORADOR 4D"
                    wellName={wellName}
                    items={[
                        { label: `${xC} Media`, value: xS.mean.toFixed(3), unit: UNITS[xC] || '', color: '#fb923c' },
                        { label: `${yC} Media`, value: yS.mean.toFixed(3), unit: UNITS[yC] || '', color: '#3b82f6' },
                        { label: `${sC} Media`, value: sS.mean.toFixed(3), unit: UNITS[sC] || '', color: '#00f2ff' },
                        { label: `${sC} Rango`, value: `${sS.min.toFixed(2)} – ${sS.max.toFixed(2)}`, color: '#fbbf24' },
                        { label: 'Puntos 3D', value: depths.length.toLocaleString(), color: '#a78bfa' },
                        { label: 'Prof. Total', value: depths.length > 0 ? `${(depths[depths.length - 1] - depths[0]).toFixed(0)} ft` : 'N/A', color: '#22d3ee' },
                    ]}
                    interpretation={`El explorador 4D muestra ${depths.length} muestras en 4 dimensiones simultáneas. ` +
                        `Esferas grandes naranja = valores altos de ${sC} (${sS.max.toFixed(2)} ${UNITS[sC] || ''}) — representan zonas de interés ("sweet spots"). ` +
                        `Esferas pequeñas azules = valores bajos (${sS.min.toFixed(2)}). ` +
                        `Busque clusters de esferas grandes naranja en profundidades específicas para identificar intervalos con mejores propiedades de reservorio.`}
                    method={`Visualización 4D: Ejes X (${xC}), Y (${yC}), Z (Depth). La 4ta dimensión (${sC}) se mapea al tamaño de la esfera (proporcional) y al color (escala naranja→azul). Los datos son 100% reales del LAS, submuestreados para rendimiento.`}
                />
            </motion.div>
        </div>
    );
};

// ============ PRODUCTION SIMULATION ============
export const ProductionModal = ({ data, onClose }) => {
    const prod = data?.production;
    if (!prod) return null;

    const wellName = data?.well_info?.well_name || 'Pozo Activo';
    const totalBarrels = prod.barrels ? prod.barrels.reduce((a, b) => a + b, 0) : 0;
    const peakRate = prod.barrels ? Math.max(...prod.barrels) : 0;
    const lastRate = prod.barrels ? prod.barrels[prod.barrels.length - 1] : 0;
    const declinePct = peakRate > 0 ? ((1 - lastRate / peakRate) * 100).toFixed(0) : 0;

    return (
        <div style={modalOverlay} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={modalContent} onClick={e => e.stopPropagation()}>
                <button style={closeBtn} onClick={onClose}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '5px' }}>
                    PRONÓSTICO DE PRODUCCIÓN (DECLINACIÓN ARPS)
                </h2>
                <p style={{ fontSize: '10px', opacity: 0.4, marginBottom: '15px' }}>
                    Simulación de producción exponencial basada en parámetros petrofísicos del pozo
                </p>
                <div style={{ display: 'flex', gap: '15px', marginBottom: '20px', flexWrap: 'wrap' }}>
                    <div style={{ padding: '12px 20px', background: 'rgba(0,242,255,0.05)', borderRadius: '15px', border: '1px solid rgba(0,242,255,0.1)' }}>
                        <span style={{ fontSize: '9px', opacity: 0.4, display: 'block' }}>OIP Estimado</span>
                        <span style={{ fontSize: '18px', fontWeight: 900, color: '#00f2ff' }}>{(prod.oip_estimate / 1e6).toFixed(2)} MM STB</span>
                    </div>
                    <div style={{ padding: '12px 20px', background: 'rgba(74,222,128,0.05)', borderRadius: '15px', border: '1px solid rgba(74,222,128,0.1)' }}>
                        <span style={{ fontSize: '9px', opacity: 0.4, display: 'block' }}>Ingresos Totales (10 años)</span>
                        <span style={{ fontSize: '18px', fontWeight: 900, color: '#4ade80' }}>${(prod.total_revenue_10y / 1e6).toFixed(1)} MM</span>
                    </div>
                    <div style={{ padding: '12px 20px', background: 'rgba(251,146,60,0.05)', borderRadius: '15px', border: '1px solid rgba(251,146,60,0.1)' }}>
                        <span style={{ fontSize: '9px', opacity: 0.4, display: 'block' }}>Producción Acumulada</span>
                        <span style={{ fontSize: '18px', fontWeight: 900, color: '#fb923c' }}>{(totalBarrels / 1e6).toFixed(2)} MM bbl</span>
                    </div>
                </div>
                <Plot
                    data={[
                        {
                            x: prod.months, y: prod.revenue, type: 'scatter', fill: 'tozeroy', fillcolor: 'rgba(0,242,255,0.15)', line: { color: '#00f2ff', width: 2 }, name: 'Ingresos (USD/mes)', yaxis: 'y',
                            hovertemplate: 'Mes %{x}<br>Ingresos: $%{y:,.0f}<extra></extra>'
                        },
                        {
                            x: prod.months, y: prod.barrels, type: 'scatter', line: { color: '#fb923c', width: 2, dash: 'dot' }, name: 'Producción (bbl/mes)', yaxis: 'y2',
                            hovertemplate: 'Mes %{x}<br>Producción: %{y:,.0f} bbl<extra></extra>'
                        },
                    ]}
                    layout={{
                        ...darkLayout, height: 400,
                        title: 'Declinación Exponencial Arps — Pronóstico 10 Años',
                        xaxis: { title: 'Mes', gridcolor: '#222' },
                        yaxis: { title: 'Ingresos (USD/mes)', side: 'left', gridcolor: '#222' },
                        yaxis2: { title: 'Barriles/Mes', side: 'right', overlaying: 'y', showgrid: false },
                        legend: { x: 0.5, y: 0.95, bgcolor: 'rgba(0,0,0,0.5)', font: { color: '#ccc', size: 10 } },
                    }}
                    config={{ responsive: true }} style={{ width: '100%' }}
                />
                <InfoPanel
                    title="RESUMEN DE PRODUCCIÓN Y ECONOMÍA"
                    wellName={wellName}
                    items={[
                        { label: 'OIP Estimado', value: `${(prod.oip_estimate / 1e6).toFixed(2)} MM`, unit: 'STB', color: '#00f2ff' },
                        { label: 'Ingresos 10yr', value: `$${(prod.total_revenue_10y / 1e6).toFixed(1)} MM`, color: '#4ade80' },
                        { label: 'Producción Acumulada', value: `${(totalBarrels / 1e6).toFixed(2)} MM`, unit: 'bbl', color: '#fb923c' },
                        { label: 'Tasa Inicial', value: peakRate.toFixed(0), unit: 'bbl/mes', color: '#fbbf24' },
                        { label: 'Tasa Final (Mes 120)', value: lastRate.toFixed(0), unit: 'bbl/mes', color: '#ef4444' },
                        { label: 'Declinación Total', value: `${declinePct}%`, color: '#f472b6' },
                    ]}
                    interpretation={`Basado en las propiedades petrofísicas del pozo ${wellName}, el OIP estimado es ${(prod.oip_estimate / 1e6).toFixed(2)} millones de barriles. ` +
                        `Con una tasa inicial de ${peakRate.toFixed(0)} bbl/mes y declinación exponencial de 5%/año, la producción acumulada en 10 años sería ${(totalBarrels / 1e6).toFixed(2)} MM bbl, ` +
                        `generando ingresos totales estimados de $${(prod.total_revenue_10y / 1e6).toFixed(1)} millones. ` +
                        `Al mes 120, la tasa ha declinado un ${declinePct}% respecto al inicio. ` +
                        `${prod.total_revenue_10y > 5e6 ? 'El pozo muestra potencial económico significativo.' : 'Se recomienda evaluar la economía con costos operativos detallados.'}`}
                    method="Modelo de declinación exponencial de Arps: q(t) = qi × exp(-D×t). OIP = 7758 × A × h × Φ × (1-Sw) / Boi. Precio asumido: $65/bbl. Área de drenaje: 40 acres. Boi = 1.2. Factor de recuperación implícito ~15-25% del OOIP. La tasa de declinación D = 0.05/año es representativa para reservorios convencionales."
                />
            </motion.div>
        </div>
    );
};
