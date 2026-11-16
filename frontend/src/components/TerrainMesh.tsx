import { useRef, useEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useAppStore } from '../store/appStore';

export default function TerrainMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  const geomRef = useRef<THREE.PlaneGeometry>(null);
  const matRef = useRef<THREE.MeshStandardMaterial>(null);
  const morphProgress = useRef(0);
  
  const { terrainData, appPhase, verticalExaggeration, confidenceMode, setInspectionPoint } = useAppStore();

  // Create geometry and texture once per terrainData
  const { geometry, canvasTexture, basePositions } = useMemo(() => {
    if (!terrainData) return { geometry: null, canvasTexture: null, basePositions: null };
    
    const { resolution, heightData, canvas } = terrainData;
    const geom = new THREE.PlaneGeometry(10, 10, resolution, resolution);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    
    // Store original Z positions (which are 0) and height data
    // PlaneGeometry is created in XY plane. Z is the height.
    const positions = geom.attributes.position.array as Float32Array;
    const basePos = new Float32Array(positions.length);
    for (let i = 0; i < positions.length; i += 3) {
      basePos[i] = positions[i];     // x
      basePos[i+1] = positions[i+1]; // y
      // We will map height to Z. The PlaneGeometry is rotated by -Math.PI/2 around X
      // so Z becomes world Y (up).
      const vertexIdx = i / 3;
      // Ensure height mapping matches texture
      const h = heightData[vertexIdx] || 0;
      basePos[i+2] = h * 2.0; // max displacement 2.0
    }
    
    return { geometry: geom, canvasTexture: tex, basePositions: basePos };
  }, [terrainData]);

  // Handle phase changes and morph animation
  useEffect(() => {
    if (appPhase === 'reconstructing') {
      morphProgress.current = 0;
    }
  }, [appPhase]);

  useFrame((_state, delta) => {
    // When exploring, animate morph to 1
    if (appPhase === 'exploring' && morphProgress.current < 1) {
      morphProgress.current += delta * 0.5; // 2 seconds to morph
      if (morphProgress.current > 1) morphProgress.current = 1;
    } else if (appPhase === 'selector') {
      morphProgress.current = 0;
    }

    // Apply vertex positions
    if (geomRef.current && basePositions) {
      const positions = geomRef.current.attributes.position.array as Float32Array;
      for (let i = 0; i < positions.length; i += 3) {
        // Apply vertical exaggeration and morph progress
        positions[i+2] = basePositions[i+2] * morphProgress.current * verticalExaggeration;
      }
      geomRef.current.attributes.position.needsUpdate = true;
      geomRef.current.computeVertexNormals();
    }
  });

  const handlePointerDown = (e: any) => {
    e.stopPropagation();
    if (appPhase !== 'exploring') return;
    
    const point = e.point;
    // Calculate elevation relative to the base plane
    const elevation = point.y;
    
    setInspectionPoint({
      x: point.x,
      y: point.y,
      z: point.z,
      elevation: elevation
    });
  };

  if (!geometry) return null;

  return (
    <mesh 
      ref={meshRef} 
      rotation={[-Math.PI / 2, 0, 0]} 
      onPointerDown={handlePointerDown}
      receiveShadow
      castShadow
    >
      <primitive object={geometry} ref={geomRef} attach="geometry" />
      <meshStandardMaterial 
        ref={matRef}
        map={confidenceMode ? null : canvasTexture}
        roughness={0.8}
        metalness={0.1}
        wireframe={appPhase === 'reconstructing'}
        color={confidenceMode ? '#ff4444' : '#ffffff'}
        emissive={confidenceMode ? '#550000' : '#000000'}
      />
    </mesh>
  );
}
