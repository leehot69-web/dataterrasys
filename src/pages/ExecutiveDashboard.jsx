import React, { useState, useEffect } from 'react';
import {
    Zap, Activity, ShieldCheck, TrendingUp, Droplets,
    Database, Layers, BarChart3, Binary, LayoutGrid, Target, Waves,
    Thermometer, Globe, Box, AlertTriangle, FileText, PieChart,
    Hexagon, Menu, X, Info, ChevronRight, Maximize2, Map as MapIcon,
    Download, Share2, ArrowLeft
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Geology Modals
import { LithoCube3D, LithologySection, SeismicSection, WellTieModal } from '../components/GeologyModals';
import WellTrajectory3D from '../components/WellTrajectory3D'; // Nuevo Visor 3D Real
// Analytics Modals
import { HistogramModal, RadarModal, ScatterModal, BubbleExplorer } from '../components/AnalyticsModals';
import ProductionModal from '../components/NodalAnalysisModal'; // Aliased for compatibility

// Export Tools
import { ExportModal } from '../components/ExportTools';
import NodalAnalysisModal from '../components/NodalAnalysisModal';

const useIsMobile = () => {
    const [m, setM] = useState(false);
    useEffect(() => { const c = () => setM(window.innerWidth < 1024); c(); window.addEventListener('resize', c); return () => window.removeEventListener('resize', c); }, []);
    return m;
};

const StatCard = ({ label, value, unit, icon: Icon, color, isMobile }) => (
    <motion.div whileHover={!isMobile ? { y: -4, borderColor: color } : {}} style={{
        background: 'rgba(255,255,255,0.03)', padding: isMobile ? '14px' : '20px', borderRadius: '20px',
        border: '1px solid rgba(255,255,255,0.06)', transition: 'all 0.3s ease'
    }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ padding: '8px', background: `${color}15`, borderRadius: '10px' }}><Icon size={16} color={color} /></div>
        </div>
        <p style={{ fontSize: '9px', fontWeight: 900, opacity: 0.4, letterSpacing: '1.5px', textTransform: 'uppercase', margin: 0 }}>{label}</p>
        <h3 style={{ fontSize: isMobile ? '18px' : '22px', fontWeight: 900, margin: '4px 0 0 0', letterSpacing: '-0.5px' }}>
            {value} {unit && <span style={{ fontSize: '11px', opacity: 0.5, fontWeight: 600 }}>{unit}</span>}
        </h3>
    </motion.div>
);

// --- Launcher Card (abre modal) ---
const LauncherCard = ({ label, description, icon: Icon, color, onClick, available }) => (
    <motion.div whileHover={{ y: -4, borderColor: color, boxShadow: `0 8px 30px ${color}20` }}
        onClick={available ? onClick : undefined}
        style={{
            background: 'rgba(255,255,255,0.02)', padding: '25px', borderRadius: '25px',
            border: '1px solid rgba(255,255,255,0.06)', cursor: available ? 'pointer' : 'not-allowed',
            opacity: available ? 1 : 0.4, transition: 'all 0.3s ease', position: 'relative'
        }}>
        <div style={{ padding: '10px', background: `${color}12`, borderRadius: '14px', display: 'inline-block', marginBottom: '12px' }}>
            <Icon size={22} color={color} />
        </div>
        <h4 style={{ fontSize: '13px', fontWeight: 800, margin: '0 0 6px 0' }}>{label}</h4>
        <p style={{ fontSize: '10px', opacity: 0.4, margin: 0, lineHeight: '1.5' }}>{description}</p>
        {available && <Maximize2 size={14} color={color} style={{ position: 'absolute', top: '15px', right: '15px', opacity: 0.3 }} />}
        {!available && <span style={{ fontSize: '8px', color: '#fbbf24', position: 'absolute', top: '15px', right: '15px' }}>REQUIRES DATA</span>}
    </motion.div>
);

// ====================================================================
// PROFESSIONAL LOG TRACK COMPONENT
// ====================================================================
const normalize = (v, range, isLog) => {
    if (isLog) return Math.max(0, Math.min(1, Math.log10(Math.max(v, 0.001) + 1) / 4));
    if (range) return Math.max(0, Math.min(1, (v - range[0]) / (range[1] - range[0])));
    return 0.5;
};

const buildPolyline = (data, w, pixPerSample, range, isLog) => {
    if (!data || data.length === 0) return '';
    return data.map((v, i) => {
        const n = normalize(v, range, isLog);
        return `${n * w},${i * pixPerSample}`;
    }).join(' ');
};

const buildFillPolygon = (data, w, pixPerSample, range, isLog, side) => {
    if (!data || data.length === 0) return '';
    const pts = data.map((v, i) => {
        const n = normalize(v, range, isLog);
        return `${n * w},${i * pixPerSample}`;
    }).join(' ');
    const h = (data.length - 1) * pixPerSample;
    if (side === 'left') return `0,0 ${pts} 0,${h}`;
    return `${w},0 ${pts} ${w},${h}`;
};

// Individual curve header row
const CurveHeaderRow = ({ label, color, unit, rangeText, scaleType, style }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 6px', ...style }}>
        <span style={{ fontSize: '9px', fontWeight: 900, color, letterSpacing: '0.5px' }}>{label}</span>
        <span style={{ fontSize: '7px', color: '#555' }}>
            {unit} • {scaleType} • {rangeText}
        </span>
    </div>
);


const WaitingState = ({ message }) => (
    <div style={{ padding: '80px 30px', textAlign: 'center' }}>
        <Database size={50} color="#1a1a1a" style={{ marginBottom: '20px' }} />
        <h3 style={{ fontWeight: 900, opacity: 0.3, marginBottom: '10px' }}>SIN DATOS</h3>
        <p style={{ fontSize: '12px', opacity: 0.3 }}>{message}</p>
    </div>
);

// ======================================================================
// 1. EXECUTIVE VIEW
// ======================================================================
const ExecutiveView = ({ data, isMobile }) => {
    if (!data) return <WaitingState message="Cargue un archivo .LAS" />;
    const { well_info, kpis, audit, pay_zones } = data;
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4, 1fr)', gap: '12px' }}>
                <StatCard label="Well Name" value={well_info?.well_name || '-'} icon={Target} color="#00f2ff" isMobile={isMobile} />
                <StatCard label="Max Depth" value={kpis?.max_depth || 0} unit="FT" icon={Layers} color="#fb923c" isMobile={isMobile} />
                <StatCard label="Avg Porosity" value={`${kpis?.avg_phi || 0}%`} icon={Droplets} color="#4ade80" isMobile={isMobile} />
                <StatCard label="Avg Sw" value={`${kpis?.avg_sw || 0}%`} icon={Waves} color="#3b82f6" isMobile={isMobile} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4, 1fr)', gap: '12px' }}>
                <StatCard label="Avg Vsh" value={`${kpis?.avg_vsh || 0}%`} icon={Activity} color="#c084fc" isMobile={isMobile} />
                <StatCard label="Avg Perm" value={kpis?.avg_perm || 0} unit="mD" icon={Thermometer} color="#f472b6" isMobile={isMobile} />
                <StatCard label="Net Pay" value={kpis?.net_pay_ft || 0} unit="FT" icon={TrendingUp} color="#4ade80" isMobile={isMobile} />
                <StatCard label="Pay Zones" value={kpis?.num_pay_zones || 0} icon={BarChart3} color="#fbbf24" isMobile={isMobile} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '20px' }}>
                <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: '25px', border: '1px solid rgba(255,255,255,0.06)', padding: '25px' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: 900, marginBottom: '15px', color: '#00f2ff', letterSpacing: '1px' }}>WELL MASTER DATA</h3>
                    {[{ k: 'Well', v: well_info?.well_name }, { k: 'Field', v: well_info?.field }, { k: 'Operator', v: well_info?.operator },
                    { k: 'Service', v: well_info?.service }, { k: 'Location', v: well_info?.location }, { k: 'Date', v: well_info?.date }].map((item, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 12px', background: '#0a0a0a', borderRadius: '8px', border: '1px solid #151515', marginBottom: '5px' }}>
                            <span style={{ fontSize: '10px', fontWeight: 700, opacity: 0.4 }}>{item.k}</span>
                            <span style={{ fontSize: '10px', fontWeight: 800 }}>{item.v || '-'}</span>
                        </div>
                    ))}
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: '25px', border: '1px solid rgba(255,255,255,0.06)', padding: '25px' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: 900, marginBottom: '15px', color: '#00f2ff', letterSpacing: '1px' }}>DATA QUALITY AUDIT</h3>
                    {audit?.map((msg, i) => {
                        const bg = msg.includes('❌') ? 'rgba(239,68,68,0.08)' : msg.includes('⚠️') ? 'rgba(251,191,36,0.08)' : 'rgba(74,222,128,0.08)';
                        const bc = msg.includes('❌') ? 'rgba(239,68,68,0.2)' : msg.includes('⚠️') ? 'rgba(251,191,36,0.2)' : 'rgba(74,222,128,0.2)';
                        return <div key={i} style={{ padding: '8px 12px', background: bg, border: `1px solid ${bc}`, borderRadius: '10px', marginBottom: '5px' }}><p style={{ margin: 0, fontSize: '10px', lineHeight: '1.5' }}>{msg}</p></div>;
                    })}
                </div>
            </div>
            {pay_zones && pay_zones.length > 0 && (
                <div style={{ background: 'rgba(74,222,128,0.03)', borderRadius: '25px', border: '1px solid rgba(74,222,128,0.1)', padding: '25px', overflowX: 'auto' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: 900, marginBottom: '15px', color: '#4ade80' }}>PAY ZONES ({pay_zones.length})</h3>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                        <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            {['#', 'Top', 'Base', 'H(ft)', 'Avg Φ', 'Avg Sw', 'Quality'].map(h => <th key={h} style={{ padding: '8px', textAlign: 'left', fontWeight: 800, opacity: 0.5, fontSize: '9px' }}>{h}</th>)}
                        </tr></thead>
                        <tbody>{pay_zones.map((z, i) => {
                            const qc = z.Calidad === 'Excelente' ? '#4ade80' : z.Calidad === 'Bueno' ? '#fbbf24' : '#fb923c';
                            return (<tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                <td style={{ padding: '8px', fontWeight: 800 }}>{i + 1}</td>
                                <td style={{ padding: '8px' }}>{z.Top?.toFixed(1)}</td><td style={{ padding: '8px' }}>{z.Base?.toFixed(1)}</td>
                                <td style={{ padding: '8px', fontWeight: 700, color: '#00f2ff' }}>{z.Espesor_ft?.toFixed(1)}</td>
                                <td style={{ padding: '8px' }}>{(z.Porosidad_Avg * 100).toFixed(1)}%</td><td style={{ padding: '8px' }}>{(z.Sw_Avg * 100).toFixed(1)}%</td>
                                <td style={{ padding: '8px' }}><span style={{ padding: '3px 10px', background: `${qc}20`, color: qc, borderRadius: '20px', fontWeight: 800, fontSize: '9px' }}>{z.Calidad}</span></td>
                            </tr>);
                        })}</tbody>
                    </table>
                </div>
            )}
        </motion.div>
    );
};

// ======================================================================
// 2. GEOLOGY VIEW (Grid de launchers para modales)
// ======================================================================
const GeologyView = ({ data, isMobile, openModal }) => {
    if (!data) return <WaitingState message="Cargue un archivo .LAS para geología" />;
    const hasGeo = data.geophysics?.available;
    const has3D = data.scatter3d?.available_columns?.length > 0;
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '20px', width: '100%' }}>
            <LauncherCard label="3D Litho-Scanner Cube" description="PHI vs RHOB vs Depth coloreado por GR. Análisis volumétrico interactivo." icon={Box} color="#00f2ff" onClick={() => openModal('lithoCube')} available={has3D} />
            <LauncherCard label="Lithology Section" description="Sección estratigráfica con Vclay y Porosidad (smoothed fill)." icon={Layers} color="#22c55e" onClick={() => openModal('lithology')} available={!!data.curves?.vsh} />
            <LauncherCard label="Seismic 2D Section" description="Sección sísmica sintética generada desde RHOB/DT del pozo." icon={Waves} color="#f59e0b" onClick={() => openModal('seismic')} available={true} />
            <LauncherCard label="Well Trajectory 3D" description="Trayectoria del pozo con propiedades coloreadas por variable." icon={MapIcon} color="#a78bfa" onClick={() => openModal('trajectory')} available={true} />
            <LauncherCard label="Well Tie (Synthetic)" description="Impedancia → Reflectividad → Convolución Ricker → Sismograma." icon={Activity} color="#f472b6" onClick={() => openModal('wellTie')} available={hasGeo} />
            <LauncherCard label="Drilling Risk (DLS)" description="Análisis de severidad de pata de perro (DLS) y tortuosidad 3D." icon={AlertTriangle} color="#ef4444" onClick={() => openModal('drillingRisk')} available={true} />
            <LauncherCard label="4D Bubble Explorer" description="Visualización multidimensional: X, Y, Z + Tamaño variable." icon={Globe} color="#fb923c" onClick={() => openModal('bubble')} available={has3D} />
        </motion.div>
    );
};

// ======================================================================
// 3. PETROPHYSICS VIEW — Professional Multi-Track Log Viewer
// ======================================================================
const PX = 3; // pixels per sample (vertical resolution)
const TW = 140; // track width in pixels

// Helper: build SVG defs for lithology patterns
const LithoPatterns = () => (
    <defs>
        {/* Sand pattern — yellow dots */}
        <pattern id="pat-sand" width="6" height="6" patternUnits="userSpaceOnUse">
            <rect width="6" height="6" fill="#d4a017" opacity="0.55" />
            <circle cx="1.5" cy="1.5" r="0.8" fill="#8B7355" opacity="0.7" />
            <circle cx="4.5" cy="4.5" r="0.8" fill="#8B7355" opacity="0.7" />
        </pattern>
        {/* Shale pattern — gray horizontal lines */}
        <pattern id="pat-shale" width="8" height="4" patternUnits="userSpaceOnUse">
            <rect width="8" height="4" fill="#6b7280" opacity="0.5" />
            <line x1="0" y1="2" x2="8" y2="2" stroke="#374151" strokeWidth="0.8" />
        </pattern>
        {/* Water — blue */}
        <pattern id="pat-water" width="6" height="6" patternUnits="userSpaceOnUse">
            <rect width="6" height="6" fill="#3b82f6" opacity="0.35" />
        </pattern>
        {/* Oil — green */}
        <pattern id="pat-oil" width="6" height="6" patternUnits="userSpaceOnUse">
            <rect width="6" height="6" fill="#22c55e" opacity="0.45" />
        </pattern>
        {/* Tight / Matrix — dark cross-hatch */}
        <pattern id="pat-matrix" width="6" height="6" patternUnits="userSpaceOnUse">
            <rect width="6" height="6" fill="#1e293b" opacity="0.4" />
            <line x1="0" y1="0" x2="6" y2="6" stroke="#334155" strokeWidth="0.5" />
            <line x1="6" y1="0" x2="0" y2="6" stroke="#334155" strokeWidth="0.5" />
        </pattern>
    </defs>
);

// Track header — professional double-row header like Techlog
const TrackHeader = ({ curves, width, borderColor }) => (
    <div style={{
        width, flexShrink: 0, background: '#0a0f15',
        borderBottom: `2px solid ${borderColor || '#1e293b'}`,
        borderRight: '1px solid #1e293b',
    }}>
        {curves.map((c, i) => (
            <div key={i} style={{
                padding: '3px 6px',
                borderBottom: i < curves.length - 1 ? '1px solid #141a24' : 'none',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
                <span style={{ fontSize: '9px', fontWeight: 900, color: c.color, letterSpacing: '0.5px' }}>{c.label}</span>
                <span style={{ fontSize: '6.5px', color: '#555', fontWeight: 600 }}>
                    {c.unit} • {c.isLog ? 'LOG' : 'LIN'} • {c.rangeText}
                </span>
            </div>
        ))}
    </div>
);

// Single SVG track panel with multiple curves, fills, and grid
const TrackPanel = ({ curves, data, width, totalH, depthGridLines, pixPerSample }) => {
    const w = width || TW;
    return (
        <div style={{ width: w, flexShrink: 0, borderRight: '1px solid #1a1a1a', position: 'relative' }}>
            <svg width={w} height={totalH} viewBox={`0 0 ${w} ${totalH}`} preserveAspectRatio="none"
                style={{ display: 'block' }}>
                <LithoPatterns />
                {/* Horizontal grid lines */}
                {depthGridLines.map((y, gi) => (
                    <line key={gi} x1="0" y1={y} x2={w} y2={y} stroke="#1a1e2a" strokeWidth="0.5" />
                ))}
                {/* Vertical center guide */}
                <line x1={w / 2} y1="0" x2={w / 2} y2={totalH} stroke="#111827" strokeWidth="0.3" strokeDasharray="4,4" />
                {/* Render fills first (behind) */}
                {curves.map((c, ci) => {
                    if (!c.fill || !data[c.key]) return null;
                    const fillPts = buildFillPolygon(data[c.key], w, pixPerSample, c.range, c.isLog, c.fill);
                    if (!fillPts) return null;
                    const pat = c.fillPattern ? `url(#${c.fillPattern})` : c.fillColor;
                    return <polygon key={`fill-${ci}`} points={fillPts} fill={pat} opacity={c.fillOpacity || 0.2} />;
                })}
                {/* Render curve lines (on top) */}
                {curves.map((c, ci) => {
                    if (!data[c.key]) return null;
                    const pts = buildPolyline(data[c.key], w, pixPerSample, c.range, c.isLog);
                    if (!pts) return null;
                    return (
                        <polyline key={`line-${ci}`} fill="none" stroke={c.color}
                            strokeWidth={c.strokeWidth || 1.5} points={pts}
                            strokeDasharray={c.dashed ? '4,3' : 'none'} />
                    );
                })}
            </svg>
        </div>
    );
};

const PetrophysicsView = ({ data, isMobile }) => {
    if (!data) return <WaitingState message="Cargue un .LAS" />;
    const { curves, depths, kpis } = data;
    const nSamples = depths?.length || 0;
    const totalH = nSamples * PX;
    const tw = isMobile ? 110 : TW;

    // Depth grid lines (every ~50 samples)
    const gridInterval = Math.max(20, Math.round(nSamples / 40));
    const depthGridLines = [];
    for (let i = gridInterval; i < nSamples; i += gridInterval) {
        depthGridLines.push(i * PX);
    }

    // Depth ticks for the depth column
    const tickInterval = Math.max(1, Math.round(nSamples / 30));
    const depthTicks = [];
    if (depths) {
        for (let i = 0; i < nSamples; i += tickInterval) {
            depthTicks.push({ idx: i, depth: depths[i] });
        }
    }

    // Define professional track groups — each group renders in one SVG panel
    const trackGroups = [
        {
            id: 'gr', borderColor: '#4ade80',
            headers: [
                { label: 'GR', color: '#4ade80', unit: 'API', rangeText: '0 — 150' },
            ],
            curves: [
                { key: 'gr', color: '#4ade80', range: [0, 150], fill: 'left', fillColor: '#fbbf24', fillOpacity: 0.15 },
            ],
        },
        {
            id: 'rt', borderColor: '#fb923c',
            headers: [
                { label: 'RT', color: '#fb923c', unit: 'Ω·m', rangeText: '0.2 — 2000', isLog: true },
            ],
            curves: [
                { key: 'rt', color: '#fb923c', isLog: true },
            ],
        },
        {
            id: 'nphi-rhob', borderColor: '#38bdf8',
            headers: [
                { label: 'NPHI', color: '#38bdf8', unit: 'v/v', rangeText: '0.45 — -0.05' },
                { label: 'RHOB', color: '#ef4444', unit: 'g/cc', rangeText: '1.95 — 2.95' },
            ],
            curves: [
                { key: 'nphi', color: '#38bdf8', range: [0.45, -0.05], strokeWidth: 1.8 },
                { key: 'rhob', color: '#ef4444', range: [1.95, 2.95], dashed: true, strokeWidth: 1.5 },
            ],
        },
        {
            id: 'dt', borderColor: '#a78bfa', optional: true,
            headers: [
                { label: 'DT', color: '#a78bfa', unit: 'μs/ft', rangeText: '140 — 40' },
            ],
            curves: [
                { key: 'dt', color: '#a78bfa', range: [140, 40], fill: 'right', fillColor: '#a78bfa', fillOpacity: 0.08 },
            ],
        },
        {
            id: 'vsh-phi', borderColor: '#fbbf24',
            headers: [
                { label: 'VSH', color: '#fbbf24', unit: 'frac', rangeText: '0 — 1' },
                { label: 'PHI', color: '#22d3ee', unit: 'frac', rangeText: '0 — 0.4' },
            ],
            curves: [
                { key: 'vsh', color: '#fbbf24', range: [0, 1], fill: 'left', fillPattern: 'pat-shale', fillOpacity: 0.5 },
                { key: 'phi', color: '#22d3ee', range: [0, 0.4], strokeWidth: 2 },
            ],
        },
        {
            id: 'sw-sh', borderColor: '#3b82f6',
            headers: [
                { label: 'SW', color: '#3b82f6', unit: 'frac', rangeText: '0 — 1' },
                { label: 'SH', color: '#10b981', unit: 'frac', rangeText: '0 — 1' },
            ],
            curves: [
                { key: 'sw', color: '#3b82f6', range: [0, 1], fill: 'left', fillPattern: 'pat-water', fillOpacity: 0.6 },
                { key: 'sh', color: '#10b981', range: [0, 1], fill: 'left', fillPattern: 'pat-oil', fillOpacity: 0.5 },
            ],
        },
        {
            id: 'perm', borderColor: '#f472b6',
            headers: [
                { label: 'K', color: '#f472b6', unit: 'mD', rangeText: '0.01 — 10⁴', isLog: true },
            ],
            curves: [
                { key: 'perm', color: '#f472b6', isLog: true, fill: 'left', fillColor: '#f472b6', fillOpacity: 0.1 },
            ],
        },
        {
            id: 'litho', borderColor: '#d4a017', isLitho: true,
            headers: [
                { label: 'LITOLOGÍA', color: '#d4a017', unit: '', rangeText: 'Fracciones' },
            ],
        },
    ];

    // Filter groups to only include those with data
    const activeGroups = trackGroups.filter(g => {
        if (g.isLitho) return curves.vsh && curves.phi; // need VSH and PHI for lithology
        return g.curves.some(c => curves[c.key] && curves[c.key].length > 0);
    });

    // Build lithology column: fraction rects based on VSH, PHI, SH
    const buildLithoColumn = () => {
        if (!curves.vsh || !curves.phi) return null;
        const vsh = curves.vsh;
        const phi = curves.phi;
        const sh = curves.sh || vsh.map(() => 0);
        const sw = curves.sw || vsh.map(() => 1);
        const rects = [];
        const blockSize = Math.max(1, Math.floor(nSamples / 200)); // group samples for performance

        for (let i = 0; i < nSamples; i += blockSize) {
            // Average values over the block
            let sumVsh = 0, sumPhi = 0, sumSh = 0, sumSw = 0, count = 0;
            for (let j = i; j < Math.min(i + blockSize, nSamples); j++) {
                sumVsh += (vsh[j] || 0);
                sumPhi += (phi[j] || 0);
                sumSh += (sh[j] || 0);
                sumSw += (sw[j] || 0);
                count++;
            }
            const avgVsh = Math.min(1, Math.max(0, sumVsh / count));
            const avgPhi = Math.min(0.4, Math.max(0, sumPhi / count));
            const avgSh = Math.min(1, Math.max(0, sumSh / count));
            const avgSw = Math.min(1, Math.max(0, sumSw / count));

            const y = i * PX;
            const h = blockSize * PX;
            const w = tw;

            // Fractions: Matrix (1 - Vsh - Phi), Shale (Vsh), Porosity Water (Phi*Sw), Porosity HC (Phi*Sh)
            const fShale = avgVsh;
            const fPorWater = avgPhi * avgSw;
            const fPorHC = avgPhi * avgSh;
            const fSand = Math.max(0, 1 - fShale - avgPhi);

            // Draw stacked bars left-to-right
            let x = 0;
            // Sand (clean matrix)
            if (fSand > 0.01) {
                rects.push(<rect key={`s-${i}`} x={x} y={y} width={fSand * w} height={h} fill="url(#pat-sand)" />);
                x += fSand * w;
            }
            // Shale
            if (fShale > 0.01) {
                rects.push(<rect key={`sh-${i}`} x={x} y={y} width={fShale * w} height={h} fill="url(#pat-shale)" />);
                x += fShale * w;
            }
            // Porosity — Water
            if (fPorWater > 0.005) {
                rects.push(<rect key={`pw-${i}`} x={x} y={y} width={fPorWater * w} height={h} fill="url(#pat-water)" />);
                x += fPorWater * w;
            }
            // Porosity — HC
            if (fPorHC > 0.005) {
                rects.push(<rect key={`ph-${i}`} x={x} y={y} width={fPorHC * w} height={h} fill="url(#pat-oil)" />);
            }
        }
        return rects;
    };

    // Count available curves
    const availableCurveCount = activeGroups.reduce((sum, g) => sum + (g.curves?.length || 0), 0);

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%' }}>
            {/* KPIs */}
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(5, 1fr)', gap: '12px' }}>
                <StatCard label="Avg GR" value={kpis?.avg_gr ?? '-'} unit="API" icon={Activity} color="#4ade80" isMobile={isMobile} />
                <StatCard label="Avg Phi" value={`${kpis?.avg_phi ?? 0}%`} icon={Droplets} color="#22d3ee" isMobile={isMobile} />
                <StatCard label="Avg Vsh" value={`${kpis?.avg_vsh ?? 0}%`} icon={Layers} color="#fbbf24" isMobile={isMobile} />
                <StatCard label="Avg Sw" value={`${kpis?.avg_sw ?? 0}%`} icon={Waves} color="#3b82f6" isMobile={isMobile} />
                <StatCard label="Net Pay" value={kpis?.net_pay_ft ?? 0} unit="FT" icon={TrendingUp} color="#4ade80" isMobile={isMobile} />
            </div>

            {/* Track info bar */}
            <div style={{ background: 'rgba(0,242,255,0.03)', borderRadius: '16px', border: '1px solid rgba(0,242,255,0.08)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                <Info size={14} color="#00f2ff" style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '10px', opacity: 0.6 }}>
                    <strong>{availableCurveCount} curvas</strong> en {activeGroups.length} tracks •
                    {depths ? ` ${nSamples} muestras` : ''} •
                    {depths ? ` Prof: ${depths[0]?.toFixed(0)} — ${depths[nSamples - 1]?.toFixed(0)} ft` : ''} •
                    Fuente PHI: <strong>{data.analysis_meta?.phi_source || 'Calculada'}</strong>
                </span>
            </div>

            {/* ============= PROFESSIONAL LOG VIEWER ============= */}
            <div style={{
                background: '#060a10', borderRadius: '20px', border: '1px solid #1e293b',
                overflow: 'hidden', boxShadow: '0 4px 30px rgba(0,0,0,0.5)',
            }}>
                {/* ---- HEADERS ROW ---- */}
                <div style={{ display: 'flex', borderBottom: '2px solid #1e293b' }}>
                    {/* Depth header */}
                    <div style={{
                        width: '62px', flexShrink: 0, background: '#0a0f15',
                        borderRight: '2px solid #00f2ff33',
                        padding: '6px', textAlign: 'center',
                        display: 'flex', flexDirection: 'column', justifyContent: 'center',
                    }}>
                        <div style={{ fontSize: '9px', fontWeight: 900, color: '#00f2ff', letterSpacing: '1px' }}>DEPTH</div>
                        <div style={{ fontSize: '6.5px', color: '#555', marginTop: '2px' }}>FT (MD)</div>
                    </div>
                    {/* Track headers */}
                    {activeGroups.map(g => (
                        g.isLitho ? (
                            <div key={g.id} style={{
                                width: tw, flexShrink: 0, background: '#0a0f15',
                                borderRight: '1px solid #1e293b', borderBottom: `2px solid ${g.borderColor}`,
                                padding: '6px', textAlign: 'center',
                                display: 'flex', flexDirection: 'column', justifyContent: 'center',
                            }}>
                                <div style={{ fontSize: '9px', fontWeight: 900, color: g.borderColor, letterSpacing: '0.5px' }}>LITOLOGÍA</div>
                                <div style={{ fontSize: '6.5px', color: '#555', marginTop: '2px' }}>Arena • Arcilla • Agua • HC</div>
                            </div>
                        ) : (
                            <TrackHeader key={g.id} curves={g.headers} width={tw} borderColor={g.borderColor} />
                        )
                    ))}
                </div>

                {/* ---- SCROLLABLE LOG AREA ---- */}
                <div style={{ maxHeight: isMobile ? '500px' : '700px', overflow: 'auto', display: 'flex' }}>
                    {/* Depth column */}
                    <div style={{
                        width: '62px', flexShrink: 0, background: '#0a0f15',
                        borderRight: '2px solid #00f2ff22', position: 'sticky', left: 0, zIndex: 2,
                    }}>
                        <div style={{ height: totalH, position: 'relative' }}>
                            {depthTicks.map((t, i) => (
                                <div key={i} style={{
                                    position: 'absolute', top: t.idx * PX, left: 0, right: 0,
                                    display: 'flex', alignItems: 'center', height: '1px',
                                }}>
                                    <div style={{ flex: 1, height: '1px', background: '#1e293b' }} />
                                    <span style={{
                                        fontSize: '7px', fontWeight: 700, color: '#94a3b8',
                                        padding: '1px 3px', background: '#0a0f15', whiteSpace: 'nowrap',
                                    }}>{t.depth?.toFixed(0)}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Track panels */}
                    {activeGroups.map(g => {
                        if (g.isLitho) {
                            // Lithology column
                            return (
                                <div key={g.id} style={{ width: tw, flexShrink: 0, borderRight: '1px solid #1a1a1a' }}>
                                    <svg width={tw} height={totalH} viewBox={`0 0 ${tw} ${totalH}`}
                                        preserveAspectRatio="none" style={{ display: 'block' }}>
                                        <LithoPatterns />
                                        {depthGridLines.map((y, gi) => (
                                            <line key={gi} x1="0" y1={y} x2={tw} y2={y} stroke="#1a1e2a" strokeWidth="0.5" />
                                        ))}
                                        {buildLithoColumn()}
                                    </svg>
                                </div>
                            );
                        }
                        return (
                            <TrackPanel
                                key={g.id}
                                curves={g.curves}
                                data={curves}
                                width={tw}
                                totalH={totalH}
                                depthGridLines={depthGridLines}
                                pixPerSample={PX}
                            />
                        );
                    })}
                </div>
            </div>

            {/* ============= LEGEND ============= */}
            <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.06)', padding: '25px' }}>
                <h3 style={{ fontSize: '11px', fontWeight: 900, marginBottom: '15px', color: '#00f2ff', letterSpacing: '1.5px' }}>
                    LEYENDA DE REGISTROS — {availableCurveCount} CURVAS ACTIVAS
                </h3>
                {/* Curve legend */}
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '8px', marginBottom: '20px' }}>
                    {activeGroups.filter(g => !g.isLitho).flatMap(g => g.curves.map(c => {
                        const hdr = g.headers.find(h => h.label === c.label || (g.headers.length === 1 && true)) || g.headers[0];
                        return { ...c, unit: hdr?.unit || '', desc: hdr?.rangeText || '' };
                    })).map((c, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 12px', background: '#0a0a0a', borderRadius: '12px', border: '1px solid #151515' }}>
                            <div style={{
                                width: '24px', height: '3px', borderRadius: '2px', background: c.color,
                                flexShrink: 0, borderTop: c.dashed ? '2px dashed' + c.color : 'none',
                            }} />
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{ fontSize: '11px', fontWeight: 900, color: c.color }}>{c.label || c.key.toUpperCase()}</span>
                                    <span style={{ fontSize: '8px', fontWeight: 700, color: '#555', background: '#1a1a1a', padding: '1px 6px', borderRadius: '10px' }}>{c.unit}</span>
                                    <span style={{ fontSize: '7px', fontWeight: 600, color: '#444' }}>{c.isLog ? 'LOG' : 'LIN'}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                {/* Lithology pattern legend */}
                <h4 style={{ fontSize: '10px', fontWeight: 900, color: '#d4a017', letterSpacing: '1px', marginBottom: '10px' }}>
                    PATRONES LITOLÓGICOS — COLUMNA DE EVALUACIÓN DE FORMACIÓN
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(5, 1fr)', gap: '8px' }}>
                    {[
                        { label: 'Arena (Cuarzo)', colors: ['#d4a017', '#8B7355'], desc: 'Matriz limpia (1-Vsh-Φ)' },
                        { label: 'Arcilla (Shale)', colors: ['#6b7280', '#374151'], desc: 'Vsh (GR Linear Index)' },
                        { label: 'Agua (Porosidad)', colors: ['#3b82f6'], desc: 'Φ × Sw (Archie)' },
                        { label: 'Hidrocarburo', colors: ['#22c55e'], desc: 'Φ × (1-Sw)' },
                        { label: 'Matriz Densa', colors: ['#1e293b', '#334155'], desc: 'Baja Φ, baja Vsh' },
                    ].map((m, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', background: '#0a0a0a', borderRadius: '10px', border: '1px solid #151515' }}>
                            <div style={{
                                width: '20px', height: '20px', borderRadius: '4px', flexShrink: 0,
                                background: m.colors.length > 1
                                    ? `repeating-linear-gradient(45deg, ${m.colors[0]}, ${m.colors[0]} 3px, ${m.colors[1]} 3px, ${m.colors[1]} 6px)`
                                    : m.colors[0],
                                opacity: 0.7,
                            }} />
                            <div>
                                <div style={{ fontSize: '9px', fontWeight: 800, color: m.colors[0] }}>{m.label}</div>
                                <div style={{ fontSize: '7px', color: '#555' }}>{m.desc}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>
    );
};

// ======================================================================
// 4. ANALYTICS VIEW (Grid de launchers para modales)
// ======================================================================
const AnalyticsView = ({ data, isMobile, openModal }) => {
    if (!data) return <WaitingState message="Cargue un .LAS" />;
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '20px', width: '100%' }}>
            <LauncherCard label="Distribution Analysis" description="Histogramas de distribución por curva (GR, PHI, Sw...)." icon={BarChart3} color="#00f2ff" onClick={() => openModal('histogram')} available={!!data.histograms && Object.keys(data.histograms).length > 0} />
            <LauncherCard label="Rock Quality Radar" description="RQI: Porosidad, Saturación, Limpieza, Potencial Económico." icon={PieChart} color="#4ade80" onClick={() => openModal('radar')} available={!!data.radar} />
            <LauncherCard label="Cross-Correlation Scatter" description="Correlaciones cruzadas con Pearson R y mapa de color." icon={Activity} color="#f59e0b" onClick={() => openModal('scatter')} available={!!data.correlations?.pairs} />
            <LauncherCard label="Nodal Analysis Simulator" description="Simulador de producción dinámico (Vogel IPR + VLP)." icon={TrendingUp} color="#f472b6" onClick={() => openModal('production')} available={true} />
            <LauncherCard label="4D Bubble Explorer" description="Visualización 3D multidimensional con tamaño y color variable." icon={Globe} color="#fb923c" onClick={() => openModal('bubble')} available={!!data.scatter3d} />
            <LauncherCard label="Data QC Audit" description="Auditoría SEG: curvas, rangos físicos, integridad de muestreo." icon={ShieldCheck} color="#64748b" onClick={() => openModal('dataQC')} available={!!data.audit} />
            <LauncherCard label="Electrofacies (PCA + K-Means)" description="Clasificación automática de litofacies: Arena, Lutita, Carbonato." icon={LayoutGrid} color="#c084fc" onClick={() => openModal('electrofacies')} available={!!data.electrofacies?.distribution} />
            <LauncherCard label="PCA — Componentes Principales" description="Reducción dimensional: varianza explicada, loadings y scatter." icon={Binary} color="#818cf8" onClick={() => openModal('pcaAnalysis')} available={!!data.pca_analysis?.available} />
            <LauncherCard label="Permeabilidad Comparativa" description="Timur-Coates vs Log-Linear vs Morris-Biggs — 3 modelos." icon={Droplets} color="#2dd4bf" onClick={() => openModal('permComparison')} available={!!data.perm_comparison} />
            <LauncherCard label="Producción & OOIP" description="Arps (Exp + Hyp), OOIP completo y simulación a 10 años." icon={Target} color="#fb923c" onClick={() => openModal('productionOOIP')} available={!!data.production?.ooip_breakdown} />
            <LauncherCard label="Unit Standardization Log" description="Registro de conversiones automáticas: NPHI, RHOB, DT." icon={FileText} color="#a3e635" onClick={() => openModal('unitConversions')} available={!!data.unit_conversions && data.unit_conversions.length > 0} />
        </motion.div>
    );
};

// ======================================================================
// DATA QC VIEW MODAL
// ======================================================================
const DataQCModal = ({ data, onClose }) => {
    if (!data) return null;
    const { audit, available_curves, analysis_meta } = data;
    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '1000px', maxHeight: '90vh', overflow: 'auto', padding: '30px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '15px', right: '15px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>
                <h2 style={{ fontSize: '16px', fontWeight: 900, color: '#00f2ff', marginBottom: '20px' }}>DATA QUALITY CONTROL</h2>
                <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ fontSize: '11px', fontWeight: 800, opacity: 0.5, marginBottom: '10px' }}>CURVES LOADED ({available_curves?.length})</h4>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {available_curves?.map((c, i) => <span key={i} style={{ padding: '5px 12px', background: 'rgba(0,242,255,0.08)', border: '1px solid rgba(0,242,255,0.15)', borderRadius: '20px', fontSize: '10px', fontWeight: 700, color: '#00f2ff' }}>{c}</span>)}
                    </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '20px' }}>
                    {[{ k: 'Phi Source', v: analysis_meta?.phi_source }, { k: 'Vsh', v: analysis_meta?.vsh_available ? '✅' : '❌' },
                    { k: 'Sw Archie', v: analysis_meta?.sw_available ? '✅' : '❌' }, { k: 'Sw Simandoux', v: analysis_meta?.sw_simandoux_available ? '✅' : '❌' }].map((it, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#111', borderRadius: '10px' }}>
                            <span style={{ fontSize: '10px', opacity: 0.4 }}>{it.k}</span><span style={{ fontSize: '10px', fontWeight: 800 }}>{it.v || '-'}</span>
                        </div>
                    ))}
                </div>
                {audit?.map((msg, i) => {
                    const bg = msg.includes('❌') ? 'rgba(239,68,68,0.08)' : msg.includes('⚠️') ? 'rgba(251,191,36,0.08)' : 'rgba(74,222,128,0.08)';
                    return <div key={i} style={{ padding: '10px 12px', background: bg, borderRadius: '10px', marginBottom: '6px' }}><p style={{ margin: 0, fontSize: '10px', lineHeight: '1.6' }}>{msg}</p></div>;
                })}
            </motion.div>
        </div>
    );
};

// ======================================================================
// DRILLING RISK MODAL (DLS Analysis)
// ======================================================================
const DrillingRiskModal = ({ data, onClose }) => {
    const dls = data?.dls_analysis || [];
    const severityColors = { 'Bajo': '#22c55e', 'Medio': '#fbbf24', 'Alto': '#f97316', 'Crítico': '#ef4444' };

    // Stats
    const maxDLS = dls.length > 0 ? Math.max(...dls.map(d => d.dls)) : 0;
    const avgDLS = dls.length > 0 ? (dls.reduce((s, d) => s + d.dls, 0) / dls.length) : 0;
    const criticalCount = dls.filter(d => d.severity === 'Crítico').length;

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '900px', maxHeight: '85vh', overflow: 'auto', padding: '40px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

                <h2 style={{ fontSize: '22px', fontWeight: 900, color: '#ef4444', marginBottom: '8px' }}>⚠️ Drilling Risk Analysis (DLS)</h2>
                <p style={{ color: '#888', fontSize: '12px', marginBottom: '25px' }}>Dog-Leg Severity — Severidad de Pata de Perro (°/100ft)</p>

                {/* KPIs */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px', marginBottom: '25px' }}>
                    <div style={{ background: '#111', borderRadius: '16px', padding: '18px', border: '1px solid #222', textAlign: 'center' }}>
                        <p style={{ fontSize: '10px', color: '#888', margin: 0 }}>MAX DLS</p>
                        <p style={{ fontSize: '24px', fontWeight: 900, color: maxDLS > 10 ? '#ef4444' : '#22c55e', margin: '5px 0 0' }}>{maxDLS.toFixed(1)}°</p>
                    </div>
                    <div style={{ background: '#111', borderRadius: '16px', padding: '18px', border: '1px solid #222', textAlign: 'center' }}>
                        <p style={{ fontSize: '10px', color: '#888', margin: 0 }}>AVG DLS</p>
                        <p style={{ fontSize: '24px', fontWeight: 900, color: '#fbbf24', margin: '5px 0 0' }}>{avgDLS.toFixed(1)}°</p>
                    </div>
                    <div style={{ background: '#111', borderRadius: '16px', padding: '18px', border: '1px solid #222', textAlign: 'center' }}>
                        <p style={{ fontSize: '10px', color: '#888', margin: 0 }}>PUNTOS CRÍTICOS</p>
                        <p style={{ fontSize: '24px', fontWeight: 900, color: criticalCount > 0 ? '#ef4444' : '#22c55e', margin: '5px 0 0' }}>{criticalCount}</p>
                    </div>
                </div>

                {/* Table */}
                {dls.length === 0 ? (
                    <p style={{ color: '#666', textAlign: 'center', padding: '40px' }}>No se detectaron puntos de riesgo significativo. El pozo tiene una trayectoria suave.</p>
                ) : (
                    <div style={{ maxHeight: '350px', overflow: 'auto', borderRadius: '12px', border: '1px solid #222' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                            <thead>
                                <tr style={{ background: '#111', position: 'sticky', top: 0 }}>
                                    <th style={{ padding: '10px 14px', textAlign: 'left', color: '#888', fontWeight: 600 }}>Profundidad</th>
                                    <th style={{ padding: '10px 14px', textAlign: 'center', color: '#888', fontWeight: 600 }}>DLS (°/100ft)</th>
                                    <th style={{ padding: '10px 14px', textAlign: 'center', color: '#888', fontWeight: 600 }}>Inclinación</th>
                                    <th style={{ padding: '10px 14px', textAlign: 'center', color: '#888', fontWeight: 600 }}>Azimuth</th>
                                    <th style={{ padding: '10px 14px', textAlign: 'center', color: '#888', fontWeight: 600 }}>Severidad</th>
                                </tr>
                            </thead>
                            <tbody>
                                {dls.map((d, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid #1a1a1a' }}>
                                        <td style={{ padding: '8px 14px', color: '#ccc' }}>{d.depth.toFixed(1)} ft</td>
                                        <td style={{ padding: '8px 14px', textAlign: 'center', fontWeight: 700, color: severityColors[d.severity] || '#ccc' }}>{d.dls}</td>
                                        <td style={{ padding: '8px 14px', textAlign: 'center', color: '#aaa' }}>{d.inclination}°</td>
                                        <td style={{ padding: '8px 14px', textAlign: 'center', color: '#aaa' }}>{d.azimuth}°</td>
                                        <td style={{ padding: '8px 14px', textAlign: 'center' }}>
                                            <span style={{ padding: '3px 10px', borderRadius: '8px', fontSize: '10px', fontWeight: 700, background: `${severityColors[d.severity]}22`, color: severityColors[d.severity] }}>{d.severity}</span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </motion.div>
        </div>
    );
};

// ======================================================================
// 1. UNIT CONVERSIONS MODAL
// ======================================================================
const UnitConversionsModal = ({ data, onClose }) => {
    const conversions = data?.unit_conversions || [];
    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '600px', padding: '30px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <FileText size={24} color="#a3e635" />
                    <h2 style={{ fontSize: '20px', fontWeight: 900, color: '#fff', margin: 0 }}>Estandarización de Unidades</h2>
                </div>
                <p style={{ color: '#888', fontSize: '12px', marginBottom: '25px', marginLeft: '34px' }}>Registro de conversiones automáticas realizadas al cargar el .LAS</p>

                {conversions.length === 0 ? (
                    <div style={{ padding: '30px', textAlign: 'center', border: '1px dashed #333', borderRadius: '12px', color: '#666' }}>
                        No se requirieron conversiones. Todas las curvas están en unidades estándar estándar.
                    </div>
                ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid #333', color: '#888', textAlign: 'left' }}>
                                <th style={{ padding: '10px' }}>Curva</th>
                                <th style={{ padding: '10px' }}>Unidad Original</th>
                                <th style={{ padding: '10px' }}>Unidad Final</th>
                                <th style={{ padding: '10px' }}>Factor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {conversions.map((c, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid #1a1a1a' }}>
                                    <td style={{ padding: '12px', fontWeight: 700, color: '#fff' }}>{c.curve}</td>
                                    <td style={{ padding: '12px', color: '#fbbf24' }}>{c.from}</td>
                                    <td style={{ padding: '12px', color: '#4ade80', fontWeight: 700 }}>{c.to}</td>
                                    <td style={{ padding: '12px', color: '#888', fontFamily: 'monospace' }}>{c.factor}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </motion.div>
        </div>
    );
};

// ======================================================================
// 2. ELECTROFACIES MODAL (PCA + K-MEANS)
// ======================================================================
const ElectrofaciesModal = ({ data, onClose }) => {
    const ef = data?.electrofacies || {};
    const dist = ef.distribution || {};
    const total = ef.total_classified || 1;

    // Convertir distribución a array ordenado
    const categories = Object.entries(dist).sort((a, b) => b[1] - a[1]);

    const faciesColors = {
        'Arena Limpia': '#fbbf24',    // Amarillo
        'Arena Arcillosa': '#a3e635', // Verde claro
        'Lutita': '#22c55e',          // Verde oscuro
        'Carbonato/Tight': '#3b82f6', // Azul
    };

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '800px', maxHeight: '90vh', overflow: 'auto', padding: '30px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <LayoutGrid size={24} color="#c084fc" />
                    <h2 style={{ fontSize: '20px', fontWeight: 900, color: '#fff', margin: 0 }}>Electrofacies Classification</h2>
                </div>
                <p style={{ color: '#888', fontSize: '12px', marginBottom: '30px', marginLeft: '34px' }}>
                    Clasificación supervisada usando <strong>PCA + K-Means ({ef.n_clusters} clusters)</strong>.
                    Curvas usadas: {ef.curves_used?.join(', ')}.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', alignItems: 'start' }}>
                    {/* Gráfico de Barras */}
                    <div>
                        <h4 style={{ fontSize: '12px', color: '#666', borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '15px' }}>DISTRIBUCIÓN DE LITOLOGÍA</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                            {categories.map(([facies, count], i) => (
                                <div key={i}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '12px' }}>
                                        <span style={{ fontWeight: 700, color: faciesColors[facies] || '#ccc' }}>{facies}</span>
                                        <span style={{ color: '#666' }}>{count} pts ({Math.round(count / total * 100)}%)</span>
                                    </div>
                                    <div style={{ width: '100%', height: '8px', background: '#222', borderRadius: '4px', overflow: 'hidden' }}>
                                        <motion.div initial={{ width: 0 }} animate={{ width: `${(count / total) * 100}%` }}
                                            style={{ height: '100%', background: faciesColors[facies] || '#ccc', borderRadius: '4px' }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Stats Box */}
                    <div style={{ background: '#111', borderRadius: '16px', padding: '20px', border: '1px solid #222' }}>
                        <h4 style={{ fontSize: '12px', color: '#888', marginBottom: '15px' }}>RESUMEN DE RESERVORIO</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(251,191,36,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Layers size={20} color="#fbbf24" />
                                </div>
                                <div>
                                    <div style={{ fontSize: '10px', color: '#666' }}>NET SAND</div>
                                    <div style={{ fontSize: '18px', fontWeight: 900, color: '#fff' }}>
                                        {Math.round(((dist['Arena Limpia'] || 0) + (dist['Arena Arcillosa'] || 0)) / total * 100)}%
                                    </div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(34,197,94,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Box size={20} color="#22c55e" />
                                </div>
                                <div>
                                    <div style={{ fontSize: '10px', color: '#666' }}>SHALE VOLUME</div>
                                    <div style={{ fontSize: '18px', fontWeight: 900, color: '#fff' }}>
                                        {Math.round((dist['Lutita'] || 0) / total * 100)}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style={{ marginTop: '20px', paddingTop: '15px', borderTop: '1px solid #333', fontSize: '11px', color: '#666' }}>
                            *La clasificación se basa en centroides estadísticos. Puede requerir calibración con núcleos.
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

// ======================================================================
// 3. PCA ANALYSIS MODAL
// ======================================================================
const PCAAnalysisModal = ({ data, onClose }) => {
    const pca = data?.pca_analysis || {};
    if (!pca.available) return null;

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '900px', maxHeight: '90vh', overflow: 'auto', padding: '30px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <Binary size={24} color="#818cf8" />
                    <h2 style={{ fontSize: '20px', fontWeight: 900, color: '#fff', margin: 0 }}>Principal Component Analysis</h2>
                </div>
                <p style={{ color: '#888', fontSize: '12px', marginBottom: '30px', marginLeft: '34px' }}>
                    Reducción de dimensionalidad para identificar drivers principales de varianza.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '30px' }}>
                    {/* Variance Chart - Simple Bar */}
                    <div>
                        <h4 style={{ fontSize: '12px', color: '#818cf8', marginBottom: '15px' }}>VARIANZA EXPLICADA</h4>
                        <div style={{ display: 'flex', alignItems: 'flex-end', height: '150px', gap: '20px', paddingBottom: '20px', borderBottom: '1px solid #333' }}>
                            {pca.variance_explained?.map((v, i) => (
                                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', alignItems: 'center' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 800, color: '#fff', marginBottom: '5px' }}>{v}%</div>
                                    <motion.div initial={{ height: 0 }} animate={{ height: `${v * 2}px` }} style={{ width: '40px', background: '#818cf8', borderRadius: '4px 4px 0 0', opacity: 1 - (i * 0.2) }} />
                                    <div style={{ fontSize: '10px', color: '#666', marginTop: '8px' }}>PC{i + 1}</div>
                                </div>
                            ))}
                        </div>
                        <p style={{ fontSize: '11px', color: '#666', marginTop: '10px', textAlign: 'center' }}>
                            Varianza Acumulada: <strong style={{ color: '#818cf8' }}>{pca.cumulative_variance}%</strong>
                        </p>
                    </div>

                    {/* Loadings Table */}
                    <div>
                        <h4 style={{ fontSize: '12px', color: '#666', marginBottom: '15px' }}>COMPONENT LOADINGS (Dominancia)</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {Object.entries(pca.loadings || {}).map(([pc, data], i) => (
                                <div key={i} style={{ padding: '12px', borderRadius: '12px', background: '#111', border: '1px solid #222' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                        <span style={{ fontSize: '11px', fontWeight: 800, color: '#818cf8' }}>{pc}</span>
                                        <span style={{ fontSize: '11px', color: '#ccc' }}>Dominante: <strong>{data.dominant_curve}</strong></span>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                        {Object.entries(data.weights).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 3).map(([curve, w], j) => (
                                            <span key={j} style={{ fontSize: '9px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', color: w > 0 ? '#4ade80' : '#ef4444' }}>
                                                {curve} {w > 0 ? '+' : ''}{w}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 2D Scatter if available */}
                {pca.pc1 && pca.pc1.length > 0 && (
                    <div style={{ marginTop: '30px', height: '200px', background: '#0e0e0e', borderRadius: '16px', border: '1px solid #222', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                        <Activity size={32} color="#333" />
                        <p style={{ fontSize: '11px', color: '#444', marginTop: '10px' }}>Visualización de Scatter PC1 vs PC2 disponible en versión Desktop</p>
                    </div>
                )}
            </motion.div>
        </div>
    );
};

// ======================================================================
// 4. PERMEABILITY COMPARISON MODAL
// ======================================================================
const PermComparisonModal = ({ data, onClose }) => {
    const perm = data?.perm_comparison || {};
    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '650px', padding: '30px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <Droplets size={24} color="#2dd4bf" />
                    <h2 style={{ fontSize: '20px', fontWeight: 900, color: '#fff', margin: 0 }}>Permeabilidad Comparativa</h2>
                </div>
                <p style={{ color: '#888', fontSize: '12px', marginBottom: '30px', marginLeft: '34px' }}>Comparación de modelos de permeabilidad (mD)</p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
                    <div style={{ padding: '20px', background: '#111', borderRadius: '16px', border: '1px solid #222', textAlign: 'center' }}>
                        <div style={{ fontSize: '10px', color: '#666', fontWeight: 700, marginBottom: '8px' }}>TIMUR-COATES (Clásico)</div>
                        <div style={{ fontSize: '28px', fontWeight: 900, color: '#f59e0b' }}>
                            {perm.timur_coates_avg || 0} <span style={{ fontSize: '12px', color: '#666' }}>mD avg</span>
                        </div>
                        <div style={{ fontSize: '10px', color: '#444', marginTop: '5px' }}>Basado en Sw irreductible teórica</div>
                    </div>

                    <div style={{ padding: '20px', background: '#111', borderRadius: '16px', border: '1px solid #222', textAlign: 'center' }}>
                        <div style={{ fontSize: '10px', color: '#666', fontWeight: 700, marginBottom: '8px' }}>MORRIS-BIGGS (Nuevo)</div>
                        <div style={{ fontSize: '28px', fontWeight: 900, color: '#2dd4bf' }}>
                            {perm.morris_biggs_avg || 0} <span style={{ fontSize: '12px', color: '#666' }}>mD avg</span>
                        </div>
                        <div style={{ fontSize: '10px', color: '#444', marginTop: '5px' }}>K = C × φ³ × Sw_irr (Recomendado)</div>
                    </div>
                </div>

                <div style={{ marginTop: '25px', padding: '15px', background: 'rgba(45,212,191,0.05)', borderRadius: '12px', border: '1px solid rgba(45,212,191,0.1)', fontSize: '11px', color: '#aaa', lineHeight: 1.6 }}>
                    <strong style={{ color: '#2dd4bf' }}>Interpretación:</strong> El modelo Morris-Biggs suele ser más optimista en arenas limpias y más preciso en presencia de gas. Timur-Coates es el estándar conservador. Se recomienda calibrar con datos de núcleo (Core Analysis) si están disponibles.
                </div>
            </motion.div>
        </div>
    );
};

// ======================================================================
// 5. PRODUCTION & OOIP MODAL
// ======================================================================
const ProductionOOIPModal = ({ data, onClose }) => {
    const prod = data?.production || {};
    const hyp = prod.hyperbolic || {};
    const ooip = prod.ooip_breakdown || {};

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '900px', maxHeight: '90vh', overflow: 'auto', padding: '30px', position: 'relative' }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <Target size={24} color="#fb923c" />
                    <h2 style={{ fontSize: '20px', fontWeight: 900, color: '#fff', margin: 0 }}>Reservoir Engineering & OOIP</h2>
                </div>
                <p style={{ color: '#888', fontSize: '12px', marginBottom: '30px', marginLeft: '34px' }}>Cálculo volumétrico y pronóstico de declinación (Arps)</p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
                    {/* OOIP Box */}
                    <div style={{ background: '#111', borderRadius: '20px', padding: '24px', border: '1px solid #222' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                            <Box size={18} color="#a78bfa" />
                            <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: '#a78bfa' }}>VOLUMETRÍA ORIGINAL (OOIP)</h3>
                        </div>

                        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                            <div style={{ fontSize: '36px', fontWeight: 900, color: '#fff' }}>
                                {(ooip.ooip_stb / 1000000).toFixed(2)} <span style={{ fontSize: '14px', color: '#666', fontWeight: 600 }}>MMstb</span>
                            </div>
                            <div style={{ fontSize: '10px', color: '#666' }}>Original Oil In Place (STB)</div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            {[
                                ['Área Drenaje', `${ooip.area_acres} ac`],
                                ['Net Pay (h)', `${ooip.net_pay_ft} ft`],
                                ['Porosidad Avg', `${(ooip.avg_porosity * 100).toFixed(1)}%`],
                                ['So (1-Sw)', `${((1 - ooip.avg_sh) * 100).toFixed(1)}%`],
                                ['Bo (FVF)', ooip.bo],
                                ['So*Phi*h', `${(ooip.avg_porosity * (1 - ooip.avg_sh) * ooip.net_pay_ft).toFixed(2)}`]
                            ].map(([l, v], i) => (
                                <div key={i} style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontSize: '10px', color: '#888' }}>{l}</span>
                                    <span style={{ fontSize: '10px', fontWeight: 700, color: '#ccc' }}>{v}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Decline Box */}
                    <div style={{ background: '#111', borderRadius: '20px', padding: '24px', border: '1px solid #222' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                            <TrendingUp size={18} color="#fb923c" />
                            <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: '#fb923c' }}>PRONÓSTICO DE PRODUCCIÓN</h3>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                            <div>
                                <div style={{ fontSize: '10px', color: '#666', fontWeight: 700 }}>RESERVAS (EUR 10y)</div>
                                <div style={{ fontSize: '20px', fontWeight: 900, color: '#fb923c' }}>{(hyp.cumulative_10y / 1000).toFixed(1)} <span style={{ fontSize: '11px' }}>Mbbl</span></div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '10px', color: '#666', fontWeight: 700 }}>Qi INICIAL</div>
                                <div style={{ fontSize: '20px', fontWeight: 900, color: '#fff' }}>{hyp.qi_stb} <span style={{ fontSize: '11px' }}>bopd</span></div>
                            </div>
                        </div>

                        <div style={{ fontSize: '11px', color: '#aaa', lineHeight: 1.6, background: 'rgba(251,146,60,0.05)', padding: '12px', borderRadius: '10px' }}>
                            <p style={{ margin: '0 0 8px 0' }}><strong style={{ color: '#fb923c' }}>Modelo Hiperbólico (Arps):</strong></p>
                            <ul style={{ margin: 0, paddingLeft: '15px' }}>
                                <li>Factor de curvatura (b): <strong>{hyp.b_factor}</strong></li>
                                <li>Declinación nominal (Di): <strong>{hyp.di_percent}% / año</strong></li>
                                <li>Límite económico: <strong>10 años</strong></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

// ======================================================================
// MAIN DASHBOARD
// ======================================================================
// ======================================================================
const UserGuideModal = ({ onClose }) => (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }} onClick={onClose}>
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            style={{ background: '#0a0a0a', borderRadius: '25px', border: '1px solid #1a1a1a', width: '95%', maxWidth: '800px', maxHeight: '85vh', overflow: 'auto', padding: '40px', position: 'relative' }} onClick={e => e.stopPropagation()}>
            <button onClick={onClose} style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid #333', borderRadius: '12px', padding: '8px', cursor: 'pointer', color: 'white' }}><X size={18} /></button>

            <h2 style={{ fontSize: '24px', fontWeight: 900, color: '#fff', marginBottom: '10px' }}>Manual de Usuario <span style={{ color: '#00f2ff' }}>DataTerra v2.1</span></h2>
            <p style={{ color: '#888', marginBottom: '30px' }}>Guía rápida de operación y explicación de módulos.</p>

            <div style={{ display: 'grid', gap: '20px' }}>
                <section>
                    <h3 style={{ color: '#00f2ff', fontSize: '16px', fontWeight: 800 }}>1. Carga de Datos</h3>
                    <div style={{ fontSize: '13px', color: '#ccc', lineHeight: '1.6' }}>
                        El sistema acepta exclusivamente archivos estándar <strong>.LAS (Log ASCII Standard)</strong> versión 2.0.
                        Al cargar un archivo, el motor Python procesa automáticamente:
                        <ul style={{ marginTop: '5px', paddingLeft: '20px', color: '#aaa' }}>
                            <li>Normalización de curvas (GR, NPHI, RHOB, DT).</li>
                            <li>Cálculo de Volumen de Arcilla (Vsh) usando método Lineal/Larionov.</li>
                            <li>Cálculo de Porosidad Efectiva (Phi) y Saturación de Agua (Sw - Archie/Simandoux).</li>
                            <li>Detección automática de zonas de paga (Net Pay).</li>
                        </ul>
                    </div>
                </section>

                <section>
                    <h3 style={{ color: '#a78bfa', fontSize: '16px', fontWeight: 800 }}>2. Módulo de Geología & Geofísica (NUEVO)</h3>
                    <div style={{ fontSize: '13px', color: '#ccc', lineHeight: '1.6' }}>
                        Herramientas avanzadas para visualizar el subsuelo:
                        <ul style={{ marginTop: '5px', paddingLeft: '20px', color: '#aaa' }}>
                            <li><strong>Seismic 2D Section:</strong> Genera un sismograma sintético en tiempo real usando las curvas Sónico (DT) y Densidad (RHOB). Convoluciona una ondícula de Ricker (30Hz) para simular la respuesta sísmica.</li>
                            <li><strong>Well Trajectory 3D:</strong> Visualización tridimensional del pozo. Permite ver la desviación y "navegar" por el reservorio.</li>
                            <li><strong>Litho-Scanner:</strong> Cubo 3D de propiedades petrofísicas cruzadas.</li>
                        </ul>
                    </div>
                </section>

                <section>
                    <h3 style={{ color: '#ef4444', fontSize: '16px', fontWeight: 800 }}>3. Perforación y Seguridad (NUEVO)</h3>
                    <p style={{ fontSize: '13px', color: '#ccc', lineHeight: '1.6' }}>
                        <strong>Drilling Risk Analysis (DLS):</strong> Utiliza la trayectoria 3D para calcular la "Severidad de Pata de Perro" (Dog-Leg Severity).
                        <br />Si la curvatura excede 3°/100ft, el tramo se marca en <span style={{ color: '#ef4444' }}>ROJO</span> indicando riesgo de atascamiento.
                    </p>
                </section>

                <section>
                    <h3 style={{ color: '#f472b6', fontSize: '16px', fontWeight: 800 }}>4. Ingeniería de Producción</h3>
                    <p style={{ fontSize: '13px', color: '#ccc', lineHeight: '1.6' }}>
                        <strong>Nodal Analysis:</strong> Simulador de flujo multifásico (Correlaciones Beggs & Brill / Hagedorn & Brown).
                        Permite calcular el caudal óptimo del pozo cruzando la curva IPR (Reservorio) con la VLP (Tubería).
                    </p>
                </section>
            </div>

            <div style={{ marginTop: '40px', paddingTop: '20px', borderTop: '1px solid #333', textAlign: 'center', fontSize: '11px', color: '#666' }}>
                © 2025 DataTerra Systems • Soporte Técnico: support@dataterra.ai
            </div>
        </motion.div>
    </div>
);

// ======================================================================
// MAIN DASHBOARD
// ======================================================================
const ExecutiveDashboard = ({ data, onUploadRequest, historyFiles, onLoadHistory, isUploading, uploadProgress }) => {
    const [activeTab, setActiveTab] = useState('executive');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [activeModal, setActiveModal] = useState(null);
    const isMobile = useIsMobile();

    const menuItems = [
        { id: 'executive', label: 'EXECUTIVE', icon: LayoutGrid },
        { id: 'geology', label: 'GEOLOGY', icon: Globe },
        { id: 'petrophysics', label: 'PETROPHYSICS', icon: Binary },
        { id: 'analytics', label: 'ANALYTICS & DATA', icon: BarChart3 },
    ];

    const handleTabChange = (id) => { setActiveTab(id); if (isMobile) setSidebarOpen(false); };
    const openModal = (id) => setActiveModal(id);
    const closeModal = () => setActiveModal(null);

    return (
        <div style={{ backgroundColor: '#050505', color: 'white', minHeight: '100vh', display: 'flex', flexDirection: isMobile ? 'column' : 'row', fontFamily: '"Space Grotesk", sans-serif', padding: isMobile ? '15px' : '30px 40px', overflowX: 'hidden' }}>
            {/* OVERLAY DE CARGA PREMIUM */}
            <AnimatePresence>
                {isUploading && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 99999, background: '#050505', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>

                        {/* Círculos Pulsantes */}
                        <div style={{ position: 'relative', width: '80px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '30px' }}>
                            <div style={{ position: 'absolute', width: '100%', height: '100%', borderRadius: '50%', border: '2px solid #00f2ff', animation: 'pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite' }}></div>
                            <div style={{ position: 'absolute', width: '60%', height: '60%', borderRadius: '50%', background: 'rgba(0, 242, 255, 0.1)', border: '1px solid rgba(0, 242, 255, 0.3)', boxShadow: '0 0 15px rgba(0, 242, 255, 0.3)' }}></div>
                        </div>

                        {/* Texto de Carga */}
                        <p style={{ color: '#ccc', fontSize: '12px', letterSpacing: '2px', fontWeight: 600, textTransform: 'uppercase', marginBottom: '15px' }}>
                            {uploadProgress || 'INICIANDO...'}
                        </p>

                        {/* Barra de Progreso */}
                        <div style={{ width: '240px', height: '4px', background: '#1a1a1a', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{
                                height: '100%',
                                background: '#00f2ff',
                                width: uploadProgress?.includes('Leyendo') ? '30%' :
                                    uploadProgress?.includes('Procesando') ? '65%' :
                                        uploadProgress?.includes('Renderizando') ? '90%' : '10%',
                                transition: 'width 0.5s ease',
                                boxShadow: '0 0 10px rgba(0, 242, 255, 0.5)'
                            }}></div>
                        </div>

                    </motion.div>
                )}
            </AnimatePresence>
            <style>{`
                @keyframes pulse-ring {
                    0% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 242, 255, 0.7); }
                    70% { transform: scale(1.1); box-shadow: 0 0 0 15px rgba(0, 242, 255, 0); }
                    100% { transform: scale(0.8); box-shadow: 0 0 0 0 rgba(0, 242, 255, 0); }
                }
            `}</style>
            {isMobile && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><Hexagon size={28} color="#00f2ff" /><span style={{ fontWeight: 900, fontSize: '16px' }}>DATA<span style={{ color: '#00f2ff' }}>TERRA</span></span></div>
                    <button onClick={() => setSidebarOpen(true)} style={{ background: 'transparent', border: 'none', color: 'white' }}><Menu size={24} /></button>
                </div>
            )}
            <AnimatePresence>
                {(sidebarOpen || !isMobile) && (
                    <motion.div initial={isMobile ? { x: '-100%' } : { x: 0 }} animate={{ x: 0 }} exit={{ x: '-100%' }} style={{
                        width: isMobile ? '100%' : '240px', height: isMobile ? '100vh' : 'calc(100vh - 60px)', position: isMobile ? 'fixed' : 'sticky',
                        top: isMobile ? 0 : '30px', left: 0, zIndex: 1000, background: '#050505', padding: isMobile ? '30px' : '0 20px 0 0',
                        display: 'flex', flexDirection: 'column', gap: '20px', borderRight: isMobile ? 'none' : '1px solid rgba(255,255,255,0.05)', overflowY: 'auto'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                            {!isMobile && <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><Hexagon size={28} color="#00f2ff" /><span style={{ fontWeight: 900, fontSize: '18px' }}>DATA<span style={{ color: '#00f2ff' }}>TERRA</span></span></div>}
                            {isMobile && <button onClick={() => setSidebarOpen(false)} style={{ background: 'transparent', border: 'none', color: 'white' }}><X size={24} /></button>}
                        </div>
                        {data && (
                            <div style={{ background: 'rgba(0,242,255,0.04)', padding: '14px', borderRadius: '18px', border: '1px solid rgba(0,242,255,0.1)' }}>
                                <p style={{ fontSize: '9px', fontWeight: 'bold', opacity: 0.4, letterSpacing: '1px', margin: 0 }}>ACTIVE WELL</p>
                                <p style={{ fontSize: '14px', fontWeight: 900, margin: '5px 0 0 0', color: '#00f2ff' }}>{data.well_info?.well_name || data.filename}</p>
                                <p style={{ fontSize: '9px', opacity: 0.4, marginTop: '3px' }}>{data.well_info?.field || ''} | {data.well_info?.operator || ''}</p>
                            </div>
                        )}

                        {/* HISTORIAL SELECTOR */}
                        {historyFiles && historyFiles.length > 0 && (
                            <div style={{ marginTop: '5px', marginBottom: '10px' }}>
                                <p style={{ fontSize: '10px', fontWeight: 700, color: '#555', marginBottom: '6px', marginLeft: '4px', letterSpacing: '0.5px' }}>SESIONES PREVIAS</p>
                                <select
                                    onChange={(e) => { if (e.target.value) onLoadHistory(e.target.value); }}
                                    style={{
                                        width: '100%', padding: '10px', background: '#0a0a0a', color: '#aaa',
                                        border: '1px solid #222', borderRadius: '12px', fontSize: '11px', outline: 'none', cursor: 'pointer'
                                    }}
                                >
                                    <option value="">📂 Abrir reciente...</option>
                                    {historyFiles.map((f, i) => (
                                        <option key={i} value={f.filename}>{f.filename.split('_')[0]} — {f.date}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* MAIN NAVIGATION */}
                        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {menuItems.map(item => (
                                <button key={item.id} onClick={() => handleTabChange(item.id)} style={{
                                    padding: '12px 16px', background: activeTab === item.id ? 'rgba(0,242,255,0.1)' : 'transparent',
                                    border: activeTab === item.id ? '1px solid rgba(0,242,255,0.15)' : '1px solid transparent',
                                    borderRadius: '14px', color: activeTab === item.id ? '#00f2ff' : 'rgba(255,255,255,0.35)',
                                    display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', textAlign: 'left', fontWeight: 700, fontSize: '11px',
                                }}><item.icon size={16} /> {item.label}</button>
                            ))}
                        </nav>

                        {/* ACTION BUTTONS */}
                        <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {/* Botón Cargar Nuevo LAS */}
                            <button onClick={onUploadRequest} style={{
                                padding: '12px 16px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: '14px', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px',
                                cursor: 'pointer', fontWeight: 800, fontSize: '11px',
                            }}><Download size={16} style={{ transform: 'rotate(180deg)' }} /> CARGAR NUEVO .LAS</button>

                            {/* Botón Ayuda / Manual */}
                            <button onClick={() => openModal('guide')} style={{
                                padding: '12px 16px', background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.15)',
                                borderRadius: '14px', color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '10px',
                                cursor: 'pointer', fontWeight: 800, fontSize: '11px',
                            }}><FileText size={16} /> GUÍA DE USUARIO</button>

                            {data && (
                                <button onClick={() => openModal('export')} style={{
                                    padding: '12px 16px', background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.15)',
                                    borderRadius: '14px', color: '#4ade80', display: 'flex', alignItems: 'center', gap: '10px',
                                    cursor: 'pointer', fontWeight: 800, fontSize: '11px',
                                }}><Share2 size={16} /> EXPORTAR / REPORTE</button>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
            <div style={{ flex: 1, paddingLeft: isMobile ? 0 : '30px', display: 'flex', flexDirection: 'column' }}>
                <header style={{ marginBottom: '25px' }}>
                    <p style={{ fontSize: '10px', color: '#00f2ff', fontWeight: 900, letterSpacing: '2px', margin: 0 }}>{activeTab.toUpperCase()} MODULE</p>
                    <h1 style={{ fontSize: isMobile ? '1.6rem' : '2.2rem', fontWeight: 900, letterSpacing: '-2px', margin: '5px 0 0 0' }}>
                        {activeTab === 'executive' && 'Executive Overview'}
                        {activeTab === 'geology' && 'Subsurface Modeling'}
                        {activeTab === 'petrophysics' && 'Well Log Analysis'}
                        {activeTab === 'analytics' && 'Analytics & Data'}
                    </h1>
                </header>
                <main style={{ flex: 1, paddingBottom: isMobile ? '80px' : 0 }}>
                    <AnimatePresence mode="wait">
                        {activeTab === 'executive' && <ExecutiveView key="1" data={data} isMobile={isMobile} />}
                        {activeTab === 'geology' && <GeologyView key="2" data={data} isMobile={isMobile} openModal={openModal} />}
                        {activeTab === 'petrophysics' && <PetrophysicsView key="3" data={data} isMobile={isMobile} />}
                        {activeTab === 'analytics' && <AnalyticsView key="4" data={data} isMobile={isMobile} openModal={openModal} />}
                    </AnimatePresence>
                </main>
            </div>
            {/* MODALS */}
            <AnimatePresence>
                {activeModal === 'lithoCube' && <LithoCube3D data={data} onClose={closeModal} />}
                {activeModal === 'lithology' && <LithologySection data={data} onClose={closeModal} />}
                {activeModal === 'seismic' && <SeismicSection data={data} onClose={closeModal} />}
                {activeModal === 'trajectory' && <WellTrajectory3D data={data} onClose={closeModal} />}
                {activeModal === 'wellTie' && <WellTieModal data={data} onClose={closeModal} />}
                {activeModal === 'bubble' && <BubbleExplorer data={data} onClose={closeModal} />}
                {activeModal === 'histogram' && <HistogramModal data={data} onClose={closeModal} />}
                {activeModal === 'radar' && <RadarModal data={data} onClose={closeModal} />}
                {activeModal === 'scatter' && <ScatterModal data={data} onClose={closeModal} />}
                {activeModal === 'production' && <ProductionModal isOpen={true} wellData={data?.well_info} kpis={data?.kpis} onClose={closeModal} />}
                {activeModal === 'dataQC' && <DataQCModal data={data} onClose={closeModal} />}
                {activeModal === 'export' && <ExportModal data={data} onClose={closeModal} />}
                {activeModal === 'guide' && <UserGuideModal onClose={closeModal} />}
                {activeModal === 'drillingRisk' && <DrillingRiskModal data={data} onClose={closeModal} />}
                {activeModal === 'electrofacies' && <ElectrofaciesModal data={data} onClose={closeModal} />}
                {activeModal === 'pcaAnalysis' && <PCAAnalysisModal data={data} onClose={closeModal} />}
                {activeModal === 'permComparison' && <PermComparisonModal data={data} onClose={closeModal} />}
                {activeModal === 'productionOOIP' && <ProductionOOIPModal data={data} onClose={closeModal} />}
                {activeModal === 'unitConversions' && <UnitConversionsModal data={data} onClose={closeModal} />}
            </AnimatePresence>
        </div>
    );
};

export default ExecutiveDashboard;
