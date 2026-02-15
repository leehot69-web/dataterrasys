import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Waves,
    Zap,
    Activity,
    Layers,
    Thermometer,
    ArrowUpRight,
    Target,
    FileSearch,
    Maximize2,
    Share2
} from 'lucide-react';

const LogTrack = ({ name, color, data, width }) => (
    <div className="flex flex-col h-full border-r border-white/5" style={{ width }}>
        <div className="p-2 border-b border-white/10 bg-white/5">
            <p className="text-[10px] font-black uppercase text-center tracking-tighter" style={{ color }}>{name}</p>
            <div className="flex justify-between text-[8px] text-white/30 px-1 mt-1">
                <span>0</span>
                <span>100</span>
            </div>
        </div>
        <div className="flex-1 relative overflow-hidden bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:100%_40px]">
            <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                <polyline
                    points={data.map((v, i) => `${v},${i * 10}`).join(' ')}
                    fill="none"
                    stroke={color}
                    strokeWidth="1.5"
                    className="opacity-80"
                />
            </svg>
        </div>
    </div>
);

const WellLogVisualization = () => {
    const [depth, setDepth] = useState(12000);
    const [data, setData] = useState({
        gamma: Array.from({ length: 50 }, () => Math.random() * 80),
        res: Array.from({ length: 50 }, () => Math.random() * 60 + 20),
        neu: Array.from({ length: 50 }, () => Math.random() * 40 + 10)
    });

    console.log("Loading WellLogVisualization component...");

    return (
        <div className="h-screen bg-[#050505] text-white flex flex-col font-mono overflow-hidden">
            {/* MOBILE STATUS BAR SIMULATION */}
            <div className="flex justify-between items-center px-6 py-3 opacity-40 text-xs">
                <div className="flex gap-4">
                    <span>DTERRA OS v7.0</span>
                    <span>LAT: 10.42N</span>
                </div>
                <div className="flex gap-2">
                    <Layers size={12} />
                    <Zap size={12} fill="currentColor" />
                </div>
            </div>

            {/* HEADER HUD */}
            <header className="px-6 py-4 flex justify-between items-end border-b border-white/10 bg-gradient-to-b from-white/5 to-transparent">
                <div>
                    <h2 className="text-2xl font-black italic tracking-tighter leading-none">VNZ_TX_402</h2>
                    <p className="text-[10px] text-cyan-400 font-bold tracking-widest mt-1">REAL-TIME LWD STREAM</p>
                </div>
                <div className="flex gap-4 mb-1">
                    <div className="text-right">
                        <span className="block text-[8px] text-white/40 uppercase font-black">ROP</span>
                        <span className="text-sm font-black">45.2 FT/H</span>
                    </div>
                    <div className="text-right">
                        <span className="block text-[8px] text-white/40 uppercase font-black">WOB</span>
                        <span className="text-sm font-black">12.5 KLB</span>
                    </div>
                </div>
            </header>

            {/* MAIN LOG AREA */}
            <div className="flex-1 flex overflow-hidden">
                {/* DEPTH SCALE */}
                <div className="w-16 flex flex-col border-r border-white/20 bg-white/5">
                    <div className="h-10 bg-white/10 flex items-center justify-center">
                        <Target size={14} className="text-cyan-400" />
                    </div>
                    <div className="flex-1 relative bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:100%_40px]">
                        {[12000, 12050, 12100, 12150, 12200].map((d, i) => (
                            <span key={i} className="absolute text-[9px] font-black text-white/40 -rotate-90 left-2" style={{ top: i * 80 + 20 }}>
                                {d}
                            </span>
                        ))}
                    </div>
                </div>

                {/* TRACKS CONTAINER */}
                <div className="flex-1 flex overflow-x-auto no-scrollbar">
                    <LogTrack name="GAMMA RAY" color="#4ade80" data={data.gamma} width="120px" />
                    <LogTrack name="RESISTIVITY" color="#facc15" data={data.res} width="120px" />
                    <LogTrack name="NEUTRON" color="#22d3ee" data={data.neu} width="120px" />
                    <LogTrack name="DENSITY" color="#f87171" data={data.neu.map(v => v * 0.8)} width="120px" />
                </div>

                {/* SIDE CONTEXT PANEL */}
                <div className="w-20 flex flex-col items-center gap-6 py-8 border-l border-white/10 bg-black/40 backdrop-blur-md">
                    {[Maximize2, FileSearch, Waves, Activity, Share2].map((Icon, i) => (
                        <motion.button
                            key={i}
                            whileTap={{ scale: 0.8 }}
                            className={`p-3 rounded-2xl ${i === 2 ? 'bg-cyan-400 text-black' : 'bg-white/5 text-white/40'}`}
                        >
                            <Icon size={20} />
                        </motion.button>
                    ))}
                </div>
            </div>

            {/* FLOATING DATA HUD */}
            <div className="absolute top-1/2 right-24 -translate-y-1/2 space-y-4">
                <motion.div
                    initial={{ x: 20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    className="p-4 bg-cyan-950/80 backdrop-blur-xl border border-cyan-400/30 rounded-3xl"
                >
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-cyan-400 text-black rounded-xl">
                            <Thermometer size={16} />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-cyan-400">BHT</p>
                            <p className="text-lg font-black italic">214.5 °F</p>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* BOTTOM TOOLBELT */}
            <div className="p-4 bg-white/5 border-t border-white/10 flex justify-between items-center">
                <div className="flex gap-4">
                    <span className="text-[10px] font-black text-cyan-400 italic">SYSTEM_ONLINE //</span>
                    <span className="text-[10px] font-black text-white/40 uppercase">Awaiting Formation Strike...</span>
                </div>
                <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                        animate={{ x: [-128, 128] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="w-16 h-full bg-cyan-400"
                    />
                </div>
            </div>
        </div>
    );
};

export default WellLogVisualization;
