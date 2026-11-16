export const DEFAULT_PITCH = 60;
export const DEFAULT_BEARING = -20;
export const DEFAULT_ZOOM = 8;
export const DEFAULT_TERRAIN_EXAGGERATION = 1.35;

export interface MapEnvironmentConfig {
  styleUrl: string;
  terrainSourceUrl: string;
  providerToken: string;
}

export function resolveMapEnvironment(
  env: Partial<ImportMetaEnv> = import.meta.env
): MapEnvironmentConfig {
  return {
    styleUrl:
      env.VITE_MAP_STYLE_URL ||
      '/map-styles/osm-3d.json',
    terrainSourceUrl:
      env.VITE_TERRAIN_SOURCE_URL ||
      'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',
    providerToken: env.VITE_MAP_PROVIDER_TOKEN || '',
  };
}

export function applyProviderToken(url: string, token: string): string {
  return url.replace('{token}', encodeURIComponent(token));
}
