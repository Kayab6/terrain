import { create } from 'zustand';
import { TerrainData } from '../utils/terrainGenerator';

export type AppPhase = 'selector' | 'reconstructing' | 'exploring';
export type CameraMode = 'orbit' | 'drone' | 'fpv' | 'cinematic';

export interface InspectionPoint {
  x: number;
  y: number;
  z: number;
  elevation: number;
}

export interface GeographicRouteCoordinate {
  lng: number;
  lat: number;
}

interface AppState {
  appPhase: AppPhase;
  currentLandscapeId: string | null;
  terrainData: TerrainData | null;
  animationStep: number;
  verticalExaggeration: number;
  
  cameraMode: CameraMode;
  inspectionPoint: InspectionPoint | null;
  confidenceMode: boolean;
  floodLevel: number;
  showWater: boolean;
  routeCoordinates: GeographicRouteCoordinate[];
  
  setAppPhase: (phase: AppPhase) => void;
  setCurrentLandscapeId: (id: string | null) => void;
  setTerrainData: (data: TerrainData | null) => void;
  setAnimationStep: (step: number) => void;
  setVerticalExaggeration: (val: number) => void;
  
  setCameraMode: (mode: CameraMode) => void;
  setInspectionPoint: (point: InspectionPoint | null) => void;
  setConfidenceMode: (mode: boolean) => void;
  setFloodLevel: (level: number) => void;
  setShowWater: (show: boolean) => void;
  setRouteCoordinates: (coordinates: GeographicRouteCoordinate[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  appPhase: 'selector',
  currentLandscapeId: null,
  terrainData: null,
  animationStep: 0,
  verticalExaggeration: 1.0,
  
  cameraMode: 'orbit',
  inspectionPoint: null,
  confidenceMode: false,
  floodLevel: 0,
  showWater: false,
  routeCoordinates: [],
  
  setAppPhase: (phase) => set({ appPhase: phase }),
  setCurrentLandscapeId: (id) => set({ currentLandscapeId: id }),
  setTerrainData: (data) => set({ terrainData: data }),
  setAnimationStep: (step) => set({ animationStep: step }),
  setVerticalExaggeration: (val) => set({ verticalExaggeration: val }),
  
  setCameraMode: (mode) => set({ cameraMode: mode }),
  setInspectionPoint: (point) => set({ inspectionPoint: point }),
  setConfidenceMode: (mode) => set({ confidenceMode: mode }),
  setFloodLevel: (level) => set({ floodLevel: level }),
  setShowWater: (show) => set({ showWater: show }),
  setRouteCoordinates: (coordinates) => set({ routeCoordinates: coordinates }),
}));
