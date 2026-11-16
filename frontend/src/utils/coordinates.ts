export interface LatLng {
  lat: number;
  lng: number;
}

export function validateCoordinate(value: LatLng): string | null {
  if (!Number.isFinite(value.lat) || !Number.isFinite(value.lng)) {
    return 'Latitude and longitude must be valid numbers.';
  }
  if (value.lat < -90 || value.lat > 90) {
    return 'Latitude must be between -90 and 90.';
  }
  if (value.lng < -180 || value.lng > 180) {
    return 'Longitude must be between -180 and 180.';
  }
  return null;
}

export function coordinatesAreIdentical(
  first: LatLng,
  second: LatLng,
  tolerance = 0.000001
) {
  return (
    Math.abs(first.lat - second.lat) <= tolerance &&
    Math.abs(first.lng - second.lng) <= tolerance
  );
}

export interface GeographicBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export function terrainPosition(
  point: LatLng,
  bounds: GeographicBounds,
  terrainSize = 10
) {
  const x = ((point.lng - bounds.west) / (bounds.east - bounds.west) - 0.5) * terrainSize;
  const z = ((point.lat - bounds.south) / (bounds.north - bounds.south) - 0.5) * terrainSize;
  if (![x, z].every(Number.isFinite)) {
    throw new Error('Coordinates cannot be mapped outside the terrain bounds.');
  }
  return { x, z };
}
