import { Canvas } from '@react-three/fiber';
import { Grid } from '@react-three/drei';
import TerrainMesh from './TerrainMesh';
import CameraControls from './CameraControls';
import { useAppStore } from '../store/appStore';
import { Line } from '@react-three/drei';
import { Vector3 } from 'three';

const WaterPlane = () => {
  const { showWater, floodLevel } = useAppStore();
  if (!showWater) return null;
  return (
    <mesh position={[0, floodLevel, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[20, 20]} />
      <meshStandardMaterial color="#3b82f6" transparent opacity={0.7} roughness={0.1} metalness={0.8} />
    </mesh>
  );
};

const ThreeCanvas = () => {
  const routeCoordinates = useAppStore((state) => state.routeCoordinates);
  const routePoints = (() => {
    if (routeCoordinates.length === 0) return [];
    const longitudes = routeCoordinates.map((point) => point.lng);
    const latitudes = routeCoordinates.map((point) => point.lat);
    const west = Math.min(...longitudes);
    const east = Math.max(...longitudes);
    const south = Math.min(...latitudes);
    const north = Math.max(...latitudes);
    const longitudeSpan = Math.max(0.000001, east - west);
    const latitudeSpan = Math.max(0.000001, north - south);
    return routeCoordinates.map((point) => new Vector3(
      ((point.lng - west) / longitudeSpan - 0.5) * 10,
      0.45,
      ((point.lat - north) / latitudeSpan + 0.5) * 10
    ));
  })();
  return (
    <Canvas camera={{ position: [0, 8, 12], fov: 50 }}>
      <color attach="background" args={['#1c1917']} />
      
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1.5} castShadow />

      <TerrainMesh />
      <WaterPlane />
      {routePoints.length > 1 && (
        <Line points={routePoints} color="#ef4444" lineWidth={4} depthTest={false} />
      )}

      <Grid infiniteGrid fadeDistance={50} sectionColor="#4a3f35" cellColor="#292524" />
      <CameraControls />
    </Canvas>
  );
};

export default ThreeCanvas;
