export const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export type Weather = { location: { name: string; latitude: number; longitude: number }; timezone: string; current: { temperature_2m: number; relative_humidity_2m: number; precipitation: number; weather_code: number; wind_speed_10m: number }; daily: { time: string[]; weather_code: number[]; temperature_2m_max: number[]; temperature_2m_min: number[]; precipitation_sum: number[]; wind_speed_10m_max: number[] } };
export type RecordItem = { id: number; location: string; latitude: number; longitude: number; start_date: string; end_date: string; weather: Weather; created_at: string; updated_at: string };
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`${API}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } }); }
  catch { throw new Error('Cannot reach the weather service. Check that the backend is running and try again.'); }
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(typeof body.detail === 'string' ? body.detail : 'Please check your input and try again.'); }
  if (response.status === 204) return undefined as T;
  return response.json();
}
export function condition(code: number): [string, string] {
  if (code === 0) return ['☀', 'Clear'];
  if (code <= 3) return ['⛅', 'Partly cloudy'];
  if (code <= 48) return ['🌫', 'Fog'];
  if (code <= 67 || (code >= 80 && code <= 82)) return ['🌧', 'Rain'];
  if (code <= 77 || (code >= 85 && code <= 86)) return ['❄', 'Snow'];
  if (code >= 95) return ['⛈', 'Thunderstorms'];
  return ['☁', 'Cloudy'];
}
