import { describe, expect, it } from 'vitest';
import {
  applyProviderToken,
  DEFAULT_PITCH,
  resolveMapEnvironment,
} from './map';

describe('MapLibre configuration', () => {
  it('uses a default style and DEM source', () => {
    const config = resolveMapEnvironment({});
    expect(config.styleUrl).toBe('/map-styles/osm-3d.json');
    expect(config.terrainSourceUrl).toContain('{z}/{x}/{y}');
  });

  it('starts between 55 and 65 degrees pitch', () => {
    expect(DEFAULT_PITCH).toBeGreaterThanOrEqual(55);
    expect(DEFAULT_PITCH).toBeLessThanOrEqual(65);
  });

  it('substitutes provider tokens without hardcoding credentials', () => {
    expect(applyProviderToken('https://example/{token}/style.json', 'secret')).toContain('secret');
  });

  it('requires configuration values to be supplied by environment', () => {
    const config = resolveMapEnvironment({
      VITE_MAP_STYLE_URL: '',
      VITE_TERRAIN_SOURCE_URL: '',
      VITE_MAP_PROVIDER_TOKEN: '',
    });
    expect(config.styleUrl).toBeTruthy();
    expect(config.terrainSourceUrl).toBeTruthy();
  });
});
