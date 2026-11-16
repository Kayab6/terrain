import { describe, expect, it } from 'vitest';
import {
  coordinatesAreIdentical,
  terrainPosition,
  validateCoordinate,
} from './coordinates';

describe('map coordinates', () => {
  it('accepts a valid coordinate', () => {
    expect(validateCoordinate({ lat: 27.9881, lng: 86.925 })).toBeNull();
  });

  it('rejects latitude outside its range', () => {
    expect(validateCoordinate({ lat: 91, lng: 86 })).toContain('Latitude');
  });

  it('rejects duplicate points', () => {
    expect(
      coordinatesAreIdentical(
        { lat: 27.9881, lng: 86.925 },
        { lat: 27.9881, lng: 86.925 }
      )
    ).toBe(true);
  });

  it('maps geographic coordinates into terrain coordinates', () => {
    const position = terrainPosition(
      { lat: 28, lng: 87 },
      { west: 86, south: 27, east: 88, north: 29 }
    );
    expect(position.x).toBe(0);
    expect(position.z).toBe(0);
  });

  it('keeps separate route point roles independent', () => {
    const start = { lat: 27.9881, lng: 86.925 };
    const destination = { lat: 28.1016, lng: 87.40538 };
    expect(coordinatesAreIdentical(start, destination)).toBe(false);
    expect(validateCoordinate(destination)).toBeNull();
  });
});
