import { TerrainType } from '../utils/terrainGenerator';

export interface Landscape {
  id: string;
  name: string;
  subtitle?: string;
  terrainType: TerrainType;
  description: string;
  featured?: boolean;
  aiContext: string;
  location: string;
}

export const landscapes: Landscape[] = [
  {
    id: 'everest',
    name: 'Everest Region',
    subtitle: 'Himalayas, Nepal',
    terrainType: 'mountain',
    description: 'Extreme alpine environment featuring dramatic elevation changes, sharp ridges, and glacial valleys. Ideal for testing high-verticality scenarios.',
    featured: true,
    aiContext: 'This is the Everest Region, characterized by extreme altitude, steep peaks, and snow-covered rocky terrain. Key concerns here are avalanche risks, extreme weather, and difficult traversal.',
    location: '27.9881° N, 86.9250° E'
  },
  {
    id: 'highland',
    name: 'Highland Ridge',
    terrainType: 'highland',
    description: 'Rolling hills and mountain ridges with varied elevation. A balanced landscape for general terrain analysis.',
    aiContext: 'This is a Highland Ridge environment with rolling hills and vegetation. Good for general traversal and moderate elevation analysis.',
    location: 'Scottish Highlands'
  },
  {
    id: 'plains',
    name: 'Agricultural Plains',
    terrainType: 'plains',
    description: 'Relatively flat terrain with subtle elevation changes. Features agricultural field patterns and gentle slopes.',
    aiContext: 'These are Agricultural Plains. The terrain is flat with very subtle changes, ideal for farming. Key concerns might be flooding and soil moisture.',
    location: 'Great Plains, USA'
  },
  {
    id: 'barren',
    name: 'Barren Frontier',
    terrainType: 'barren',
    description: 'Arid, rocky landscape with significant erosion patterns. Excellent for testing rugged terrain navigation.',
    aiContext: 'This is a Barren Frontier. It is dry, rocky, and features erosion. Challenges include lack of water, heat, and rugged surface traversal.',
    location: 'Atacama Desert, Chile'
  },
  {
    id: 'river',
    name: 'River Valley',
    terrainType: 'river',
    description: 'A winding river channel cutting through a lush valley. Perfect for flood simulation and hydrological studies.',
    aiContext: 'This is a River Valley. It features a central water channel surrounded by elevated banks. Perfect for analyzing flood risks and watershed dynamics.',
    location: 'Amazon Basin, Brazil'
  }
];
