import os

files = {
    "package.json": """{
  "name": "depth_wizard_frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@react-three/drei": "^9.105.6",
    "@react-three/fiber": "^8.16.2",
    "lucide-react": "^0.378.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "three": "^0.164.0",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@types/three": "^0.164.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}
""",
    "vite.config.ts": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
""",
    "index.html": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DepthWizard</title>
  </head>
  <body class="bg-stone-900 text-stone-100 h-screen w-screen overflow-hidden">
    <div id="root" class="h-full w-full"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terrain: {
          dark: '#1a1d1a',
          brown: '#4a3f35',
          green: '#2d4a22'
        }
      }
    },
  },
  plugins: [],
}
""",
    "postcss.config.js": """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""",
    "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
""",
    "tsconfig.node.json": """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
""",
    "src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
}
""",
    "src/main.tsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
    "src/App.tsx": """import React from 'react';
import ThreeCanvas from './components/ThreeCanvas';
import { Upload } from 'lucide-react';

function App() {
  return (
    <div className="h-full flex flex-col">
      {/* Top Navigation */}
      <nav className="h-14 bg-terrain-dark border-b border-stone-700 flex items-center justify-between px-6">
        <div className="font-bold text-lg text-emerald-500">DepthWizard</div>
        <div className="flex gap-4">
          <button className="bg-emerald-700 hover:bg-emerald-600 px-4 py-1.5 rounded flex items-center gap-2 text-sm">
            <Upload size={16} />
            Upload Image
          </button>
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <aside className="w-72 bg-terrain-dark border-r border-stone-700 p-4 overflow-y-auto">
          <h2 className="text-sm font-semibold text-stone-400 mb-4 tracking-wider">DATA</h2>
          <div className="bg-stone-800 rounded p-4 border border-stone-700 text-sm">
            <p className="text-stone-400">No image loaded</p>
          </div>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 relative bg-stone-900">
          <ThreeCanvas />
        </main>

        {/* Right Info Panel */}
        <aside className="w-72 bg-terrain-dark border-l border-stone-700 p-4">
           <h2 className="text-sm font-semibold text-stone-400 mb-4 tracking-wider">INSPECTION</h2>
           <p className="text-sm text-stone-500">Click anywhere on the terrain to inspect.</p>
        </aside>
      </div>

      {/* Bottom Bar */}
      <footer className="h-8 bg-terrain-dark border-t border-stone-700 flex items-center px-4 text-xs text-stone-500 justify-between">
        <div>Ready</div>
        <div className="flex gap-4">
          <span>Alt: --</span>
          <span>Zoom: --</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
""",
    "src/components/ThreeCanvas.tsx": """import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import TerrainMesh from './TerrainMesh';

const ThreeCanvas = () => {
  return (
    <Canvas camera={{ position: [0, 5, 10], fov: 45 }}>
      <color attach="background" args={['#1c1917']} />
      
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1.5} castShadow />

      <TerrainMesh />

      <Grid infiniteGrid fadeDistance={50} sectionColor="#4a3f35" cellColor="#292524" />
      <OrbitControls makeDefault />
    </Canvas>
  );
};

export default ThreeCanvas;
""",
    "src/components/TerrainMesh.tsx": """import React from 'react';

const TerrainMesh = () => {
  // Placeholder terrain
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[10, 10, 32, 32]} />
      <meshStandardMaterial color="#4a3f35" wireframe={true} />
    </mesh>
  );
};

export default TerrainMesh;
"""
}

base_dir = "C:\\\\Users\\\\saanv\\\\OneDrive\\\\Desktop\\\\mini project\\\\project\\\\depth_wizard\\\\frontend"

for rel_path, content in files.items():
    full_path = os.path.join(base_dir, *rel_path.split("/"))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Frontend scaffolded.")
