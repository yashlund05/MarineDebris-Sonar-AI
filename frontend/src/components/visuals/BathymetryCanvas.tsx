import React, { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

interface BathymetryCanvasProps {
  paused?: boolean;
  className?: string;
  activeCount?: number;
  evidenceCount?: number;
  failedCount?: number;
}

interface MissionSceneProps extends Required<Omit<BathymetryCanvasProps, "className">> {}

const supportsWebGl = () => {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
};

function MissionTopology({ activeCount, evidenceCount, failedCount, paused }: MissionSceneProps) {
  const group = React.useRef<THREE.Group>(null);
  const ring = React.useRef<THREE.Mesh>(null);
  const topology = useMemo(() => {
    const geometry = new THREE.PlaneGeometry(11, 7, 32, 22);
    const position = geometry.attributes.position;
    for (let index = 0; index < position.count; index += 1) {
      const x = position.getX(index);
      const y = position.getY(index);
      position.setZ(index, Math.sin(x * 1.3) * 0.18 + Math.cos(y * 1.65) * 0.12 + Math.sin((x + y) * 1.7) * 0.08);
    }
    geometry.computeVertexNormals();
    return geometry;
  }, []);

  useEffect(() => () => topology.dispose(), [topology]);

  useFrame((state, delta) => {
    if (paused) return;
    if (group.current) group.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.14) * 0.025;
    if (ring.current) ring.current.rotation.z += delta * 0.16;
  });

  const evidenceScale = Math.max(0.45, Math.min(1.4, 0.45 + evidenceCount * 0.08));
  const activeScale = Math.max(0.3, Math.min(1.1, 0.3 + activeCount * 0.1));
  const alertScale = Math.max(0.18, Math.min(0.7, 0.18 + failedCount * 0.1));

  return (
    <group ref={group} rotation={[-0.86, 0.1, -0.35]} position={[1.55, -0.3, 0]}>
      <mesh geometry={topology} receiveShadow>
        <meshStandardMaterial color="#1f6268" roughness={0.7} metalness={0.1} wireframe />
      </mesh>
      <mesh position={[0.75, 0.55, 0.32]} scale={evidenceScale}>
        <icosahedronGeometry args={[0.19, 2]} />
        <meshStandardMaterial color="#efd18b" emissive="#b7842e" emissiveIntensity={0.55} roughness={0.28} />
      </mesh>
      <mesh position={[-1.85, -0.8, 0.2]} scale={activeScale}>
        <octahedronGeometry args={[0.17, 1]} />
        <meshStandardMaterial color="#9ed9d1" emissive="#287a77" emissiveIntensity={0.48} />
      </mesh>
      <mesh position={[2.2, -1.05, 0.18]} scale={alertScale}>
        <sphereGeometry args={[0.16, 20, 20]} />
        <meshStandardMaterial color="#d86d54" emissive="#bd493d" emissiveIntensity={0.5} />
      </mesh>
      <mesh ref={ring} position={[0.75, 0.55, 0.25]}>
        <torusGeometry args={[0.52, 0.012, 10, 50]} />
        <meshBasicMaterial color="#f1cf82" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

/** An abstract mission-state scene: not bathymetry or a geospatial map. */
export const BathymetryCanvas: React.FC<BathymetryCanvasProps> = ({
  paused = false,
  className,
  activeCount = 0,
  evidenceCount = 0,
  failedCount = 0,
}) => {
  const [webGlAvailable, setWebGlAvailable] = useState(true);
  const reducedMotion = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => setWebGlAvailable(supportsWebGl()), []);

  if (!webGlAvailable) {
    return <div className={`${className ?? ""} mission-scene-fallback`} role="img" aria-label="Mission state visualization unavailable because WebGL is not supported." />;
  }

  return (
    <div className={className} aria-hidden="true">
      <Canvas dpr={reducedMotion ? 1 : [1, 1.5]} camera={{ position: [0, 0.2, 7.2], fov: 42 }} gl={{ antialias: !reducedMotion, powerPreference: "high-performance" }} performance={{ min: 0.6 }}>
        <color attach="background" args={["#123640"]} />
        <fog attach="fog" args={["#123640", 5, 12]} />
        <ambientLight intensity={1.35} />
        <directionalLight position={[4, 5, 4]} intensity={1.5} color="#f4d68c" />
        <pointLight position={[-3, 1, 2]} intensity={1.8} color="#4caaa3" distance={8} />
        <Suspense fallback={null}>
          <MissionTopology activeCount={activeCount} evidenceCount={evidenceCount} failedCount={failedCount} paused={paused || reducedMotion} />
        </Suspense>
        <OrbitControls enablePan={false} enableZoom={false} minPolarAngle={0.8} maxPolarAngle={1.7} autoRotate={!paused && !reducedMotion} autoRotateSpeed={0.35} />
      </Canvas>
    </div>
  );
};

export default BathymetryCanvas;
