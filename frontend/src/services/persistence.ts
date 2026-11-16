export interface PersistenceStatus {
  enabled: boolean;
  connected: boolean;
  backend: 'memory' | 'mongodb';
  message: string;
}

export interface PersistedItem {
  id: string;
  [key: string]: unknown;
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000';

async function readJson(response: Response): Promise<unknown> {
  const payload = await response.json();
  if (!response.ok) {
    const message =
      typeof payload === 'object' &&
      payload !== null &&
      'message' in payload &&
      typeof payload.message === 'string'
        ? payload.message
        : 'Persistence request failed';
    throw new Error(message);
  }
  return payload;
}

export async function getPersistenceStatus(): Promise<PersistenceStatus> {
  const response = await fetch(`${apiBaseUrl}/api/persistence/status`);
  const payload = await readJson(response);
  return payload as PersistenceStatus;
}

export async function savePersistedItem(
  collection: 'routes' | 'scenarios',
  item: object,
): Promise<PersistedItem> {
  const response = await fetch(`${apiBaseUrl}/api/persistence/${collection}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  });
  const payload = await readJson(response);
  return (payload as { item: PersistedItem }).item;
}
