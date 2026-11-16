import { LatLng } from './coordinates';

export function addCheckpoint(checkpoints: LatLng[], checkpoint: LatLng): LatLng[] {
  return [...checkpoints, checkpoint];
}

export function removeCheckpoint(checkpoints: LatLng[], index: number): LatLng[] {
  return checkpoints.filter((_, checkpointIndex) => checkpointIndex !== index);
}

export function reorderCheckpoint(checkpoints: LatLng[], index: number, direction: -1 | 1): LatLng[] {
  const target = index + direction;
  if (target < 0 || target >= checkpoints.length) return checkpoints;
  const reordered = [...checkpoints];
  [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
  return reordered;
}
