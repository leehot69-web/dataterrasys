import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Activity,
    Droplets,
    Zap,
    ShieldCheck,
    TrendingUp,
    Map as MapIcon,
    Search,
    Settings,
    Bell,
    Navigation,
    Thermometer,
    Wind
} from 'lucide-react';

const KPICard = ({ title, value, unit, trend, icon: Icon, color }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 backdrop-blur-xl border border-white/10 p-5 rounded-3xl"
    >
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-2xl bg-${color}/10 text-${color}`}>
                <Icon size={24} />
            </div>
            {trend && (
                <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${trend > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {trend > 0 ? '+' : ''}{trend}%
                </span>
            )}
        </div>
        <div className="space-y-1">
            <p className="text-white/40 text-[10px] uppercase tracking-widest font-bold">{title}</p>
            <div className="flex items-baseline gap-1">
                <h3 className="text-2xl font-black text-white">{value}</h3>
                <span className="text-xs text-white/30 font-bold">{unit}</span>
            </div>
        </div>
    </motion.div>
);

const GaugeIndicator = ({ label, value, color }) => (
    <div className="flex flex-col items-center gap-2">
        <div className="relative w-32 h-16 overflow-hidden">
            <div className="absolute top-0 left-0 w-32 h-32 border-[12px] border-white/5 rounded-full" />
            <motion.div
                initial={{ rotate: -90 }}
                animate={{ rotate: -90 + (value * 1.8) }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                className={`absolute top-0 left-0 w-32 h-32 border-[12px] border-${color} rounded-full`}
                style={{ clipPath: 'polygon(0 0, 100% 0, 100% 50%, 0 50%)', borderColor: color }}
            />
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-white font-black text-xl">
                {value}%
            </div>
        </div>
        <span className="text-[10px] font-black text-white/40 uppercase tracking-tighter">{label}</span>
    </div>
);

const ExecutiveDashboard = () => {
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    console.log("Loading ExecutiveDashboard component...");

    return (
        <div className="min-h-screen bg-[#050505] text-white p-4 font-sans overflow-hidden">
            {/* MOBILE STATUS BAR SIMULATION */}
            <div className="flex justify-between items-center px-4 py-2 mb-4 opacity-70">
                <span className="text-sm font-bold">
                    {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <div className="flex gap-2">
                    <Activity size={14} />
                    <Navigation size={14} />
                    <Zap size={14} />
                </div>
            </div>

            <div className="flex gap-6 h-[calc(100vh-80px)]">
                {/* SLIM SIDEBAR */}
                <div className="w-16 flex flex-col items-center gap-8 py-8 bg-white/5 rounded-full border border-white/10">
                    <div className="w-10 h-10 bg-cyan-400 rounded-2xl flex items-center justify-center text-black shadow-[0_0_20px_rgba(34,211,238,0.4)]">
                        <Zap size={20} />
                    </div>
                    {[MapIcon, Activity, Database, TrendingUp, ShieldCheck, Settings].map((Icon, i) => (
                        <motion.div
                            key={i}
                            whileTap={{ scale: 0.9 }}
                            className={`p-3 rounded-2xl ${i === 0 ? 'bg-white/10 text-cyan-400' : 'text-white/20'}`}
                        >
                            <Icon size={24} />
                        </motion.div>
                    ))}
                </div>

                {/* MAIN CONTENT */}
                <div className="flex-1 space-y-6 overflow-y-auto no-scrollbar pr-2">
                    {/* HEADER / COMMAND BAR */}
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-black tracking-tighter uppercase">Operations</h1>
                            <p className="text-xs font-bold text-cyan-400/80 tracking-[0.2em]">GENESYS NODE: VENEZUELA-EAST</p>
                        </div>
                        <div className="flex gap-3">
                            <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
                                <Search size={20} className="text-white/40" />
                            </div>
                            <div className="p-3 bg-white/5 rounded-2xl border border-white/10 relative">
                                <Bell size={20} className="text-white/40" />
                                <div className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-[#050505]" />
                            </div>
                        </div>
                    </div>

                    {/* ASSET NAV TABS */}
                    <div className="flex gap-6 border-b border-white/5 pb-2">
                        {['Regional Hub', 'Asset Control', 'HSE Analytics', 'AI Diagnostics'].map((tab, i) => (
                            <span key={tab} className={`text-[10px] font-black uppercase tracking-widest pb-2 cursor-pointer transition-all ${i === 0 ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-white/20'}`}>
                                {tab}
                            </span>
                        ))}
                    </div>

                    {/* KPI GRID */}
                    <div className="grid grid-cols-2 gap-4">
                        <KPICard title="Net Daily Prod" value="48,250" unit="BBL" trend={4.2} icon={Droplets} color="cyan-400" />
                        <KPICard title="Energy Output" value="12.4" unit="MWH" trend={-1.8} icon={Zap} color="orange-400" />
                        <KPICard title="System Integrity" value="99.9" unit="%" trend={0.1} icon={ShieldCheck} color="green-400" />
                        <KPICard title="MTD Revenue" value="2.8M" unit="USD" trend={12.5} icon={Activity} color="purple-400" />
                    </div>

                    {/* MAIN VISUAL: STYLIZED MAP */}
                    <div className="relative aspect-square rounded-[40px] overflow-hidden border border-white/10 group">
                        <div className="absolute inset-0 bg-cyan-950/20" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-full h-full bg-[radial-gradient(circle_at_center,rgba(34,211,238,0.15),transparent_70%)]" />
                            {/* STYLIZED GRID OVERLAY */}
                            <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
                        </div>

                        {/* MAP HUD ELEMENTS */}
                        <div className="absolute top-6 left-6 space-y-1">
                            <p className="text-[10px] font-black text-cyan-400 uppercase tracking-widest">Active Survey Area</p>
                            <h2 className="text-xl font-bold italic tracking-tighter">ORINOCO_BELT_SEC_7</h2>
                        </div>

                        <div className="absolute bottom-6 right-6 p-4 bg-black/80 backdrop-blur-md rounded-2xl border border-white/10 flex items-center gap-4">
                            <div className="text-right">
                                <p className="text-[8px] font-black text-white/30 uppercase">Depth</p>
                                <p className="text-sm font-black">12,450 FT</p>
                            </div>
                            <div className="w-[1px] h-8 bg-white/10" />
                            <div className="text-right">
                                <p className="text-[8px] font-black text-white/30 uppercase">Temp</p>
                                <p className="text-sm font-black">185° F</p>
                            </div>
                        </div>

                        {/* CENTER SCANNER UI */}
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                                className="w-48 h-48 border border-cyan-400/20 rounded-full relative"
                            >
                                <div className="absolute top-0 left-1/2 w-1 h-24 bg-gradient-to-t from-cyan-400/0 to-cyan-400 -translate-x-1/2 origin-bottom" />
                            </motion.div>
                        </div>
                    </div>

                    {/* BOTTOM GAUGE SECTION */}
                    <div className="bg-white/5 rounded-3xl p-6 border border-white/10 flex justify-around">
                        <GaugeIndicator label="HSE Health" value={94} color="#4ade80" />
                        <GaugeIndicator label="Emissions" value={22} color="#f87171" />
                        <GaugeIndicator label="Opt Efficiency" value={88} color="#22d3ee" />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExecutiveDashboard;
