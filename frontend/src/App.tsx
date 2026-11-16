import ThreeCanvas from './components/ThreeCanvas';
import LandscapeSelector from './components/LandscapeSelector';
import ReconstructionOverlay from './components/ReconstructionOverlay';
import { Camera, Plane, User, Film, Layers, Droplets, ArrowLeft } from 'lucide-react';
import { useAppStore, CameraMode } from './store/appStore';
import { landscapes } from './data/landscapes';
import TerrainAssistant from './components/TerrainAssistant';
import MapPanel from './components/MapPanel';

export default function App() {
  const {
    appPhase,
    currentLandscapeId,
    terrainData,
    cameraMode,
    inspectionPoint,
    confidenceMode,
    showWater,
    floodLevel,
    verticalExaggeration,
    setAppPhase,
    setCameraMode,
    setConfidenceMode,
    setShowWater,
    setFloodLevel,
    setVerticalExaggeration,
    setCurrentLandscapeId,
    setTerrainData,
  } = useAppStore();

  const currentLandscape = landscapes.find((landscape) => landscape.id === currentLandscapeId);

  const handleBackToSelector = () => {
    setAppPhase('selector');
    setCurrentLandscapeId(null);
    setTerrainData(null);
  };

  const modes: { id: CameraMode; icon: typeof Camera; label: string }[] = [
    { id: 'orbit', icon: Camera, label: 'Orbit' },
    { id: 'drone', icon: Plane, label: 'Drone' },
    { id: 'fpv', icon: User, label: 'FPV' },
    { id: 'cinematic', icon: Film, label: 'Cinematic' },
  ];

  if (appPhase === 'selector') return <LandscapeSelector />;

  return (
    <div className="h-full flex flex-col bg-stone-950 font-mono text-stone-300">
      {appPhase === 'reconstructing' && <ReconstructionOverlay />}
      <nav className="h-14 shrink-0 bg-stone-950 border-b border-stone-800 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <button onClick={handleBackToSelector} className="p-1 text-stone-400 hover:text-green-400" title="Change Landscape">
            <ArrowLeft size={20} />
          </button>
          <div className="font-bold text-lg text-green-500 tracking-widest">DEPTHWIZARD</div>
          {currentLandscape && (
            <div className="hidden items-center gap-2 border-l border-stone-800 pl-4 md:flex">
              <span className="text-stone-300 font-bold">{currentLandscape.name}</span>
              <span className="text-xs text-stone-500">{currentLandscape.location}</span>
            </div>
          )}
        </div>
        <div className="flex rounded border border-stone-800 bg-stone-900 overflow-hidden">
          {modes.map((mode) => {
            const Icon = mode.icon;
            return (
              <button
                key={mode.id}
                onClick={() => setCameraMode(mode.id)}
                className={`flex items-center gap-2 px-3 py-1.5 text-xs font-bold ${cameraMode === mode.id ? 'bg-green-800 text-green-50' : 'text-stone-400 hover:bg-stone-800'}`}
              >
                <Icon size={14} /> {mode.label}
              </button>
            );
          })}
        </div>
      </nav>

      <div className="min-h-0 flex-1 flex overflow-hidden">
        <aside className="hidden w-72 shrink-0 bg-stone-950 border-r border-stone-800 p-4 overflow-y-auto lg:flex flex-col gap-6">
          {terrainData && (
            <div>
              <h2 className="text-xs font-bold text-stone-500 mb-3 tracking-widest">TERRAIN STATS</h2>
              <div className="bg-stone-900/50 rounded border border-stone-800 p-4 space-y-3 text-sm">
                <div className="flex justify-between"><span>Max Elevation</span><b>{terrainData.stats.maxElevation.toFixed(1)}m</b></div>
                <div className="flex justify-between"><span>Min Elevation</span><b>{terrainData.stats.minElevation.toFixed(1)}m</b></div>
                <div className="flex justify-between"><span>Resolution</span><b>{terrainData.resolution}x{terrainData.resolution}</b></div>
              </div>
            </div>
          )}
          <div>
            <h2 className="text-xs font-bold text-stone-500 mb-3 tracking-widest">VISUALIZATION</h2>
            <div className="bg-stone-900/50 rounded border border-stone-800 p-4 space-y-4 text-sm">
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={confidenceMode} onChange={(event) => setConfidenceMode(event.target.checked)} />
                <Layers size={16} className={confidenceMode ? 'text-green-500' : 'text-stone-500'} />
                Elevation heatmap
              </label>
              <div>
                <div className="flex justify-between text-xs mb-2"><span>Vertical Exaggeration</span><b>{verticalExaggeration.toFixed(1)}x</b></div>
                <input aria-label="Vertical terrain scale" type="range" min="0.1" max="3" step="0.1" value={verticalExaggeration} onChange={(event) => setVerticalExaggeration(Number(event.target.value))} className="w-full accent-green-600" />
              </div>
            </div>
          </div>
          <div>
            <h2 className="text-xs font-bold text-stone-500 mb-3 tracking-widest">SIMULATION</h2>
            <label className="flex items-center gap-3 bg-stone-900/50 border border-stone-800 p-4 text-sm rounded">
              <input type="checkbox" checked={showWater} onChange={(event) => setShowWater(event.target.checked)} />
              <Droplets size={16} className={showWater ? 'text-blue-400' : 'text-stone-500'} />
              Water simulation
            </label>
            {showWater && (
              <input aria-label="Flood level" type="range" min="0" max="6" step="0.1" value={floodLevel} onChange={(event) => setFloodLevel(Number(event.target.value))} className="mt-3 w-full accent-blue-500" />
            )}
          </div>
        </aside>

        <main className="relative flex-1 bg-stone-950">
          <div className="absolute inset-0"><ThreeCanvas /></div>
          {appPhase === 'exploring' && <MapPanel />}
        </main>

        <aside className="hidden w-80 shrink-0 border-l border-stone-800 bg-stone-950 md:block">
          <div className="p-4 border-b border-stone-800 text-xs font-bold text-stone-500 tracking-widest">INSPECTION POINT</div>
          <div className="p-4 text-sm text-stone-400">
            {inspectionPoint ? `${inspectionPoint.elevation.toFixed(1)} m elevation` : 'Click the procedural terrain mesh to inspect elevation.'}
          </div>
          <TerrainAssistant welcomeMessage="Terrain controls and 3D inspection remain available beside the real route map." />
        </aside>
      </div>
    </div>
  );
}
