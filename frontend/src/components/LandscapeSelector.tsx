import React from 'react';
import { useAppStore } from '../store/appStore';
import { landscapes } from '../data/landscapes';
import { generateTerrainData } from '../utils/terrainGenerator';

export default function LandscapeSelector() {
  const { setAppPhase, setCurrentLandscapeId, setTerrainData, setAnimationStep } = useAppStore();
  const [isPreparing, setIsPreparing] = React.useState(false);
  const [selectionError, setSelectionError] = React.useState('');

  const handleSelect = (id: string, terrainType: any) => {
    setIsPreparing(true);
    setSelectionError('');

    try {
      const data = generateTerrainData(terrainType, 256);
      setCurrentLandscapeId(id);
      setTerrainData(data);
      setAnimationStep(0);
      setAppPhase('reconstructing');
    } catch (error) {
      setSelectionError(
        error instanceof Error
          ? `Unable to prepare terrain: ${error.message}`
          : 'Unable to prepare terrain.'
      );
      setIsPreparing(false);
    }
  };

  const featured = landscapes.find(l => l.featured);
  const others = landscapes.filter(l => !l.featured);

  return (
    <div className="h-full overflow-y-auto bg-stone-950 text-stone-300 p-8 flex flex-col font-mono selection:bg-green-900 selection:text-green-50">
      
      {/* Header */}
      <header className="mb-12 border-b border-stone-800 pb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 bg-green-900 rounded grid place-items-center">
            <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-wider text-stone-100">DEPTHWIZARD</h1>
          <span className="px-2 py-1 bg-stone-800 text-stone-400 text-xs rounded border border-stone-700">DEMO ENVIRONMENT</span>
        </div>
        <p className="text-stone-500 max-w-2xl">Select a curated landscape to run the AI reconstruction sequence. Each environment demonstrates different terrain analysis capabilities and verticality handling.</p>
        <button
          onClick={() => useAppStore.getState().setAppPhase('exploring')}
          className="mt-5 rounded border border-green-700 bg-green-900/30 px-5 py-3 text-sm font-bold tracking-widest text-green-300 hover:bg-green-800"
        >
          OPEN REAL ROUTE MAP
        </button>
      </header>

      {/* Main Content */}
      <div className="max-w-6xl w-full mx-auto space-y-8 flex-1">
        {selectionError && (
          <div role="alert" className="border border-red-900 bg-red-950/40 text-red-200 px-4 py-3 rounded">
            {selectionError}
          </div>
        )}
        {isPreparing && (
          <div role="status" className="text-sm text-green-400">
            Preparing terrain data...
          </div>
        )}
        
        {/* Featured Landscape */}
        {featured && (
          <div className="border border-stone-800 bg-stone-900/50 overflow-hidden group hover:border-green-800 transition-colors duration-300">
            <div className="p-8 flex flex-col md:flex-row gap-8 items-center">
              <div className="flex-1 space-y-4">
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 bg-green-900/30 text-green-400 text-xs font-bold tracking-widest border border-green-900/50 rounded">FEATURED REGION</span>
                  <span className="text-stone-500 text-sm">{featured.location}</span>
                </div>
                <h2 className="text-4xl font-bold text-stone-100">{featured.name}</h2>
                <h3 className="text-xl text-stone-400">{featured.subtitle}</h3>
                <p className="text-stone-400 leading-relaxed max-w-xl">{featured.description}</p>
                <div className="pt-4">
                  <button 
                    onClick={() => handleSelect(featured.id, featured.terrainType)}
                    className="bg-green-800 hover:bg-green-700 text-green-50 px-6 py-3 rounded font-bold tracking-widest transition-colors flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    RUN AI RECONSTRUCTION
                  </button>
                </div>
              </div>
              <div className="w-full md:w-1/3 aspect-square bg-stone-950 border border-stone-800 relative rounded overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-stone-800 to-stone-950 opacity-50"></div>
                {/* Abstract wireframe representing mountain */}
                <svg className="absolute inset-0 w-full h-full opacity-20 group-hover:opacity-40 transition-opacity" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <path d="M0,100 L30,60 L50,80 L80,20 L100,60 L100,100 Z" fill="none" stroke="currentColor" strokeWidth="1" className="text-green-500" />
                  <path d="M20,100 L40,70 L60,85 L85,30 L100,70 L100,100 Z" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-stone-400" />
                </svg>
              </div>
            </div>
          </div>
        )}

        {/* Other Landscapes */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {others.map(landscape => (
            <div 
              key={landscape.id}
              className="border border-stone-800 bg-stone-900/30 p-5 flex flex-col hover:border-stone-600 transition-colors cursor-pointer group"
              onClick={() => handleSelect(landscape.id, landscape.terrainType)}
            >
              <div className="text-xs text-stone-500 mb-2 truncate">{landscape.location}</div>
              <h3 className="text-lg font-bold text-stone-200 mb-2 group-hover:text-green-400 transition-colors">{landscape.name}</h3>
              <p className="text-sm text-stone-500 flex-1 mb-4 line-clamp-3">{landscape.description}</p>
              <div className="flex items-center gap-2 text-xs font-bold text-stone-400 group-hover:text-green-500 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                INITIATE
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
