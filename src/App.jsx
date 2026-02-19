import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, BarChart3, Layers, Activity, Globe, Zap, ArrowRight, ChevronDown, Database, Cpu, FileText, Share2, ArrowLeft, Hexagon, Waves, Target, TrendingUp, Check, Crown, Building2, User, Shield, Star, BadgeDollarSign, MonitorDown, AlertTriangle, ShieldCheck, Lock } from 'lucide-react';
import './index.css';
import ExecutiveDashboard from './pages/ExecutiveDashboard';

// ====== SVG Mini-chart previews for feature cards ======
const MiniLogChart = () => (
    <svg viewBox="0 0 120 80" style={{ width: '100%', height: '80px', opacity: 0.6 }}>
        <defs>
            <linearGradient id="grd1" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#00f2ff" stopOpacity="0.4" /><stop offset="100%" stopColor="#00f2ff" stopOpacity="0" /></linearGradient>
        </defs>
        <path d="M0,60 L8,55 L16,58 L24,40 L32,45 L40,30 L48,35 L56,20 L64,25 L72,18 L80,22 L88,15 L96,28 L104,20 L112,12 L120,15" fill="none" stroke="#00f2ff" strokeWidth="1.5" />
        <path d="M0,60 L8,55 L16,58 L24,40 L32,45 L40,30 L48,35 L56,20 L64,25 L72,18 L80,22 L88,15 L96,28 L104,20 L112,12 L120,15 L120,80 L0,80 Z" fill="url(#grd1)" />
        <path d="M0,45 L15,50 L30,42 L45,55 L60,48 L75,52 L90,38 L105,42 L120,35" fill="none" stroke="#4ade80" strokeWidth="1" strokeDasharray="3,3" />
    </svg>
);

const mini3DPoints = [
    [22, 62, 2, '#00f2ff'], [30, 52, 2.4, '#fb923c'], [40, 45, 2.8, '#00f2ff'],
    [50, 34, 2, '#fb923c'], [60, 25, 2.6, '#00f2ff'], [70, 38, 2.2, '#fb923c'],
    [80, 29, 2.9, '#00f2ff'], [90, 21, 2.1, '#fb923c'], [96, 48, 2.4, '#00f2ff'],
    [72, 56, 2.3, '#fb923c'], [56, 60, 2.1, '#00f2ff'], [36, 65, 2.0, '#fb923c']
];

const Mini3DChart = () => (
    <svg viewBox="0 0 120 80" style={{ width: '100%', height: '80px', opacity: 0.6 }}>
        {mini3DPoints.map(([x, y, r, fill], i) => (
            <circle key={i} cx={x} cy={y} r={r} fill={fill} opacity={0.75} />
        ))}
        <line x1="10" y1="75" x2="110" y2="75" stroke="#333" strokeWidth="0.5" />
        <line x1="10" y1="5" x2="10" y2="75" stroke="#333" strokeWidth="0.5" />
        <line x1="10" y1="75" x2="60" y2="45" stroke="#333" strokeWidth="0.5" />
    </svg>
);

const MiniRadarChart = () => (
    <svg viewBox="0 0 120 80" style={{ width: '100%', height: '80px', opacity: 0.6 }}>
        <polygon points="60,10 95,30 85,65 35,65 25,30" fill="none" stroke="#333" strokeWidth="0.5" />
        <polygon points="60,25 80,37 75,57 45,57 40,37" fill="none" stroke="#333" strokeWidth="0.5" />
        <polygon points="60,15 88,33 80,62 40,62 32,33" fill="rgba(0,242,255,0.15)" stroke="#00f2ff" strokeWidth="1.5" />
        {[[60, 15], [88, 33], [80, 62], [40, 62], [32, 33]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="2.5" fill="#4ade80" />)}
    </svg>
);

const MiniSeismicChart = () => (
    <svg viewBox="0 0 120 80" style={{ width: '100%', height: '80px', opacity: 0.6 }}>
        {[...Array(12)].map((_, i) => {
            const x = 10 + i * 9;
            return <rect key={i} x={x} y={15 + Math.sin(i * 0.8) * 10} width="7" height={30 + Math.cos(i * 0.5) * 15} fill={i % 2 === 0 ? 'rgba(239,68,68,0.4)' : 'rgba(59,130,246,0.4)'} rx="1" />;
        })}
        <line x1="60" y1="5" x2="60" y2="78" stroke="red" strokeWidth="1" strokeDasharray="2,2" />
    </svg>
);

// ====== Animated counter ======
const AnimatedCounter = ({ target, suffix = '', prefix = '' }) => {
    const [count, setCount] = useState(0);
    useEffect(() => {
        let start = 0;
        const duration = 2000;
        const step = target / (duration / 16);
        const timer = setInterval(() => {
            start += step;
            if (start >= target) { setCount(target); clearInterval(timer); }
            else setCount(Math.floor(start));
        }, 16);
        return () => clearInterval(timer);
    }, [target]);
    return <>{prefix}{count.toLocaleString()}{suffix}</>;
};

function App() {
    const [view, setView] = useState('landing');
    const [realData, setRealData] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState('');
    const fileInputRef = useRef(null);
    const featuresRef = useRef(null);
    const pricingRef = useRef(null);
    const [scrolled, setScrolled] = useState(false);
    const [historyFiles, setHistoryFiles] = useState([]);

    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 80);
        window.addEventListener('scroll', handleScroll);

        // Cargar historial
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        fetch(`${apiUrl}/history`)
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data)) setHistoryFiles(data);
            })
            .catch(err => console.error("Error history:", err));

        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const loadHistoryFile = async (filename) => {
        setIsUploading(true);
        setUploadProgress('Recuperando sesión...');
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiUrl}/load_history/${filename}`);
            if (!res.ok) throw new Error("No se pudo cargar el archivo");
            const data = await res.json();
            setRealData(data);
            setTimeout(() => setView('dashboard'), 300);
        } catch (err) {
            alert("Error: " + err.message);
        } finally {
            setIsUploading(false);
            setUploadProgress('');
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setIsUploading(true);
        setUploadProgress('Leyendo archivo .LAS...');

        const formData = new FormData();
        formData.append('file', file);

        try {
            setUploadProgress('Procesando petrofísica con Python...');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error uploading file');
            }

            setUploadProgress('Renderizando gráficos...');
            const data = await response.json();
            setRealData(data);
            setTimeout(() => setView('dashboard'), 300);
        } catch (error) {
            console.error('Upload failed:', error);
            alert(`Error al procesar archivo: ${error.message}\n\nSi el problema persiste, el servidor backend podría estar reiniciándose (Cold Start). Espera 1 minuto y reintenta.`);
        } finally {
            setIsUploading(false);
            setUploadProgress('');
        }
    };

    const triggerFileInput = () => fileInputRef.current?.click();

    const scrollToFeatures = () => featuresRef.current?.scrollIntoView({ behavior: 'smooth' });
    const scrollToPricing = () => pricingRef.current?.scrollIntoView({ behavior: 'smooth' });

    // ====== DASHBOARD VIEW ======
    if (view === 'dashboard') {
        return (
            <div style={{ backgroundColor: '#050505', minHeight: '100vh' }}>
                {/* Hidden Input for File Upload in Dashboard */}
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".las,.LAS"
                    style={{ display: 'none' }}
                />

                <motion.button
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    onClick={() => setView('landing')}
                    style={{
                        position: 'fixed', top: '14px', right: '20px', zIndex: 100,
                        padding: '8px 18px', display: 'flex', alignItems: 'center', gap: '8px',
                        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(12px)',
                        color: '#94a3b8', border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '12px', cursor: 'pointer', fontSize: '11px', fontWeight: 700,
                        fontFamily: 'Inter, sans-serif', letterSpacing: '0.5px',
                        transition: 'all 0.3s ease',
                    }}
                    whileHover={{ background: 'rgba(0,242,255,0.08)', color: '#00f2ff', borderColor: 'rgba(0,242,255,0.2)' }}
                >
                    <ArrowLeft size={14} />
                    INICIO
                </motion.button>
                <ExecutiveDashboard
                    data={realData}
                    onUploadRequest={triggerFileInput}
                    historyFiles={historyFiles}
                    onLoadHistory={loadHistoryFile}
                    isUploading={isUploading}
                    uploadProgress={uploadProgress}
                />
            </div>
        );
    }

    // ====== LANDING PAGE ======
    const modules = [
        {
            icon: <BarChart3 size={22} color="#00f2ff" />,
            title: 'Registros Petrofísicos',
            desc: 'Multi-track log viewer con 11 curvas: GR, RT, NPHI, RHOB, DT, VSH, PHI, SW, K, SH. Headers detallados con unidades, rango y tipo de escala.',
            chart: <MiniLogChart />,
            color: '#00f2ff',
            preview: null,
        },
        {
            icon: <Hexagon size={22} color="#a78bfa" />,
            title: 'Litho-Scanner 3D',
            desc: 'Cubo volumétrico 3D interactivo. Cruza porosidad, densidad y profundidad con código de colores por GR, VSH, PHI, SW o Permeabilidad.',
            chart: <Mini3DChart />,
            color: '#a78bfa',
            preview: '/previews/litho_scanner.png',
        },
        {
            icon: <Waves size={22} color="#ef4444" />,
            title: 'Geofísica Sintética',
            desc: 'Impedancia Acústica, Coeficientes de Reflexión, Well Tie con wavelet Ricker y sección sísmica 2D generada desde RHOB + DT.',
            chart: <MiniSeismicChart />,
            color: '#ef4444',
            preview: '/previews/geofisica.png',
        },
        {
            icon: <Target size={22} color="#4ade80" />,
            title: 'Calidad de Roca (RQI)',
            desc: 'Radar multidimensional: Porosidad, Saturación HC, Limpieza, Potencial Económico y Calidad de Datos — scoring 0-100%.',
            chart: <MiniRadarChart />,
            color: '#4ade80',
            preview: '/previews/rqi_radar.png',
        },
        {
            icon: <Activity size={22} color="#fbbf24" />,
            title: 'Correlaciones & Distribución',
            desc: 'Histogramas estadísticos, análisis de Pearson con scatter interactivos, y explorador 4D Bubble con 4 variables simultáneas.',
            chart: <MiniLogChart />,
            color: '#fbbf24',
            preview: '/previews/correlaciones.png',
        },
        {
            icon: <TrendingUp size={22} color="#f472b6" />,
            title: 'Producción & Economía',
            desc: 'Pronóstico Arps 10 años con OIP estimado, curva de producción, ingresos acumulados y análisis de declinación exponencial.',
            chart: <MiniLogChart />,
            color: '#f472b6',
            preview: '/previews/produccion.png',
        },
        {
            icon: <Layers size={22} color="#06b6d4" />,
            title: 'Electrofacies (K-Means)',
            desc: 'Clasificación automática de litología usando Machine Learning (K-Means Clustering). Identifica Arena, Lutita, Carbonato y zonas mixtas sin datos de núcleo.',
            chart: <MiniRadarChart />,
            color: '#06b6d4',
            preview: '/previews/electrofacies.png',
        },
        {
            icon: <AlertTriangle size={22} color="#ef4444" />,
            title: 'Drilling Risk (DLS)',
            desc: 'Análisis de Dog-Leg Severity para evaluación de riesgo de perforación. Clasifica puntos críticos por severidad (Bajo/Medio/Alto/Crítico).',
            chart: <MiniSeismicChart />,
            color: '#ef4444',
            preview: '/previews/drilling_risk.png',
        },
        {
            icon: <ShieldCheck size={22} color="#22c55e" />,
            title: 'Auditoría Forense',
            desc: 'Certificación de lectura completa: líneas cargadas, cobertura de profundidad, curvas detectadas, confirmación de cada cálculo ejecutado.',
            chart: <MiniLogChart />,
            color: '#22c55e',
            preview: '/previews/auditoria.png',
        },
    ];

    const workflow = [
        { step: '01', title: 'Carga tu archivo .LAS', desc: 'Arrastra o selecciona. Compatible con LAS 2.0 de cualquier servicio de wireline.', icon: <Upload size={20} /> },
        { step: '02', title: 'Python procesa en segundos', desc: 'Vsh (Linear), Sw (Archie + Simandoux), Permeabilidad, Pay Zones, QC — todo automático.', icon: <Cpu size={20} /> },
        { step: '03', title: 'Visualiza 11+ gráficos', desc: 'Dashboard interactivo con módulos de Geología, Petrofísica, Analytics y Reservoir.', icon: <BarChart3 size={20} /> },
        { step: '04', title: 'Exporta reporte completo', desc: 'PDF, HTML responsive, CSV de datos, Pay Zones — con interpretaciones técnicas incluidas.', icon: <FileText size={20} /> },
    ];

    return (
        <div style={{ background: '#050505', minHeight: '100vh', fontFamily: "'Inter', sans-serif", overflowX: 'hidden' }}>
            <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".las" style={{ display: 'none' }} />

            {/* ====== NAVBAR ====== */}
            <motion.nav
                initial={{ y: -80 }}
                animate={{ y: 0 }}
                transition={{ delay: 0.2 }}
                style={{
                    position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '16px 5%',
                    background: scrolled ? 'rgba(5,5,5,0.9)' : 'transparent',
                    backdropFilter: scrolled ? 'blur(20px)' : 'none',
                    borderBottom: scrolled ? '1px solid rgba(255,255,255,0.05)' : 'none',
                    transition: 'all 0.4s ease',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        width: '38px', height: '38px', borderRadius: '10px',
                        background: 'linear-gradient(135deg, #00f2ff, #0088ff)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontWeight: 900, fontSize: '1.1rem', color: '#000',
                        boxShadow: '0 0 20px rgba(0,242,255,0.3)',
                    }}>D</div>
                    <span style={{ fontFamily: "'Outfit', sans-serif", fontWeight: 900, fontSize: '1.15rem', letterSpacing: '-0.5px' }}>
                        DATA<span style={{ color: '#00f2ff' }}>TERRA</span>
                    </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '30px' }}>
                    <a onClick={scrollToFeatures} style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.05em', textDecoration: 'none', transition: '0.3s' }}>Módulos</a>
                    <a onClick={scrollToPricing} style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.05em', textDecoration: 'none', transition: '0.3s' }}>Planes</a>
                    <button onClick={triggerFileInput} disabled={isUploading} style={{
                        padding: '9px 22px', borderRadius: '50px', fontWeight: 800,
                        fontSize: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase',
                        background: '#00f2ff', color: '#000', border: 'none', cursor: 'pointer',
                        boxShadow: '0 0 15px rgba(0,242,255,0.3)', transition: '0.3s',
                    }}>{isUploading ? 'PROCESANDO...' : 'CARGAR .LAS'}</button>
                </div>
            </motion.nav>

            {/* ====== HERO SECTION ====== */}
            <section style={{
                minHeight: '100vh', display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', textAlign: 'center',
                position: 'relative', padding: '120px 5% 80px', overflow: 'hidden',
            }}>
                {/* Animated background effects */}
                <div style={{
                    position: 'absolute', top: '-30%', right: '-10%', width: '700px', height: '700px',
                    borderRadius: '50%', background: 'radial-gradient(circle, rgba(0,242,255,0.06) 0%, transparent 70%)',
                    filter: 'blur(60px)', pointerEvents: 'none',
                }} />
                <div style={{
                    position: 'absolute', bottom: '-20%', left: '-10%', width: '500px', height: '500px',
                    borderRadius: '50%', background: 'radial-gradient(circle, rgba(112,0,255,0.04) 0%, transparent 70%)',
                    filter: 'blur(60px)', pointerEvents: 'none',
                }} />
                {/* Grid lines decoration */}
                <div style={{
                    position: 'absolute', inset: 0, opacity: 0.03,
                    backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
                    backgroundSize: '60px 60px', pointerEvents: 'none',
                }} />

                <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.8 }}>
                    <div style={{
                        display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 18px',
                        background: 'rgba(0,242,255,0.06)', border: '1px solid rgba(0,242,255,0.12)',
                        borderRadius: '50px', marginBottom: '30px', fontSize: '0.75rem', color: '#00f2ff',
                        fontWeight: 700, letterSpacing: '0.5px',
                    }}>
                        <Zap size={12} /> SISTEMA PETROFÍSICO AVANZADO
                    </div>
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, duration: 0.8 }}
                    style={{
                        fontFamily: "'Outfit', sans-serif",
                        fontSize: 'clamp(2.5rem, 7vw, 5.5rem)',
                        fontWeight: 900, lineHeight: 0.95, letterSpacing: '-0.04em',
                        marginBottom: '25px', maxWidth: '900px',
                    }}
                >
                    Inteligencia de<br />
                    <span style={{
                        background: 'linear-gradient(135deg, #00f2ff, #0088ff, #00f2ff)',
                        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                        textShadow: 'none',
                    }}>Subsuelo</span> en tiempo real
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7, duration: 0.8 }}
                    style={{
                        color: '#94a3b8', fontSize: 'clamp(0.9rem, 1.5vw, 1.15rem)',
                        maxWidth: '600px', lineHeight: 1.7, marginBottom: '40px',
                    }}
                >
                    Carga un archivo <strong style={{ color: '#fff' }}>.LAS</strong> y obtén análisis petrofísico completo,
                    geofísica sintética, detección de pay zones y pronóstico de producción — todo procesado por{' '}
                    <strong style={{ color: '#fff' }}>Python</strong>, visualizado en tu navegador.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.9, duration: 0.8 }}
                    style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}
                >
                    <button onClick={triggerFileInput} disabled={isUploading} style={{
                        display: 'flex', alignItems: 'center', gap: '10px',
                        padding: '16px 36px', fontSize: '0.9rem', fontWeight: 800,
                        background: 'linear-gradient(135deg, #00f2ff, #0088ff)', color: '#000',
                        border: 'none', borderRadius: '50px', cursor: isUploading ? 'wait' : 'pointer',
                        boxShadow: '0 0 30px rgba(0,242,255,0.35), 0 4px 20px rgba(0,0,0,0.3)',
                        transition: 'all 0.3s ease', letterSpacing: '0.02em',
                    }}>
                        <Upload size={18} />
                        {isUploading ? uploadProgress || 'PROCESANDO...' : 'CARGAR ARCHIVO .LAS'}
                    </button>
                </motion.div>

                {/* Upload progress indicator */}
                <AnimatePresence>
                    {isUploading && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0 }}
                            style={{
                                marginTop: '20px', padding: '12px 24px',
                                background: 'rgba(0,242,255,0.06)', border: '1px solid rgba(0,242,255,0.15)',
                                borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '10px',
                            }}
                        >
                            <div style={{
                                width: '16px', height: '16px', border: '2px solid #00f2ff',
                                borderTopColor: 'transparent', borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                            }} />
                            <span style={{ fontSize: '0.8rem', color: '#00f2ff', fontWeight: 600 }}>{uploadProgress}</span>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Stats bar */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.3 }}
                    style={{
                        marginTop: '60px', display: 'flex', gap: '40px', flexWrap: 'wrap', justifyContent: 'center',
                    }}
                >
                    {[
                        { val: 11, suffix: '+', label: 'Curvas Petrofísicas' },
                        { val: 6, suffix: '', label: 'Módulos Integrados' },
                        { val: 15, suffix: '+', label: 'Gráficos Interactivos' },
                        { val: 100, suffix: '%', label: 'Datos Reales' },
                    ].map((s, i) => (
                        <div key={i} style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.8rem', fontWeight: 900, fontFamily: "'Outfit', sans-serif" }}>
                                <span style={{ color: '#00f2ff' }}><AnimatedCounter target={s.val} suffix={s.suffix} /></span>
                            </div>
                            <div style={{ fontSize: '0.7rem', color: '#555', fontWeight: 600, letterSpacing: '1px', textTransform: 'uppercase' }}>{s.label}</div>
                        </div>
                    ))}
                </motion.div>

                {/* Scroll indicator */}
                <motion.div
                    animate={{ y: [0, 8, 0] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    onClick={scrollToFeatures}
                    style={{ position: 'absolute', bottom: '30px', cursor: 'pointer', opacity: 0.3 }}
                >
                    <ChevronDown size={28} />
                </motion.div>
            </section>

            {/* ====== WORKFLOW SECTION ====== */}
            <section style={{ padding: '80px 5% 60px', position: 'relative' }}>
                <div style={{ textAlign: 'center', marginBottom: '60px' }}>
                    <h2 style={{ fontFamily: "'Outfit', sans-serif", fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontWeight: 900, marginBottom: '12px' }}>
                        ¿Cómo <span style={{ color: '#00f2ff' }}>funciona</span>?
                    </h2>
                    <p style={{ color: '#555', fontSize: '0.9rem', maxWidth: '500px', margin: '0 auto' }}>
                        De archivo .LAS a reporte profesional en 4 pasos
                    </p>
                </div>
                <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                    gap: '20px', maxWidth: '1100px', margin: '0 auto',
                }}>
                    {workflow.map((w, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.15 }}
                            style={{
                                padding: '30px 25px', borderRadius: '20px',
                                background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)',
                                position: 'relative', overflow: 'hidden',
                            }}
                        >
                            <span style={{
                                position: 'absolute', top: '15px', right: '18px',
                                fontSize: '3rem', fontWeight: 900, fontFamily: "'Outfit'",
                                color: 'rgba(0,242,255,0.05)', lineHeight: 1,
                            }}>{w.step}</span>
                            <div style={{
                                width: '42px', height: '42px', borderRadius: '12px',
                                background: 'rgba(0,242,255,0.08)', display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                color: '#00f2ff', marginBottom: '16px',
                            }}>{w.icon}</div>
                            <h3 style={{ fontSize: '0.95rem', fontWeight: 800, marginBottom: '8px' }}>{w.title}</h3>
                            <p style={{ fontSize: '0.78rem', color: '#666', lineHeight: 1.6 }}>{w.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* ====== MODULES GALLERY ====== */}
            <section ref={featuresRef} style={{ padding: '80px 5%', position: 'relative' }}>
                <div style={{ textAlign: 'center', marginBottom: '60px' }}>
                    <h2 style={{ fontFamily: "'Outfit', sans-serif", fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontWeight: 900, marginBottom: '12px' }}>
                        Módulos de <span style={{ color: '#00f2ff' }}>Análisis</span>
                    </h2>
                    <p style={{ color: '#555', fontSize: '0.9rem', maxWidth: '550px', margin: '0 auto' }}>
                        Cada módulo genera gráficos interactivos con datos 100% reales de tu archivo .LAS — con interpretaciones técnicas y leyendas detalladas
                    </p>
                </div>
                <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '24px', maxWidth: '1200px', margin: '0 auto',
                }}>
                    {modules.map((m, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.08 }}
                            style={{ perspective: '1000px', cursor: 'default' }}
                        >
                            {/* Outer wrapper - contains bg reveal + fg card */}
                            <div className="reveal-card-wrapper" style={{
                                position: 'relative', borderRadius: '24px', overflow: 'hidden',
                                minHeight: '260px',
                            }}>
                                {/* BACKGROUND: Real preview image reveal layer */}
                                <div className="reveal-bg" style={{
                                    position: 'absolute', inset: 0,
                                }}>
                                    {m.preview ? (
                                        <img src={m.preview} alt={m.title} style={{
                                            width: '100%', height: '100%', objectFit: 'cover',
                                            borderRadius: '24px',
                                        }} />
                                    ) : (
                                        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '30px' }}>
                                            <div style={{ width: '100%', transform: 'scale(1.3)' }}>{m.chart}</div>
                                        </div>
                                    )}
                                    {/* Color glow */}
                                    <div style={{
                                        position: 'absolute', bottom: '-10px', left: '50%', transform: 'translateX(-50%)',
                                        width: '80%', height: '80px', borderRadius: '50%',
                                        background: m.color, filter: 'blur(50px)', opacity: 0.25,
                                    }} />
                                    {/* Gradient overlay for smooth blend */}
                                    <div style={{
                                        position: 'absolute', inset: 0, borderRadius: '24px',
                                        background: 'linear-gradient(to bottom, rgba(5,5,5,0.3) 0%, rgba(5,5,5,0.7) 100%)',
                                    }} />
                                </div>

                                {/* FOREGROUND: The card content that slides on hover */}
                                <div className="reveal-fg" style={{
                                    position: 'relative', zIndex: 2, padding: '28px', borderRadius: '24px',
                                    background: 'rgba(10,10,10,0.95)', border: '1px solid rgba(255,255,255,0.06)',
                                    backdropFilter: 'blur(12px)',
                                    transition: 'transform 0.5s cubic-bezier(.4,0,.2,1), box-shadow 0.5s ease',
                                    transformOrigin: 'left center',
                                    minHeight: '260px',
                                }}>
                                    {/* Mini chart preview */}
                                    <div style={{
                                        borderRadius: '14px', background: 'rgba(0,0,0,0.5)',
                                        padding: '12px', marginBottom: '18px', border: `1px solid ${m.color}10`,
                                    }}>
                                        {m.chart}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                        <div style={{
                                            width: '36px', height: '36px', borderRadius: '10px',
                                            background: `${m.color}12`, display: 'flex',
                                            alignItems: 'center', justifyContent: 'center',
                                            border: `1px solid ${m.color}20`,
                                        }}>{m.icon}</div>
                                        <h3 style={{ fontSize: '0.9rem', fontWeight: 800 }}>{m.title}</h3>
                                    </div>
                                    <p style={{ fontSize: '0.78rem', color: '#666', lineHeight: 1.65 }}>{m.desc}</p>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* ====== EXPORT & FEATURES ====== */}
            <section style={{ padding: '60px 5% 80px' }}>
                <div style={{
                    maxWidth: '1000px', margin: '0 auto', borderRadius: '30px',
                    background: 'linear-gradient(135deg, rgba(0,242,255,0.04), rgba(112,0,255,0.03))',
                    border: '1px solid rgba(0,242,255,0.08)', padding: 'clamp(30px, 5vw, 60px)',
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '40px',
                }}>
                    <div>
                        <h2 style={{ fontFamily: "'Outfit'", fontSize: '1.8rem', fontWeight: 900, marginBottom: '15px' }}>
                            Reportes <span style={{ color: '#00f2ff' }}>Profesionales</span>
                        </h2>
                        <p style={{ fontSize: '0.85rem', color: '#666', lineHeight: 1.7, marginBottom: '25px' }}>
                            Exporta tu análisis completo con un click. El reporte incluye resúmenes interpretativos de cada módulo gráfico,
                            KPIs, pay zones, correlaciones, y metodología detallada — listo para presentaciones técnicas.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {[
                                { icon: <Globe size={16} />, text: 'HTML Responsive — se abre en cualquier dispositivo', color: '#00f2ff' },
                                { icon: <FileText size={16} />, text: 'PDF via Print — con CSS optimizado para impresión', color: '#a78bfa' },
                                { icon: <Database size={16} />, text: 'CSV con todas las curvas + Pay Zones separado', color: '#fb923c' },
                                { icon: <Share2 size={16} />, text: 'Compartir resumen KPI por texto/clipboard', color: '#f472b6' },
                            ].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                    <span style={{ color: f.color }}>{f.icon}</span>
                                    <span style={{ fontSize: '0.78rem', color: '#999' }}>{f.text}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '20px' }}>
                        <div style={{
                            padding: '25px', borderRadius: '20px', background: 'rgba(0,0,0,0.4)',
                            border: '1px solid rgba(255,255,255,0.05)', width: '100%', textAlign: 'center',
                        }}>
                            <div style={{ fontSize: '0.6rem', color: '#555', fontWeight: 800, letterSpacing: '2px', marginBottom: '15px' }}>MOTOR DE ANÁLISIS</div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                                {[
                                    { label: 'Vsh', val: 'GR Index (Linear)' },
                                    { label: 'Sw', val: 'Archie + Simandoux' },
                                    { label: 'K', val: 'Morris-Biggs' },
                                    { label: 'Geofísica', val: 'Ricker Convolution' },
                                    { label: 'Pay', val: 'Custom Cutoff Detector' },
                                    { label: 'QC', val: 'SEG Standard Audit' },
                                ].map((m, i) => (
                                    <div key={i} style={{ padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', textAlign: 'left' }}>
                                        <div style={{ fontSize: '0.6rem', color: '#00f2ff', fontWeight: 800 }}>{m.label}</div>
                                        <div style={{ fontSize: '0.7rem', color: '#666' }}>{m.val}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <button onClick={triggerFileInput} disabled={isUploading} style={{
                            width: '100%', padding: '16px', borderRadius: '14px',
                            background: 'linear-gradient(135deg, #00f2ff, #0088ff)', color: '#000',
                            border: 'none', cursor: 'pointer', fontWeight: 800, fontSize: '0.85rem',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                            boxShadow: '0 0 25px rgba(0,242,255,0.25)',
                        }}>
                            Comenzar Análisis <ArrowRight size={16} />
                        </button>
                    </div>
                </div>
            </section>

            {/* ====== PRICING SECTION ====== */}
            <section ref={pricingRef} style={{ padding: '80px 5% 60px', position: 'relative' }}>
                {/* Section header */}
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                    <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                        <div style={{
                            display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 18px',
                            background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.12)',
                            borderRadius: '50px', marginBottom: '20px', fontSize: '0.7rem', color: '#fbbf24',
                            fontWeight: 700, letterSpacing: '1px',
                        }}>
                            <BadgeDollarSign size={12} /> SISTEMA DE LICENCIAS
                        </div>
                        <h2 style={{ fontFamily: "'Outfit', sans-serif", fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontWeight: 900, marginBottom: '12px' }}>
                            Planes & <span style={{ color: '#00f2ff' }}>Precios</span>
                        </h2>
                        <p style={{ color: '#555', fontSize: '0.85rem', maxWidth: '600px', margin: '0 auto', lineHeight: 1.7 }}>
                            Geoestadística avanzada, Machine Learning y Visualización Petrofísica —<br />
                            cada plan está diseñado para maximizar el retorno de tu inversión en exploración.
                        </p>
                    </motion.div>
                </div>

                {/* ROI Argument Banner */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    style={{
                        maxWidth: '900px', margin: '30px auto 50px', padding: '20px 28px', borderRadius: '16px',
                        background: 'linear-gradient(135deg, rgba(74,222,128,0.05), rgba(0,242,255,0.03))',
                        border: '1px solid rgba(74,222,128,0.12)',
                        display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap',
                    }}
                >
                    <div style={{
                        width: '44px', height: '44px', borderRadius: '12px', flexShrink: 0,
                        background: 'rgba(74,222,128,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}><Shield size={20} color="#4ade80" /></div>
                    <div style={{ flex: 1, minWidth: '250px' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#4ade80', letterSpacing: '1px', marginBottom: '4px' }}>JUSTIFICACIÓN DE INVERSIÓN (ROI)</div>
                        <p style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.6, margin: 0 }}>
                            Un error de interpretación en un solo pozo puede costar <strong style={{ color: '#fff' }}>millones de dólares</strong>.
                            DataTerra reduce el riesgo de incertidumbre en un <strong style={{ color: '#4ade80' }}>30%</strong> y ahorra
                            <strong style={{ color: '#4ade80' }}> 40 horas</strong> de trabajo manual por proyecto.
                        </p>
                    </div>
                </motion.div>

                {/* ===== CATÁLOGO DE OPERACIONES ===== */}
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    style={{ maxWidth: '1140px', margin: '0 auto 50px', padding: '32px 28px', borderRadius: '24px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)' }}
                >
                    <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                        <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#00f2ff', letterSpacing: '2px', marginBottom: '8px' }}>36 MÓDULOS DE ANÁLISIS</div>
                        <h3 style={{ fontFamily: "'Outfit'", fontSize: '1.3rem', fontWeight: 900, margin: 0 }}>Catálogo Completo de <span style={{ color: '#00f2ff' }}>Operaciones</span></h3>
                        <p style={{ fontSize: '0.75rem', color: '#555', marginTop: '8px' }}>Cada módulo ha sido validado con datos reales de campo. Sin IA generativa — solo algoritmos petrofísicos comprobados.</p>
                    </div>

                    {[
                        {
                            cat: '📂 GESTIÓN DE DATOS', color: '#4ade80', items: [
                                { name: 'Carga LAS 2.0', desc: 'Parser robusto de archivos .LAS con detección automática de curvas, metadatos y profundidades.' },
                                { name: 'Normalización de Curvas', desc: 'Aliasing inteligente: GR, SP, NPHI, RHOB, DT, ILD, ILS, CALI → nombres estándar API.' },
                                { name: 'Estandarización de Unidades', desc: 'Convierte NPHI (% → v/v), RHOB (kg/m³ → g/cm³), DT (μs/m → μs/ft) automáticamente.' },
                            ]
                        },
                        {
                            cat: '🔬 PETROFÍSICA', color: '#00f2ff', items: [
                                { name: 'Volumen de Arcilla (Vsh)', desc: 'Cálculo de Vsh usando GR con método Larionov para rocas terciarias. Clasifica arena/lutita.' },
                                { name: 'Porosidad Efectiva (PHI)', desc: 'Porosidad con corrección por arcillosidad: PHI = PHIT × (1 - Vsh). Usa Density-Neutron o Sonic.' },
                                { name: 'Saturación de Agua — Archie', desc: 'Modelo clásico: Sw = (a × Rw / (Rt × φ^m))^(1/n). Para arenas limpias con porosidad intergranular.' },
                                { name: 'Saturación de Agua — Simandoux', desc: 'Modelo para arenas arcillosas: incluye efecto de conductividad de la arcilla sobre Rt.' },
                                { name: 'Permeabilidad — Timur-Coates', desc: 'K = C × φ^a × (FFI/BVI)^b. Modelo clásico NMR-calibrado para rocas clásticas.' },
                                { name: 'Permeabilidad — Log-Linear', desc: 'Regresión log(K) = a + b×φ. Relación empírica poro-perm calibrada con datos de núcleo.' },
                                { name: 'Permeabilidad — Morris-Biggs', desc: 'K = 62,500 × φ³ × Swirr. Alternativa rápida para arenas cuando no hay datos NMR.' },
                                { name: 'Crossplot NPHI-RHOB', desc: 'Scatter NPHI vs RHOB con overlays de litología (arena, caliza, dolomita) y detección de gas.', pending: true },
                            ]
                        },
                        {
                            cat: '🏗️ RESERVORIO', color: '#fbbf24', items: [
                                { name: 'Detección de Pay Zones', desc: 'Identifica zonas prospectivas donde PHI > 8%, Sw < 50%, Vsh < 40% con espesor neto.' },
                                { name: 'RQI Radar — 5 Ejes', desc: 'Índice de calidad de roca: PHI, Perm, Pay, Sw, Vsh en gráfico radar para ranking de zonas.' },
                            ]
                        },
                        {
                            cat: '🤖 MACHINE LEARNING', color: '#c084fc', items: [
                                { name: 'PCA (Componentes Principales)', desc: 'Reduce dimensionalidad de 5+ curvas a 3 componentes. Muestra varianza y loadings por curva.' },
                                { name: 'Electrofacies — PCA + K-Means', desc: 'Clasifica litofacies automáticamente: Arena Limpia, Arena Arcillosa, Lutita, Carbonato/Tight.' },
                            ]
                        },
                        {
                            cat: '🌍 GEOLOGÍA & GEOFÍSICA', color: '#f472b6', items: [
                                { name: 'Litho-Scanner 3D', desc: 'Cubo volumétrico con distribución litológica en profundidad. Visualización 3D interactiva.' },
                                { name: 'Impedancia Acústica', desc: 'AI = Vp × ρ. Perfil de impedancia para calibración de sísmica y AVO.' },
                                { name: 'Coeficientes de Reflexión', desc: 'RC = (AI₂ - AI₁) / (AI₂ + AI₁). Muestra interfaces de contraste acústico.' },
                                { name: 'Ondícula Ricker', desc: 'Wavelet sintética con frecuencia dominante configurable (25 Hz default).' },
                                { name: 'Sismograma Sintético', desc: 'Convolución RC × Ricker. Genera traza sintética para comparar con sísmica real.' },
                                { name: 'Well Tie (DTW)', desc: 'Dynamic Time Warping para amarre pozo-sísmica. Requiere datos de sísmica real.', pending: true },
                                { name: 'DLS — Dog-Leg Severity', desc: 'Calcula severidad de cambio de rumbo en trayectoria. Clasifica riesgo de perforación.' },
                            ]
                        },
                        {
                            cat: '⛽ PRODUCCIÓN', color: '#fb923c', items: [
                                { name: 'Análisis Nodal (IPR/VLP)', desc: 'Intersección de curvas de influjo (Vogel) y salida vertical. Calcula AOF y punto óptimo.' },
                                { name: 'Arps — Declinación Exponencial', desc: 'Q(t) = Qi × e^(-Di×t). Modelo conservador de pronóstico de producción a 10 años.' },
                                { name: 'Arps — Declinación Hiperbólica', desc: 'Q(t) = Qi / (1+b·Di·t)^(1/b). Modelo más realista con factor de curvatura b.' },
                                { name: 'OOIP — Petróleo Original en Sitio', desc: 'OOIP = 7,758 × A × h × φ × (1-Sw) / Bo. Fórmula API estándar con desglose completo.' },
                            ]
                        },
                        {
                            cat: '📊 ESTADÍSTICA', color: '#38bdf8', items: [
                                { name: 'Histogramas de Distribución', desc: 'Distribución estadística de cada curva con bins automáticos y métricas (media, σ, P10/P90).' },
                                { name: 'Correlación de Pearson', desc: 'Matriz de correlación entre todas las curvas. Identifica dependencias lineales fuertes.' },
                                { name: '4D Bubble Plot', desc: 'Scatter 3D interactivo: 3 curvas en ejes + 1 curva como tamaño de burbuja + color por facies.' },
                            ]
                        },
                        {
                            cat: '📤 EXPORTACIÓN', color: '#a3e635', items: [
                                { name: 'PDF Técnico', desc: 'Reporte completo con todos los gráficos, KPIs y tablas. Solo incluye módulos del plan activo.' },
                                { name: 'HTML Responsivo', desc: 'Dashboard HTML con gráficos interactivos (Plotly). Para visualización web sin servidor.' },
                                { name: 'CSV', desc: 'Tabla completa de datos procesados para análisis en Excel, Python o MATLAB.' },
                                { name: 'LAS 2.0', desc: 'Re-exportación del archivo procesado con curvas calculadas (PHI, SW, PERM, Facies).' },
                            ]
                        },
                    ].map((section, si) => (
                        <div key={si} style={{ marginBottom: si < 7 ? '24px' : 0 }}>
                            <div style={{ fontSize: '0.65rem', fontWeight: 800, color: section.color, letterSpacing: '1.5px', marginBottom: '12px', paddingBottom: '6px', borderBottom: `1px solid ${section.color}22` }}>{section.cat}</div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '8px' }}>
                                {section.items.map((item, ii) => (
                                    <div key={ii} style={{ padding: '10px 14px', borderRadius: '10px', background: item.pending ? 'rgba(255,255,255,0.005)' : 'rgba(255,255,255,0.015)', border: `1px solid ${item.pending ? 'rgba(255,255,255,0.03)' : section.color + '15'}`, opacity: item.pending ? 0.6 : 1, display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: item.pending ? '#666' : section.color, marginTop: '6px', flexShrink: 0 }} />
                                        <div>
                                            <div style={{ fontSize: '0.73rem', fontWeight: 700, color: item.pending ? '#666' : '#ddd', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                {item.name}
                                                {item.pending && <span style={{ fontSize: '0.55rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(251,191,36,0.1)', color: '#fbbf24' }}>Próximamente</span>}
                                            </div>
                                            <div style={{ fontSize: '0.66rem', color: '#666', lineHeight: 1.5, marginTop: '2px' }}>{item.desc}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </motion.div>

                {/* ===== SaaS Plans Grid ===== */}
                <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '20px', maxWidth: '1140px', margin: '0 auto 60px',
                }}>
                    {/* Plan Professional */}
                    <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0 }}
                        style={{ padding: '32px 26px', borderRadius: '24px', background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.06)', display: 'flex', flexDirection: 'column' }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(0,242,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><User size={18} color="#00f2ff" /></div>
                            <div>
                                <div style={{ fontSize: '0.65rem', color: '#555', fontWeight: 700, letterSpacing: '1px' }}>SUSCRIPCIÓN</div>
                                <div style={{ fontSize: '1rem', fontWeight: 800 }}>Professional</div>
                            </div>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: '#666', lineHeight: 1.6, marginBottom: '16px' }}>Para consultores independientes y freelancers de petrofísica.</p>
                        <div style={{ marginBottom: '16px' }}>
                            <span style={{ fontSize: '2.2rem', fontWeight: 900, fontFamily: "'Outfit'" }}>$99</span>
                            <span style={{ fontSize: '0.8rem', color: '#555' }}> USD / mes</span>
                            <div style={{ fontSize: '0.7rem', color: '#444', marginTop: '4px' }}>o $990 USD / año (2 meses gratis)</div>
                        </div>
                        {/* Quota badge */}
                        <div style={{ padding: '8px 14px', borderRadius: '10px', background: 'rgba(0,242,255,0.04)', border: '1px solid rgba(0,242,255,0.08)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Database size={13} color="#00f2ff" />
                            <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}><strong style={{ color: '#00f2ff' }}>5 pozos/mes</strong> · máx 2 por día · 1 usuario</span>
                        </div>
                        {/* Included modules */}
                        <div style={{ fontSize: '0.6rem', fontWeight: 800, color: '#4ade80', letterSpacing: '1px', marginBottom: '8px' }}>✓ MÓDULOS INCLUIDOS</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '16px' }}>
                            {['Carga LAS + Normalización + QC', 'Vsh · PHI · SW (Archie)', 'Detección de Pay Zones', 'Histogramas + Correlación Pearson', 'Exportación PDF / CSV (solo módulos del plan)', 'Soporte por email (48h)'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                                    <Check size={13} color="#4ade80" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.72rem', color: '#999' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                        {/* Locked modules */}
                        <div style={{ fontSize: '0.6rem', fontWeight: 800, color: '#ef4444', letterSpacing: '1px', marginBottom: '8px' }}>🔒 REQUIERE CORPORATE O SUPERIOR</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '20px', opacity: 0.5 }}>
                            {['SW Simandoux · 3 Modelos de Permeabilidad', 'Electrofacies PCA + K-Means', 'Geofísica Sintética · RQI Radar', 'Análisis Nodal · Arps Decline · OOIP'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                                    <Lock size={12} color="#ef4444" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.7rem', color: '#555' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                        <button onClick={triggerFileInput} style={{ width: '100%', padding: '13px', borderRadius: '12px', background: 'transparent', color: '#00f2ff', fontWeight: 800, fontSize: '0.8rem', border: '1px solid rgba(0,242,255,0.2)', cursor: 'pointer', transition: 'all 0.3s', marginTop: 'auto' }}>Comenzar Ahora</button>
                    </motion.div>

                    {/* Plan Corporate (POPULAR) */}
                    <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
                        style={{ padding: '32px 26px', borderRadius: '24px', position: 'relative', background: 'linear-gradient(180deg, rgba(0,242,255,0.04) 0%, rgba(0,242,255,0.01) 100%)', border: '1px solid rgba(0,242,255,0.15)', display: 'flex', flexDirection: 'column', boxShadow: '0 0 40px rgba(0,242,255,0.06)' }}
                    >
                        <div style={{ position: 'absolute', top: '-12px', right: '20px', padding: '5px 16px', borderRadius: '50px', background: 'linear-gradient(135deg, #00f2ff, #0088ff)', fontSize: '0.6rem', fontWeight: 900, color: '#000', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '4px' }}><Star size={10} /> MÁS POPULAR</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(0,242,255,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Building2 size={18} color="#00f2ff" /></div>
                            <div>
                                <div style={{ fontSize: '0.65rem', color: '#00f2ff', fontWeight: 700, letterSpacing: '1px' }}>SUSCRIPCIÓN</div>
                                <div style={{ fontSize: '1rem', fontWeight: 800 }}>Corporate</div>
                            </div>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: '#666', lineHeight: 1.6, marginBottom: '16px' }}>Para equipos de geociencias con análisis avanzados y volumen medio.</p>
                        <div style={{ marginBottom: '16px' }}>
                            <span style={{ fontSize: '2.2rem', fontWeight: 900, fontFamily: "'Outfit'", color: '#00f2ff' }}>$299</span>
                            <span style={{ fontSize: '0.8rem', color: '#555' }}> USD / mes</span>
                            <div style={{ fontSize: '0.7rem', color: '#444', marginTop: '4px' }}>o $2,990 USD / año (2 meses gratis)</div>
                        </div>
                        <div style={{ padding: '8px 14px', borderRadius: '10px', background: 'rgba(0,242,255,0.06)', border: '1px solid rgba(0,242,255,0.12)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Database size={13} color="#00f2ff" />
                            <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}><strong style={{ color: '#00f2ff' }}>30 pozos/mes</strong> · máx 5 por día · 5 usuarios</span>
                        </div>
                        <div style={{ fontSize: '0.6rem', fontWeight: 800, color: '#4ade80', letterSpacing: '1px', marginBottom: '8px' }}>✓ TODO LO DE PROFESSIONAL +</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', marginBottom: '16px' }}>
                            {['SW Simandoux (arenas arcillosas)', 'Permeabilidad: Timur-Coates + Log-Linear + Morris-Biggs', 'Electrofacies con PCA + K-Means', 'Geofísica Sintética (Impedancia + Sismograma)', 'RQI Radar 5 Ejes · 4D Bubble Plot', 'DLS Drilling Risk · Crossplot NPHI-RHOB', 'Reportes PDF con logo de la empresa', 'Soporte prioritario (24h) + Asesoría 1h/mes'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                                    <Check size={13} color="#00f2ff" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.72rem', color: '#ccc' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                        <div style={{ fontSize: '0.6rem', fontWeight: 800, color: '#ef4444', letterSpacing: '1px', marginBottom: '8px' }}>🔒 REQUIERE ENTERPRISE</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '20px', opacity: 0.5 }}>
                            {['Litho-Scanner 3D · Análisis Nodal IPR/VLP', 'Arps Decline (Exp + Hyp) · OOIP Completo', 'Reportes White-Label · Multi-Well'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                                    <Lock size={12} color="#ef4444" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.7rem', color: '#555' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                        <button onClick={triggerFileInput} style={{ width: '100%', padding: '14px', borderRadius: '12px', background: 'linear-gradient(135deg, #00f2ff, #0088ff)', color: '#000', fontWeight: 800, fontSize: '0.8rem', border: 'none', cursor: 'pointer', boxShadow: '0 0 25px rgba(0,242,255,0.25)', transition: 'all 0.3s', marginTop: 'auto' }}>Solicitar Acceso</button>
                    </motion.div>

                    {/* Plan Enterprise */}
                    <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}
                        style={{ padding: '32px 26px', borderRadius: '24px', background: 'linear-gradient(180deg, rgba(167,139,250,0.03) 0%, rgba(167,139,250,0.01) 100%)', border: '1px solid rgba(167,139,250,0.1)', display: 'flex', flexDirection: 'column' }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(167,139,250,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Crown size={18} color="#a78bfa" /></div>
                            <div>
                                <div style={{ fontSize: '0.65rem', color: '#a78bfa', fontWeight: 700, letterSpacing: '1px' }}>ANUAL / DEDICADO</div>
                                <div style={{ fontSize: '1rem', fontWeight: 800 }}>Enterprise</div>
                            </div>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: '#666', lineHeight: 1.6, marginBottom: '16px' }}>Acceso total. Todos los módulos, sin límites, soporte dedicado.</p>
                        <div style={{ marginBottom: '16px' }}>
                            <span style={{ fontSize: '2.2rem', fontWeight: 900, fontFamily: "'Outfit'", color: '#a78bfa' }}>$4,900</span>
                            <span style={{ fontSize: '0.8rem', color: '#555' }}> USD / año</span>
                            <div style={{ fontSize: '0.7rem', color: '#444', marginTop: '4px' }}>~$408/mes · Descuento contrato multi-año</div>
                        </div>
                        <div style={{ padding: '8px 14px', borderRadius: '10px', background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.1)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Database size={13} color="#a78bfa" />
                            <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}><strong style={{ color: '#a78bfa' }}>Pozos ilimitados</strong> · sin restricción · 15 usuarios</span>
                        </div>
                        <div style={{ fontSize: '0.6rem', fontWeight: 800, color: '#4ade80', letterSpacing: '1px', marginBottom: '8px' }}>✓ ACCESO TOTAL — 36 MÓDULOS</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', flex: 1, marginBottom: '20px' }}>
                            {['Todo lo de Corporate incluido', 'Litho-Scanner 3D (Cubo Volumétrico)', 'Análisis Nodal Avanzado (IPR/VLP)', 'Arps Decline: Exponencial + Hiperbólica', 'OOIP Completo con desglose de parámetros', 'Multi-Well Correlation (próximamente)', 'Reportes PDF White-Label personalizados', 'Soporte WhatsApp/email (<12h)', 'Asesoría técnica quincenal (1h videollamada)', 'Capacitación remota (2 sesiones incluidas)', 'Acceso anticipado a versiones beta'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                                    <Check size={13} color="#a78bfa" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.72rem', color: '#999' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                        <button style={{ width: '100%', padding: '13px', borderRadius: '12px', background: 'transparent', color: '#a78bfa', fontWeight: 800, fontSize: '0.8rem', border: '1px solid rgba(167,139,250,0.2)', cursor: 'pointer', transition: 'all 0.3s', marginTop: 'auto' }}>Contactar Ventas</button>
                    </motion.div>
                </div>

                {/* ===== Additional Models: Pay-per-Well & Desktop License ===== */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', maxWidth: '1140px', margin: '0 auto 40px' }}>
                    {/* Pay-per-Well */}
                    <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                        style={{ padding: '28px', borderRadius: '20px', background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(251,191,36,0.08)' }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(251,191,36,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><BadgeDollarSign size={18} color="#fbbf24" /></div>
                            <h3 style={{ fontSize: '0.95rem', fontWeight: 800 }}>Pay-per-Well</h3>
                            <span style={{ marginLeft: 'auto', padding: '3px 12px', borderRadius: '50px', background: 'rgba(251,191,36,0.08)', fontSize: '0.6rem', color: '#fbbf24', fontWeight: 800 }}>FLEXIBLE</span>
                        </div>
                        <p style={{ fontSize: '0.78rem', color: '#666', lineHeight: 1.6, marginBottom: '18px' }}>Sin suscripción — paga solo por lo que procesas. Módulos nivel Corporate incluidos.</p>
                        <div style={{ padding: '16px 20px', borderRadius: '14px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.04)', display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '16px' }}>
                            <span style={{ fontSize: '1.6rem', fontWeight: 900, fontFamily: "'Outfit'", color: '#fbbf24' }}>$25</span>
                            <span style={{ fontSize: '0.75rem', color: '#666' }}>USD por pozo procesado</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {['Reporte completo con módulos Corporate', 'Petrofísica + Geofísica + Electrofacies', 'Descarga PDF + CSV + HTML', 'Paquetes: 10 pozos ($200) / 50 pozos ($900)'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Check size={13} color="#fbbf24" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.72rem', color: '#888' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>

                    {/* Desktop License */}
                    <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
                        style={{ padding: '28px', borderRadius: '20px', background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(244,114,182,0.08)' }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(244,114,182,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><MonitorDown size={18} color="#f472b6" /></div>
                            <h3 style={{ fontSize: '0.95rem', fontWeight: 800 }}>Licencia Desktop</h3>
                            <span style={{ marginLeft: 'auto', padding: '3px 12px', borderRadius: '50px', background: 'rgba(244,114,182,0.08)', fontSize: '0.6rem', color: '#f472b6', fontWeight: 800 }}>PERPETUA</span>
                        </div>
                        <p style={{ fontSize: '0.78rem', color: '#666', lineHeight: 1.6, marginBottom: '18px' }}>Versión instalable (PyQt6). Sin internet. Todos los 36 módulos incluidos.</p>
                        <div style={{ padding: '16px 20px', borderRadius: '14px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.04)', display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '6px' }}>
                            <span style={{ fontSize: '1.6rem', fontWeight: 900, fontFamily: "'Outfit'", color: '#f472b6' }}>$14,900</span>
                            <span style={{ fontSize: '0.75rem', color: '#666' }}>USD pago único / puesto</span>
                        </div>
                        <div style={{ padding: '10px 20px', borderRadius: '10px', marginBottom: '16px', background: 'rgba(244,114,182,0.03)', border: '1px solid rgba(244,114,182,0.06)' }}>
                            <span style={{ fontSize: '0.68rem', color: '#f472b6', fontWeight: 700 }}>+ Mantenimiento anual: 18% ($2,682/año)</span>
                            <span style={{ fontSize: '0.65rem', color: '#666', display: 'block' }}>Incluye actualizaciones, bugfixes y soporte técnico</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {['Instalación local (Windows/Mac/Linux)', 'Sin conexión requerida post-instalación', '100% de los 36 módulos (nivel Enterprise)', 'Actualizaciones por 1 año incluidas', 'Licencia transferible dentro de la empresa'].map((f, i) => (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Check size={13} color="#f472b6" style={{ flexShrink: 0 }} />
                                    <span style={{ fontSize: '0.72rem', color: '#888' }}>{f}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                </div>

                {/* Comparison table — Module Access by Tier */}
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    style={{ maxWidth: '1140px', margin: '0 auto', padding: '28px', borderRadius: '20px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', overflow: 'auto' }}
                >
                    <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#555', letterSpacing: '1.5px', marginBottom: '18px', textAlign: 'center' }}>ACCESO A MÓDULOS POR PLAN</div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                                <th style={{ textAlign: 'left', padding: '10px 12px', color: '#666', fontWeight: 700 }}>Módulo / Característica</th>
                                <th style={{ textAlign: 'center', padding: '10px 8px', color: '#fff', fontWeight: 800, fontSize: '0.65rem' }}>Professional<br /><span style={{ color: '#00f2ff', fontSize: '0.6rem' }}>$99/mes</span></th>
                                <th style={{ textAlign: 'center', padding: '10px 8px', color: '#00f2ff', fontWeight: 800, fontSize: '0.65rem' }}>Corporate<br /><span style={{ fontSize: '0.6rem' }}>$299/mes</span></th>
                                <th style={{ textAlign: 'center', padding: '10px 8px', color: '#a78bfa', fontWeight: 800, fontSize: '0.65rem' }}>Enterprise<br /><span style={{ fontSize: '0.6rem' }}>$4,900/año</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                ['Pozos por mes', '5', '30', '♾️ Ilimitado'],
                                ['Usuarios', '1', '5', '15'],
                                ['Carga LAS + Normalización + QC', '✓', '✓', '✓'],
                                ['Vsh · PHI · SW Archie', '✓', '✓', '✓'],
                                ['Detección de Pay Zones', '✓', '✓', '✓'],
                                ['Histogramas + Correlación', '✓', '✓', '✓'],
                                ['SW Simandoux', '🔒', '✓', '✓'],
                                ['3 Modelos Permeabilidad', '🔒', '✓', '✓'],
                                ['PCA + K-Means Electrofacies', '🔒', '✓', '✓'],
                                ['Geofísica Sintética', '🔒', '✓', '✓'],
                                ['RQI Radar · DLS · 4D Bubble', '🔒', '✓', '✓'],
                                ['Crossplot NPHI-RHOB', '🔒', '✓', '✓'],
                                ['Litho-Scanner 3D', '🔒', '🔒', '✓'],
                                ['Análisis Nodal IPR/VLP', '🔒', '🔒', '✓'],
                                ['Arps Decline (Exp + Hyp)', '🔒', '🔒', '✓'],
                                ['OOIP Completo', '🔒', '🔒', '✓'],
                                ['Multi-Well Correlation', '🔒', '🔒', '✓'],
                                ['PDF / CSV Export', '✓ Básico', '✓ Con logo', '✓ White-label'],
                                ['Soporte', 'Email 48h', 'Email 24h', 'WhatsApp <12h'],
                            ].map(([feat, pro, corp, ent], i) => (
                                <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                    <td style={{ padding: '8px 12px', color: '#999' }}>{feat}</td>
                                    <td style={{ padding: '8px 8px', textAlign: 'center', color: pro.includes('🔒') ? '#ef4444' : '#4ade80', fontSize: '0.7rem' }}>{pro}</td>
                                    <td style={{ padding: '8px 8px', textAlign: 'center', color: corp.includes('🔒') ? '#ef4444' : '#00f2ff', fontWeight: 600, fontSize: '0.7rem' }}>{corp}</td>
                                    <td style={{ padding: '8px 8px', textAlign: 'center', color: '#a78bfa', fontSize: '0.7rem' }}>{ent}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </motion.div>

                {/* CTA Bottom */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                    style={{ textAlign: 'center', marginTop: '50px' }}
                >
                    <p style={{ fontSize: '0.8rem', color: '#555', marginBottom: '20px' }}>
                        ¿Necesitas un plan personalizado? <strong style={{ color: '#fff' }}>Contacta a nuestro equipo de ventas.</strong>
                    </p>
                    <button onClick={triggerFileInput} style={{
                        padding: '15px 40px', borderRadius: '50px',
                        background: 'linear-gradient(135deg, #00f2ff, #0088ff)', color: '#000',
                        fontWeight: 800, fontSize: '0.85rem', border: 'none', cursor: 'pointer',
                        boxShadow: '0 0 30px rgba(0,242,255,0.25)',
                        display: 'inline-flex', alignItems: 'center', gap: '10px',
                    }}>
                        Probar DataTerra Gratis <ArrowRight size={16} />
                    </button>
                    <p style={{ fontSize: '0.65rem', color: '#333', marginTop: '10px' }}>Sin tarjeta de crédito • Prueba completa con tu propio .LAS</p>
                </motion.div>
            </section>

            {/* ====== FOOTER ====== */}
            <footer style={{
                padding: '40px 5%', borderTop: '1px solid rgba(255,255,255,0.03)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '15px',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontFamily: "'Outfit'", fontWeight: 900, fontSize: '0.9rem' }}>
                        DATA<span style={{ color: '#00f2ff' }}>TERRA</span>
                    </span>
                    <span style={{ fontSize: '0.65rem', color: '#333' }}>• Subsurface Intelligence Systems</span>
                </div>
                <p style={{ fontSize: '0.65rem', color: '#333' }}>
                    © 2025 • 100% datos reales de tu archivo .LAS • Procesado por Python • Sin IA generativa
                </p>
            </footer>

            {/* ====== Global animations ====== */}
            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                button:hover { transform: translateY(-1px); }
                a:hover { color: #00f2ff !important; }
            `}</style>
        </div>
    );
}

export default App;
