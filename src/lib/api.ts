const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchStations(city?: string) {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await fetch(`${API_BASE}/api/stations${params}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch stations: ${res.status}`);
  return res.json();
}

export async function fetchStationDetail(stationId: string) {
  const res = await fetch(`${API_BASE}/api/stations/${stationId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch station: ${res.status}`);
  return res.json();
}

export async function fetchPredictions(stationId: string, hours: number = 72) {
  const res = await fetch(
    `${API_BASE}/api/predictions/${stationId}?hours=${hours}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Failed to fetch predictions: ${res.status}`);
  return res.json();
}

export async function fetchEnforcement(city?: string) {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await fetch(`${API_BASE}/api/enforcement${params}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch enforcement: ${res.status}`);
  return res.json();
}

export async function fetchCities() {
  const res = await fetch(`${API_BASE}/api/cities`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch cities: ${res.status}`);
  return res.json();
}

export async function fetchModelInfo() {
  const res = await fetch(`${API_BASE}/api/model/info`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch model info: ${res.status}`);
  return res.json();
}

export async function fetchSatelliteHotspots(city?: string) {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await fetch(`${API_BASE}/api/satellite/hotspots${params}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch satellite data: ${res.status}`);
  return res.json();
}

export async function fetchDispersion(city: string, windSpeed = 5, windDirection = 270) {
  const res = await fetch(
    `${API_BASE}/api/dispersion/${encodeURIComponent(city)}?wind_speed=${windSpeed}&wind_direction=${windDirection}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Failed to fetch dispersion: ${res.status}`);
  return res.json();
}

export async function fetchComparative() {
  const res = await fetch(`${API_BASE}/api/comparative`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch comparative data: ${res.status}`);
  return res.json();
}

export async function fetchAgentReport(city?: string) {
  const url = city
    ? `${API_BASE}/api/agents/report/${encodeURIComponent(city)}`
    : `${API_BASE}/api/agents/report`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch agent report: ${res.status}`);
  return res.json();
}

export async function downloadEnforcementPDF(city?: string) {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await fetch(`${API_BASE}/api/report/pdf${params}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to generate PDF: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `VayuDrishti_Enforcement_${city || "All"}_${new Date().toISOString().slice(0, 10)}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function fetchHealthImpact(city?: string) {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await fetch(`${API_BASE}/api/health-impact${params}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch health impact: ${res.status}`);
  return res.json();
}

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/api/alerts`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.status}`);
  return res.json();
}

export async function sendChatMessage(message: string, language = "en", city?: string) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, language, city }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}
