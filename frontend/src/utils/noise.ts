// A simple seeded hash function for procedural generation
export function hash(x: number, y: number): number {
  // Multiply by large primes and take fractional part
  // The % 1 pattern works, but Math.sin can be used for pseudo-randomness
  // Ensure it works for negative inputs by using Math.abs or shifting
  const dot = x * 12.9898 + y * 78.233;
  const sin = Math.sin(dot) * 43758.5453;
  return sin - Math.floor(sin);
}

export function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}

export function lerp(a: number, b: number, t: number): number {
  return a + t * (b - a);
}

export function valueNoise(x: number, y: number): number {
  const i = Math.floor(x);
  const j = Math.floor(y);
  const fX = x - i;
  const fY = y - j;

  // Smooth interpolation
  const u = fX * fX * (3.0 - 2.0 * fX);
  const v = fY * fY * (3.0 - 2.0 * fY);

  // 4 corners
  const a = hash(i, j);
  const b = hash(i + 1, j);
  const c = hash(i, j + 1);
  const d = hash(i + 1, j + 1);

  // Mix
  const res = lerp(
    lerp(a, b, u),
    lerp(c, d, u),
    v
  );
  
  return res;
}

export function fbm(x: number, y: number, octaves: number = 4, lacunarity: number = 2.0, gain: number = 0.5): number {
  let amplitude = 1.0;
  let frequency = 1.0;
  let sum = 0.0;
  let maxAmplitude = 0.0;

  for (let i = 0; i < octaves; i++) {
    sum += valueNoise(x * frequency, y * frequency) * amplitude;
    maxAmplitude += amplitude;
    amplitude *= gain;
    frequency *= lacunarity;
  }

  return sum / maxAmplitude; // Normalize to 0-1
}
