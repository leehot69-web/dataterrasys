
import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Text } from '@react-three/drei';
import * as THREE from 'three';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

// --- Utilitarios Geométricos ---

import { calculateDLS } from '../utils/physics_models'; // Nueva Geofísica

const WellPath = ({ depthData, curveData, curveName = 'GR' }) => {
    // Si no hay datos de survey real, simulamos una desviación suave
    // para que se vea "interesante" en 3D (o usamos vertical si es lo que hay)

    const points = useMemo(() => {
        if (!depthData || depthData.length === 0) return [];

        const pts = [];
        // const maxDepth = Math.max(...depthData); // Original line
        const kop = Math.max(...depthData) * 0.2; // Simulación de desviación (Kick-off point a 20% prof)

        // En una app real, esto vendría del Survey (Inc, Azi)
        // const kop = maxDepth * 0.2; // Original line
        let inc = 0;
        let azi = 45 * (Math.PI / 180); // 45 grados Norte-Este

        let x = 0, y = 0, z = 0; // x=East, y=North, z=TVD (invertido para ThreeJS: y es arriba)

        for (let i = 0; i < depthData.length; i += 10) { // Subsampling cada 10 pts para rendimiento
            const md = depthData[i];
            // const val = curveData ? curveData[i] : 0; // Valor de curva (ej. GR) para color // Original line

            // Calculo simplificado de trayectoria (Método Tangencial simple para visualización)
            const prevInc = inc; // Store previous inclination for DLS calculation
            if (md > kop) {
                inc += 0.005; // Build rate suave
            }

            // Delta MD
            const dMd = i > 0 ? (md - depthData[i - 10]) : md;
            const prevMd = i > 0 ? depthData[i - 10] : 0; // Store previous MD for DLS calculation

            const dZ = dMd * Math.cos(inc);
            const dH = dMd * Math.sin(inc);

            // const dN = dH * Math.cos(azi); // Original line
            // const dE = dH * Math.sin(azi); // Original line

            z -= dZ; // ThreeJS: Y es arriba, así que Profundidad es -Y
            y += dH * Math.cos(azi); // North es -Z en ThreeJS por convención o X
            x += dH * Math.sin(azi); // East

            // CÁLCULO DLS REAl (Drilling Engineering)
            // Convertir rad a deg para la función
            const dls = calculateDLS(
                prevMd, prevInc * (180 / Math.PI), azi * (180 / Math.PI),
                md, inc * (180 / Math.PI), azi * (180 / Math.PI)
            );

            // COLOREADO POR RIESGO DE PERFORACIÓN (DLS)
            // Safe < 3°/100ft (Verde), Risky > 3° (Rojo)
            const isRisky = dls > 3.0;
            const color = new THREE.Color(isRisky ? '#ef4444' : '#22c55e'); // Rojo vs Verde

            pts.push({ pos: new THREE.Vector3(x, z, y), color, depth: md, val: dls });
        }
        return pts;
    }, [depthData, curveData]);

    // Crear geometría del tubo
    const curve = useMemo(() => {
        if (points.length < 2) return null;
        return new THREE.CatmullRomCurve3(points.map(p => p.pos));
    }, [points]);

    if (!curve) return null;

    return (
        <group>
            {/* El Tubo del Pozo */}
            <mesh>
                <tubeGeometry args={[curve, points.length, 120, 16, false]} />
                {/* Material AUTO-ILUMINADO para máxima visibilidad */}
                <meshBasicMaterial vertexColors={true} />
            </mesh>

            {/* Líneas de Profundidad cada 1000m */}
            {points.filter((_, i) => i % 50 === 0).map((p, i) => (
                <Text key={i} position={[p.pos.x + 30, p.pos.y, p.pos.z]} fontSize={40} color="white">
                    {Math.round(p.depth)}'
                </Text>
            ))}
        </group>
    );
};

// --- Componente de Rejilla Geológica (Grid) ---
const ReservoirGrid = () => {
    return (
        <gridHelper args={[10000, 50, 0x444444, 0x222222]} position={[0, -8000, 0]} />
    );
};

const WellTrajectory3D = ({ data, onClose }) => {
    // Helper para buscar curvas con aliases
    const findCurve = (aliases) => {
        if (!data?.well_data) return [];
        for (const alias of aliases) {
            // Check exact match
            if (data.well_data[alias]) return data.well_data[alias];
            // Check case-insensitive
            const key = Object.keys(data.well_data).find(k => k.toUpperCase() === alias);
            if (key) return data.well_data[key];
        }
        return [];
    };

    const depth = findCurve(['DEPTH', 'DEPT', 'M_DEPTH', 'MD']);
    const gr = findCurve(['GR', 'GR_ED', 'GAMMA', 'GAM', 'CGR', 'GR_FINAL']);

    // Fallback: Si no hay profundidad, generar una sintética basada en Max Depth
    const finalDepth = (depth && depth.length > 0) ? depth :
        Array.from({ length: gr?.length || 1000 }, (_, i) => i * ((data?.kpis?.max_depth || 5000) / (gr?.length || 1000)));

    console.log("3D Viewer data:", { depthLen: finalDepth?.length, grLen: gr?.length, available: Object.keys(data?.well_data || {}) });

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{
                    position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
                    background: '#000', zIndex: 3000, display: 'flex', flexDirection: 'column'
                }}
            >
                {/* Header Flotante */}
                <div style={{
                    position: 'absolute', top: 20, left: 20, zIndex: 3010,
                    background: 'rgba(0,0,0,0.8)', padding: '15px 25px', borderRadius: '12px',
                    border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)',
                    display: 'flex', gap: '20px', alignItems: 'center'
                }}>
                    <div>
                        <h2 style={{ margin: 0, color: '#fff', fontSize: '1.2rem', fontFamily: 'Outfit' }}>
                            Visor de Trayectoria 3D
                        </h2>
                        <div style={{ fontSize: '0.8rem', color: '#888' }}>
                            Visualización de Desviación y Litología (GR)
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '15px', fontSize: '0.75rem', color: '#ccc' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ width: 12, height: 12, background: '#fbbf24', borderRadius: '50%' }}></div>
                            Arena (Reservorio)
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ width: 12, height: 12, background: '#10b981', borderRadius: '50%' }}></div>
                            Lutita (Sello)
                        </div>
                    </div>
                </div>

                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute', top: 20, right: 20, zIndex: 3010,
                        background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff',
                        width: '40px', height: '40px', borderRadius: '50%', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}
                >
                    <X size={20} />
                </button>

                {/* Canvas 3D */}
                <div style={{ flex: 1, cursor: 'move' }}>
                    <Canvas camera={{ position: [4000, -3000, 4000], fov: 45, far: 50000 }}>
                        {/* Fondo Azul Ingenieria (Petrel Style) */}
                        <color attach="background" args={['#1e293b']} />
                        <fog attach="fog" args={['#1e293b', 2000, 40000]} />

                        <ambientLight intensity={0.8} />
                        <pointLight position={[2000, 5000, 2000]} intensity={1.5} />

                        {/* Superficie (Ground Level) */}
                        <gridHelper args={[20000, 40, 0x64748b, 0x334155]} position={[0, 0, 0]} />

                        <OrbitControls
                            target={[0, -4000, 0]}
                            autoRotate={true}
                            autoRotateSpeed={1.0}
                            enableDamping
                            dampingFactor={0.05}
                            rotateSpeed={0.5}
                            minDistance={100}
                            maxDistance={30000}
                        />

                        {/* Elementos Geológicos */}
                        <ReservoirGrid />
                        <WellPath depthData={finalDepth} curveData={gr} />
                        <axesHelper args={[1000]} />
                    </Canvas>
                </div>

                {/* Footer Controls */}
                <div style={{
                    position: 'absolute', bottom: 30, left: '50%', transform: 'translateX(-50%)',
                    zIndex: 3010, background: 'rgba(0,0,0,0.6)', padding: '10px 20px', borderRadius: '30px',
                    color: '#666', fontSize: '0.8rem', pointerEvents: 'none'
                }}>
                    Hold Click to Rotate • Scroll to Zoom • Right Click to Pan
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

export default WellTrajectory3D;
