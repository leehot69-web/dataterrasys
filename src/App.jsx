import React, { useState } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
    ChevronRight,
    Database,
    Zap,
    ShieldCheck,
    Globe,
    BarChart3,
    Cpu,
    Layers,
    Mail,
    Linkedin,
    Twitter,
    Languages
} from 'lucide-react';
import './index.css';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import WellLogVisualization from './pages/WellLogVisualization';

const translations = {
    es: {
        nav: { platform: 'Plataforma', ai: 'Núcleo IA', enterprise: 'Empresarial', launch: 'INICIAR OS' },
        hero: {
            protocol: 'PROTOCOLO GENESYS V7.0',
            title1: 'EXTRAYENDO',
            title2: 'INTELIGENCIA',
            subtitle: 'Analítica de subsuelo de próxima generación impulsada por IA agentica. Petrofísica en tiempo real, visión sísmica e ingeniería de yacimientos a escala.',
            btnEnter: 'ENTRAR A LA PLATAFORMA',
            btnDemo: 'VER DEMO TÉCNICA'
        },
        features: {
            header: 'MÓDULOS DE ANÁLISIS',
            subheader: 'Arquitectura técnica diseñada para la toma de decisiones en tiempo real.',
            f1_t: 'Dashboard Ejecutivo',
            f1_d: 'Visualización global de KPIs, salud de activos y estado HSE del proyecto con indicadores tipo Gauge.',
            f2_t: 'Geología y Sísmica',
            f2_d: 'Interpretación estructural, generación de sismogramas sintéticos y mapeo de horizontes técnicos.',
            f3_t: 'Evaluación de Formaciones',
            f3_d: 'Análisis petrofísico avanzado, visualización de registros LAS y procesamiento de imagen de pozo.',
            f4_t: 'Integridad de Datos',
            f4_d: 'Auditoría técnica automática de curvas, control de calidad SEG y validación de estándares industriales.',
            f5_t: 'Ingeniería de Yacimientos',
            f5_d: 'Simulación de producción, cálculo de reservas y análisis económico de flujo de caja (Cash Flow).',
            f6_t: 'Generador de Reportes',
            f6_d: 'Exportación instantánea de informes técnicos profesionales en PDF y HTML con data real procesada.'
        },
        footer: {
            slogan: 'Pioneros en el futuro de la exploración digital del subsuelo. Diseñado para exploradores, por genios.',
            contact: 'Contacto',
            newsletter: 'Boletín',
            allRights: 'TODOS LOS SISTEMAS OPERATIVOS.'
        }
    },
    en: {
        nav: { platform: 'Platform', ai: 'AI Core', enterprise: 'Enterprise', launch: 'LAUNCH OS' },
        hero: {
            protocol: 'GENESYS PROTOCOL V7.0',
            title1: 'UNEARTHING',
            title2: 'INTELLIGENCE',
            subtitle: 'Next-generation subsurface analytics powered by agentic AI. Real-time petrophysics, seismic vision, and reservoir engineering at scale.',
            btnEnter: 'ENTER PLATFORM',
            btnDemo: 'WATCH TECH DEMO'
        },
        features: {
            header: 'ANALYSIS MODULES',
            subheader: 'Technical architecture designed for real-time decision-making.',
            f1_t: 'Executive Dashboard',
            f1_d: 'Global visualization of KPIs, asset health, and project HSE status with professional Gauge indicators.',
            f2_t: 'Geology & Seismic',
            f2_d: 'Structural interpretation, synthetic seismogram generation, and technical horizon mapping.',
            f3_t: 'Formation Evaluation',
            f3_d: 'Advanced petrophysical analysis, LAS log visualization, and borehole imagery processing.',
            f4_t: 'Data Integrity',
            f4_d: 'Automatic technical audit of curves, SEG quality control, and industrial standards validation.',
            f5_t: 'Reservoir Engineering',
            f5_d: 'Production simulation, reserves calculation, and economic cash flow analysis (Cash Flow).',
            f6_t: 'Report Generator',
            f6_d: 'Instant export of professional technical reports in PDF and HTML with real processed data.'
        },
        footer: {
            slogan: 'Pioneering the future of digital subsurface exploration. Engineered for explorers, by geniuses.',
            contact: 'Contact',
            newsletter: 'Newsletter',
            allRights: 'ALL SYSTEMS OPERATIONAL.'
        }
    }
};

const Navbar = ({ lang, setLang }) => {
    const t = translations[lang].nav;
    return (
        <nav className="navbar glass">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div className="logo-icon">D</div>
                <span style={{ fontSize: '1.5rem', fontWeight: 900, letterSpacing: '-0.05em' }}>
                    DATA<span style={{ color: 'var(--primary)' }}>TERRA</span>
                </span>
            </div>
            <div className="nav-links">
                <a href="#platform">{t.platform}</a>
                <a href="#ai">{t.ai}</a>
                <a href="#about">{t.enterprise}</a>
                <button
                    onClick={() => setLang(lang === 'es' ? 'en' : 'es')}
                    className="glass"
                    style={{
                        padding: '2px 10px',
                        borderRadius: '5px',
                        fontSize: '0.7rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        color: 'white',
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}
                >
                    <Languages size={14} /> {lang.toUpperCase()}
                </button>
            </div>
            <button
                onClick={() => window.location.href = 'https://dataterraapp.streamlit.app/'}
                className="launch-btn"
            >
                {t.launch}
            </button>
        </nav>
    );
};

const Hero = ({ lang, setView }) => {
    const t = translations[lang].hero;
    const { scrollY } = useScroll();
    const y1 = useTransform(scrollY, [0, 500], [0, 200]);
    const opacity = useTransform(scrollY, [0, 300], [1, 0]);

    return (
        <section className="hero responsive-hero" style={{ padding: '0 8%', textAlign: 'left', alignItems: 'center', display: 'flex', minHeight: '100vh', paddingTop: '80px' }}>
            <div className="hero-bg">
                <div className="hero-bg-overlay" />
                <video
                    autoPlay
                    muted
                    loop
                    playsInline
                    poster="https://images.unsplash.com/photo-1639322537228-f710d846310a?auto=format&fit=crop&q=80"
                    style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        filter: 'grayscale(1) brightness(0.6)'
                    }}
                >
                    <source src="/assets/hero_video.mp4" type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>

            <div className="hero-container" style={{
                display: 'flex',
                width: '100%',
                zIndex: 10,
                gap: '4rem'
            }}>
                {/* LEFT COLUMN: TEXT */}
                <motion.div style={{ y: y1, opacity, flex: 1.2 }}>
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        style={{
                            display: 'inline-block',
                            padding: '0.25rem 1rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 'bold',
                            letterSpacing: '0.2em',
                            marginBottom: '1.5rem',
                            border: '1px solid rgba(0, 242, 255, 0.3)',
                            color: 'var(--primary)'
                        }}
                        className="glass"
                    >
                        {t.protocol}
                    </motion.div>

                    <h1 className="hero-title" style={{ textAlign: 'left', margin: 0 }}>
                        <span style={{ fontSize: 'clamp(4rem, 10vw, 8rem)', letterSpacing: '-0.07em', display: 'block' }}>
                            D<span style={{ color: 'var(--primary)' }}>TERRA</span>
                        </span>
                        <span style={{ fontSize: 'clamp(1.5rem, 3vw, 2.5rem)', opacity: 0.8, display: 'block', marginTop: '0.5rem', fontWeight: 400 }}>
                            {t.title1} <span className="neon-text" style={{ fontWeight: 800 }}>{t.title2}</span>
                        </span>
                    </h1>

                    <p className="hero-subtitle" style={{ textAlign: 'left', margin: '2rem 0', maxWidth: '35rem' }}>
                        {t.subtitle}
                    </p>

                    <div className="btn-group" style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <button
                            onClick={() => window.location.href = 'https://dataterraapp.streamlit.app/'}
                            className="primary-btn"
                        >
                            {t.btnEnter} <ChevronRight />
                        </button>
                        <button
                            className="secondary-btn"
                            onClick={() => setView('dashboard')}
                        >
                            {t.btnDemo}
                        </button>
                    </div>
                </motion.div>

                {/* RIGHT COLUMN: VISUAL WITH FADED EDGES */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.8, x: 50 }}
                    animate={{ opacity: 1, scale: 1, x: 0 }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                    className="hero-visual"
                    style={{
                        flex: 1,
                        position: 'relative'
                    }}
                >
                    <div style={{
                        width: '100%',
                        maxWidth: '800px',
                        height: '550px',
                        borderRadius: '40px',
                        overflow: 'hidden',
                        position: 'relative',
                        background: 'transparent',
                        boxShadow: '0 25px 70px rgba(0,0,0,0.5)',
                        maskImage: 'radial-gradient(ellipse at center, black 50%, transparent 100%)',
                        WebkitMaskImage: 'radial-gradient(ellipse at center, black 50%, transparent 100%)',
                    }}>
                        <video
                            autoPlay
                            muted
                            loop
                            playsInline
                            style={{
                                width: '100%',
                                height: '100%',
                                objectFit: 'cover',
                                opacity: 0.9
                            }}
                        >
                            <source src="/assets/side_viz.mp4" type="video/mp4" />
                            Your browser does not support the video tag.
                        </video>
                    </div>

                    <div className="glass" style={{
                        position: 'absolute',
                        bottom: '40px',
                        left: '0px',
                        padding: '15px 25px',
                        borderRadius: '15px',
                        fontSize: '0.8rem',
                        fontWeight: 'bold',
                        color: 'var(--primary)',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.3)'
                    }}>
                        <Zap size={16} style={{ marginBottom: '-3px', marginRight: '8px' }} />
                        REAL TIME ANALYSIS ACTIVE
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

const FeatureCard = ({ icon: Icon, title, desc }) => (
    <motion.div
        whileHover={{ y: -10 }}
        className="feature-card glass"
    >
        <div className="feature-icon-box">
            <Icon style={{ width: '32px', height: '32px', color: 'var(--primary)' }} />
        </div>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>{title}</h3>
        <p style={{ color: 'var(--text-dim)', lineHeight: 1.6 }}>{desc}</p>
    </motion.div>
);

const Features = ({ lang }) => {
    const t = translations[lang].features;
    return (
        <section id="platform" className="features-section">
            <div className="section-header">
                <h2>{t.header}</h2>
                <p style={{ color: '#64748b', fontSize: '1.25rem' }}>{t.subheader}</p>
            </div>

            <div className="features-grid">
                <FeatureCard icon={Cpu} title={t.f1_t} desc={t.f1_d} />
                <FeatureCard icon={Layers} title={t.f2_t} desc={t.f2_d} />
                <FeatureCard icon={ShieldCheck} title={t.f3_t} desc={t.f3_d} />
                <FeatureCard icon={BarChart3} title={t.f4_t} desc={t.f4_d} />
                <FeatureCard icon={Globe} title={t.f5_t} desc={t.f5_d} />
                <FeatureCard icon={Zap} title={t.f6_t} desc={t.f6_d} />
            </div>
        </section>
    );
}

const Footer = ({ lang }) => {
    const t = translations[lang].footer;
    return (
        <footer className="footer glass">
            <div className="footer-content">
                <div style={{ maxWidth: '400px' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, marginBottom: '1.5rem' }}>
                        DATA<span style={{ color: 'var(--primary)' }}>TERRA</span>
                    </div>
                    <p style={{ color: '#64748b', marginBottom: '2rem', lineHeight: 1.6 }}>
                        {t.slogan}
                    </p>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <div className="logo-icon glass" style={{ width: '40px', height: '40px' }}><Twitter /></div>
                        <div className="logo-icon glass" style={{ width: '40px', height: '40px' }}><Linkedin /></div>
                        <div className="logo-icon glass" style={{ width: '40px', height: '40px' }}><Mail /></div>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    <div>
                        <h4 style={{ fontWeight: 'bold', marginBottom: '1.5rem', color: 'var(--primary)' }}>{t.contact}</h4>
                        <p style={{ color: 'var(--text-dim)', marginBottom: '0.5rem' }}>dataterrasys@gmail.com</p>
                        <p style={{ color: 'var(--text-dim)' }}>Maracaibo, Venezuela</p>
                    </div>
                    <div>
                        <h4 style={{ fontWeight: 'bold', marginBottom: '1.5rem', color: 'var(--primary)' }}>{t.newsletter}</h4>
                        <div className="glass" style={{ display: 'flex', padding: '0.5rem', borderRadius: '1rem' }}>
                            <input type="text" placeholder="Email" style={{ background: 'transparent', border: 'none', outline: 'none', padding: '0 1rem', color: 'white', width: '100%' }} />
                            <button style={{ background: 'var(--primary)', border: 'none', padding: '0.5rem', borderRadius: '0.5rem', cursor: 'pointer' }}><ChevronRight style={{ width: '16px', height: '16px' }} /></button>
                        </div>
                    </div>
                </div>
            </div>
            <div style={{
                maxWidth: '80rem',
                margin: '5rem auto 0',
                paddingTop: '2rem',
                borderTop: '1px solid #1e293b',
                textAlign: 'center',
                fontSize: '0.875rem',
                color: '#475569'
            }}>
                © 2026 DATA TERRA DIGITAL SOLUTIONS. {t.allRights}
            </div>
        </footer>
    );
}

function App() {
    const [lang, setLang] = useState('es');
    const [view, setView] = useState('landing');
    const t = translations[lang];

    console.log("Current App View:", view);

    if (view === 'dashboard') {
        return (
            <div className="relative">
                <ExecutiveDashboard />
                <button
                    onClick={() => setView('logs')}
                    className="fixed bottom-24 right-4 bg-primary text-black p-4 rounded-full shadow-lg z-50 font-bold text-xs"
                >
                    LOGS VISUALIZER
                </button>
                <button
                    onClick={() => setView('landing')}
                    className="fixed top-2 right-4 bg-white/10 backdrop-blur-md text-white px-4 py-2 rounded-lg z-50 text-[10px] font-bold border border-white/10"
                >
                    BACK TO HOME
                </button>
            </div>
        );
    }

    if (view === 'logs') {
        return (
            <div className="relative">
                <WellLogVisualization />
                <button
                    onClick={() => setView('dashboard')}
                    className="fixed bottom-24 right-4 bg-primary text-black p-4 rounded-full shadow-lg z-50 font-bold text-xs"
                >
                    DASHBOARD
                </button>
                <button
                    onClick={() => setView('landing')}
                    className="fixed top-2 right-4 bg-white/10 backdrop-blur-md text-white px-4 py-2 rounded-lg z-50 text-[10px] font-bold border border-white/10"
                >
                    BACK TO HOME
                </button>
            </div>
        );
    }

    return (
        <div className="gradient-bg">
            <Navbar lang={lang} setLang={setLang} />
            <main>
                <Hero lang={lang} setView={setView} />
                <Features lang={lang} />
            </main>
            <Footer lang={lang} />
        </div>
    );
}

export default App;
