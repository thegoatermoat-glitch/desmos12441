const base = process.env.REACT_APP_BACKEND_URL;
if (!base) throw new Error('REACT_APP_BACKEND_URL is required');
export const API = `${base.replace(/\/+$/, '')}/api`;
export async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Something went wrong. Please try again.');
  }
  return response.status === 204 ? null : response.json();
}
export function readStorage(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
export function writeStorage(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Private storage can be unavailable. */ }
}