/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_MAP_STYLE_URL?: string;
  readonly VITE_MAP_PROVIDER_TOKEN?: string;
  readonly VITE_TERRAIN_SOURCE_URL?: string;
}
