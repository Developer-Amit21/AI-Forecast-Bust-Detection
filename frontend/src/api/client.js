/**
 * API Client for interacting with the AeroCast BustSentinel FastAPI Backend.
 */

const API_BASE = '/api/v1';

export async function fetchScenarios() {
  const res = await fetch(`${API_BASE}/forecast/scenarios`);
  if (!res.ok) throw new Error('Failed to fetch scenarios');
  return res.json();
}

export async function fetchForecastSummary(scenario = 'western_disturbance') {
  const res = await fetch(`${API_BASE}/forecast/summary?scenario=${encodeURIComponent(scenario)}`);
  if (!res.ok) throw new Error('Failed to fetch forecast summary');
  return res.json();
}

export async function fetchForecastGrid(leadDay = 5, scenario = 'western_disturbance') {
  const res = await fetch(`${API_BASE}/forecast/grid?lead_day=${leadDay}&scenario=${encodeURIComponent(scenario)}`);
  if (!res.ok) throw new Error(`Failed to fetch forecast grid for day ${leadDay}`);
  return res.json();
}

export async function fetchForecastExplain(leadDay = 5, lat = 30.0, lon = 74.0, scenario = 'western_disturbance') {
  const res = await fetch(
    `${API_BASE}/forecast/explain?lead_day=${leadDay}&lat=${lat}&lon=${lon}&scenario=${encodeURIComponent(scenario)}`
  );
  if (!res.ok) throw new Error('Failed to fetch synoptic XAI explanation');
  return res.json();
}

export async function uploadNetCDF(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/forecast/infer`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to upload NetCDF payload');
  }
  return res.json();
}
