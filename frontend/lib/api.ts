const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ViolationRecord {
  id: number;
  camera_id: str;
  track_id: number;
  started_at: string;
  ended_at?: string;
  snapshot_path?: string;
  confidence?: number;
}

export interface CameraRecord {
  id: string;
  name: string;
  source_type: string;
  source_url: string;
  status: string;
}

export async function fetchViolations(cameraId?: string, limit: number = 50): Promise<ViolationRecord[]> {
  try {
    const url = new URL(`${API_BASE}/api/violations`);
    if (cameraId) url.searchParams.append('camera_id', cameraId);
    url.searchParams.append('limit', limit.toString());

    const res = await fetch(url.toString(), { cache: 'no-store' });
    if (!res.ok) throw new Error('Failed to fetch violations');
    return await res.json();
  } catch (err) {
    console.error('API fetchViolations error:', err);
    return [];
  }
}

export async function fetchViolationStats() {
  try {
    const res = await fetch(`${API_BASE}/api/violations/stats`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Failed to fetch violation stats');
    return await res.json();
  } catch (err) {
    console.error('API fetchViolationStats error:', err);
    return { total_violations: 0, violations_today: 0, active_violations: 0 };
  }
}

export async function fetchCameras(): Promise<CameraRecord[]> {
  try {
    const res = await fetch(`${API_BASE}/api/cameras`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Failed to fetch cameras');
    return await res.json();
  } catch (err) {
    console.error('API fetchCameras error:', err);
    return [];
  }
}

export async function startStream(source: string = '0', cameraId: string = 'cam-01') {
  const res = await fetch(`${API_BASE}/api/streams/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, camera_id: cameraId }),
  });
  return await res.json();
}

export async function stopStream() {
  const res = await fetch(`${API_BASE}/api/streams/stop`, {
    method: 'POST',
  });
  return await res.json();
}

export function getExportUrl(): string {
  return `${API_BASE}/api/violations/export`;
}

export function getSnapshotUrl(path?: string): string {
  if (!path) return '';
  return path.startsWith('http') ? path : `${API_BASE}${path}`;
}
