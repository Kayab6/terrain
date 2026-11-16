import { fbm, smoothstep } from './noise';

export type TerrainType = 'highland' | 'plains' | 'barren' | 'river' | 'mountain';

export interface TerrainData {
  heightData: Float32Array;
  canvas: HTMLCanvasElement;
  resolution: number;
  stats: {
    minElevation: number;
    maxElevation: number;
    avgElevation: number;
  };
}

export function generateHeightmap(type: TerrainType, resolution: number): Float32Array {
  const size = resolution + 1;
  const data = new Float32Array(size * size);
  
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      const nx = col / resolution;
      const ny = row / resolution;
      
      let height = 0;
      
      // Different noise generation per type
      if (type === 'highland') {
        height = fbm(nx * 3, ny * 3, 6, 2.0, 0.5);
        height = Math.pow(height, 1.2); // steeper hills
      } else if (type === 'plains') {
        height = fbm(nx * 2, ny * 2, 4, 2.0, 0.3) * 0.3; // flatter
        height += 0.1; // base elevation
      } else if (type === 'barren') {
        height = fbm(nx * 4, ny * 4, 5, 2.2, 0.4);
        height = Math.abs(height * 2 - 1); // ridges
      } else if (type === 'river') {
        const baseHeight = fbm(nx * 3, ny * 3, 5, 2.0, 0.4);
        // River channel
        const riverPath = 0.5 + Math.sin(ny * Math.PI * 2) * 0.1;
        const distToRiver = Math.abs(nx - riverPath);
        const riverDepth = smoothstep(0.0, 0.1, distToRiver);
        height = baseHeight * riverDepth;
      } else if (type === 'mountain') { // Everest
        height = fbm(nx * 4, ny * 4, 8, 2.0, 0.55);
        height = Math.pow(height, 1.5); // Very steep
        height += fbm(nx * 10, ny * 10, 4) * 0.1; // small detail
      }
      
      // Ensure height is > 0
      height = Math.max(0, height);
      
      // Apply edge fade to prevent vertical walls
      const borderFade = Math.min(nx, 1 - nx, ny, 1 - ny) / 0.05;
      height *= Math.min(1, borderFade);
      
      data[row * size + col] = height;
    }
  }
  
  return data;
}

export function generateCanvasTexture(type: TerrainType, heightData: Float32Array, resolution: number): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = resolution;
  canvas.height = resolution;
  const ctx = canvas.getContext('2d');
  if (!ctx) return canvas;
  
  const size = resolution + 1;
  const imageData = ctx.createImageData(resolution, resolution);
  
  // Define colormaps per type
  const getColor = (h: number): [number, number, number] => {
    if (type === 'highland') {
      if (h < 0.2) return [60, 100, 40]; // low green
      if (h < 0.6) return [100, 120, 60]; // mid green
      if (h < 0.8) return [150, 140, 100]; // rock
      return [200, 200, 200]; // snow
    } else if (type === 'plains') {
      if (h < 0.15) return [120, 150, 80]; // farm green
      if (h < 0.2) return [180, 170, 100]; // dry grass
      return [140, 160, 90]; 
    } else if (type === 'barren') {
      if (h < 0.3) return [180, 150, 120]; // sand
      if (h < 0.6) return [150, 110, 80]; // red rock
      return [100, 80, 70]; // dark rock
    } else if (type === 'river') {
      if (h < 0.05) return [40, 80, 150]; // water
      if (h < 0.1) return [150, 140, 100]; // sand bank
      if (h < 0.5) return [70, 110, 50]; // lush
      return [100, 120, 70];
    } else if (type === 'mountain') {
      if (h < 0.3) return [80, 90, 80]; // dark rock
      if (h < 0.6) return [120, 130, 130]; // gray rock
      return [240, 250, 255]; // snow
    }
    return [100, 100, 100];
  };

  for (let y = 0; y < resolution; y++) {
    for (let x = 0; x < resolution; x++) {
      const idx = y * size + x;
      const h = heightData[idx];
      const color = getColor(h);
      
      const pxIdx = (y * resolution + x) * 4;
      imageData.data[pxIdx] = color[0];
      imageData.data[pxIdx + 1] = color[1];
      imageData.data[pxIdx + 2] = color[2];
      imageData.data[pxIdx + 3] = 255;
    }
  }
  
  ctx.putImageData(imageData, 0, 0);
  return canvas;
}

export function generateTerrainData(type: TerrainType, resolution: number = 256): TerrainData {
  const heightData = generateHeightmap(type, resolution);
  const canvas = generateCanvasTexture(type, heightData, resolution);
  
  let minElevation = Infinity;
  let maxElevation = -Infinity;
  let sum = 0;
  
  for (let i = 0; i < heightData.length; i++) {
    const h = heightData[i];
    if (h < minElevation) minElevation = h;
    if (h > maxElevation) maxElevation = h;
    sum += h;
  }
  
  // Real-world scaling for stats display
  const scaleMultipliers: Record<TerrainType, number> = {
    highland: 1500,
    plains: 200,
    barren: 800,
    river: 400,
    mountain: 8848
  };
  
  const mult = scaleMultipliers[type];
  
  return {
    heightData,
    canvas,
    resolution,
    stats: {
      minElevation: minElevation * mult,
      maxElevation: maxElevation * mult,
      avgElevation: (sum / heightData.length) * mult
    }
  };
}
