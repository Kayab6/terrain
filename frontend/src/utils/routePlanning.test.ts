import { describe, expect, it } from 'vitest';
import { addCheckpoint, removeCheckpoint, reorderCheckpoint } from './routePlanning';

const checkpoints = [
  { lat: 27.9, lng: 86.9 },
  { lat: 28.0, lng: 87.0 },
  { lat: 28.1, lng: 87.1 },
];

describe('route checkpoint planning', () => {
  it('adds a checkpoint', () => {
    expect(addCheckpoint(checkpoints, { lat: 28.2, lng: 87.2 })).toHaveLength(4);
  });

  it('removes a checkpoint', () => {
    expect(removeCheckpoint(checkpoints, 1)).toEqual([checkpoints[0], checkpoints[2]]);
  });

  it('reorders checkpoints in both directions', () => {
    expect(reorderCheckpoint(checkpoints, 0, 1)).toEqual([checkpoints[1], checkpoints[0], checkpoints[2]]);
    expect(reorderCheckpoint(checkpoints, 2, 1)).toEqual(checkpoints);
  });
});
