import { useEffect } from 'react';
import { useAppStore } from '../store/appStore';

export default function ReconstructionOverlay() {
  const { animationStep, setAnimationStep, setAppPhase } = useAppStore();

  useEffect(() => {
    // 6-step animated sequence
    // Steps: 0=Original Landscape, 1=Analyzing, 2=Depth, 3=Generating Elevation, 4=Constructing, 5=Complete
    if (animationStep < 5) {
      const timer = setTimeout(() => {
        setAnimationStep(animationStep + 1);
      }, 1500); // 1.5 seconds per step
      return () => clearTimeout(timer);
    } else if (animationStep === 5) {
      const timer = setTimeout(() => {
        setAppPhase('exploring');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [animationStep, setAnimationStep, setAppPhase]);

  const steps = [
    'Acquiring Landscape Data',
    'Analyzing Topography',
    'Inferring Depth Map',
    'Generating Elevation Mesh',
    'Constructing 3D Terrain',
    'Reconstruction Complete'
  ];

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-stone-950/80 backdrop-blur-sm">
      <div className="bg-stone-900 border border-stone-800 p-8 rounded-lg max-w-md w-full font-mono shadow-2xl">
        <h2 className="text-xl font-bold text-stone-100 mb-6 flex items-center gap-2">
          <svg className="w-5 h-5 text-green-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          AI RECONSTRUCTION
        </h2>
        
        <div className="space-y-4">
          {steps.map((stepText, index) => {
            const isActive = index === animationStep;
            const isCompleted = index < animationStep;
            let colorClass = 'text-stone-500';
            if (isActive) colorClass = 'text-green-400 font-bold';
            if (isCompleted) colorClass = 'text-stone-300';

            return (
              <div key={index} className={`flex items-center gap-3 ${colorClass} transition-colors duration-300`}>
                <div className={`w-4 h-4 rounded-full border ${isCompleted ? 'bg-green-600 border-green-600' : isActive ? 'bg-green-400 border-green-400 animate-pulse' : 'border-stone-700'}`}>
                  {isCompleted && (
                    <svg className="w-full h-full text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <span>{stepText}</span>
              </div>
            );
          })}
        </div>

        <div className="mt-8 h-1 bg-stone-800 rounded overflow-hidden">
          <div 
            className="h-full bg-green-500 transition-all duration-300 ease-linear"
            style={{ width: `${(animationStep / 5) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
