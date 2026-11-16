import { useRef, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, PointerLockControls } from '@react-three/drei';
import * as THREE from 'three';
import { useAppStore } from '../store/appStore';

const CameraControls = () => {
  const cameraMode = useAppStore(state => state.cameraMode);
  const { camera } = useThree();
  const orbitRef = useRef<any>(null);
  
  // Basic WASD movement for FPV and Drone
  const keys = useRef({ w: false, a: false, s: false, d: false });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if(e.key.toLowerCase() in keys.current) keys.current[e.key.toLowerCase() as keyof typeof keys.current] = true;
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if(e.key.toLowerCase() in keys.current) keys.current[e.key.toLowerCase() as keyof typeof keys.current] = false;
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  useFrame((state, delta) => {
    if (cameraMode === 'drone' || cameraMode === 'fpv') {
      const speed = cameraMode === 'drone' ? 5.0 : 2.0;
      const velocity = new THREE.Vector3();
      const direction = new THREE.Vector3();
      
      camera.getWorldDirection(direction);
      direction.y = cameraMode === 'fpv' ? 0 : direction.y; // Keep FPV flat
      direction.normalize();

      if (keys.current.w) velocity.add(direction);
      if (keys.current.s) velocity.sub(direction);
      
      const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize();
      if (keys.current.a) velocity.add(right);
      if (keys.current.d) velocity.sub(right);

      velocity.normalize().multiplyScalar(speed * delta);
      camera.position.add(velocity);

      // FPV lock height to roughly ground level
      if (cameraMode === 'fpv') {
        camera.position.y = 0.5; 
      }
    } else if (cameraMode === 'cinematic') {
       // Simple cinematic orbit around origin
       const time = state.clock.getElapsedTime();
       camera.position.x = Math.sin(time * 0.2) * 10;
       camera.position.z = Math.cos(time * 0.2) * 10;
       camera.position.y = 5;
       camera.lookAt(0, 0, 0);
    }
  });

  return (
    <>
      {cameraMode === 'orbit' && <OrbitControls ref={orbitRef} makeDefault />}
      {(cameraMode === 'drone' || cameraMode === 'fpv') && <PointerLockControls makeDefault />}
    </>
  );
};

export default CameraControls;
