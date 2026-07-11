export interface Station {
  id: string;
  name: string;
  city: string;
  lat: number;
  lng: number;
  aqi: number;
  pm25: number;
  pm10: number;
  no2: number;
  so2: number;
  co: number;
  o3: number;
  category: AQICategory;
  dominantPollutant: string;
  lastUpdated: string;
  sources: SourceAttribution[];
  trend: "improving" | "worsening" | "stable";
}

export interface SourceAttribution {
  source: string;
  percentage: number;
  confidence: number;
  color: string;
}

export interface Prediction {
  hour: number;
  label: string;
  aqi: number;
  category: AQICategory;
  confidence?: number;
}

export interface EnforcementAction {
  id: string;
  priority: "critical" | "high" | "medium";
  location: string;
  city: string;
  lat: number;
  lng: number;
  type: string;
  description: string;
  evidence: string[];
  estimatedImpact: string;
  status: "pending" | "dispatched" | "resolved";
}

export type AQICategory = "good" | "satisfactory" | "moderate" | "poor" | "very_poor" | "severe";

export interface CityStats {
  city: string;
  avgAqi: number;
  category: AQICategory;
  stationCount: number;
  criticalStations: number;
  population: string;
  trend: Station["trend"];
}

export function getAQICategory(aqi: number): AQICategory {
  if (aqi <= 50) return "good";
  if (aqi <= 100) return "satisfactory";
  if (aqi <= 200) return "moderate";
  if (aqi <= 300) return "poor";
  if (aqi <= 400) return "very_poor";
  return "severe";
}

export function getAQICategoryLabel(cat: AQICategory): string {
  const labels: Record<AQICategory, string> = {
    good: "Good",
    satisfactory: "Satisfactory",
    moderate: "Moderate",
    poor: "Poor",
    very_poor: "Very Poor",
    severe: "Severe",
  };
  return labels[cat];
}

export function getAQIColor(cat: AQICategory): string {
  const colors: Record<AQICategory, string> = {
    good: "#22c55e",
    satisfactory: "#84cc16",
    moderate: "#eab308",
    poor: "#f97316",
    very_poor: "#ef4444",
    severe: "#991b1b",
  };
  return colors[cat];
}

export function getAQIBgClass(cat: AQICategory): string {
  const classes: Record<AQICategory, string> = {
    good: "bg-green-500",
    satisfactory: "bg-lime-500",
    moderate: "bg-yellow-500",
    poor: "bg-orange-500",
    very_poor: "bg-red-500",
    severe: "bg-red-900",
  };
  return classes[cat];
}

export function getAQITextClass(cat: AQICategory): string {
  const classes: Record<AQICategory, string> = {
    good: "text-green-600",
    satisfactory: "text-lime-600",
    moderate: "text-yellow-600",
    poor: "text-orange-600",
    very_poor: "text-red-600",
    severe: "text-red-900",
  };
  return classes[cat];
}

const SOURCE_COLORS: Record<string, string> = {
  "Vehicular Emissions": "#ef4444",
  "Road Dust": "#f59e0b",
  "Construction Activity": "#8b5cf6",
  "Industrial Emissions": "#6366f1",
  "Biomass & Waste Burning": "#f97316",
  "Waste Burning": "#f97316",
  "Cooking/Heating": "#fb923c",
  "Secondary Particles": "#06b6d4",
  "Other": "#94a3b8",
};

export function mapApiStation(raw: Record<string, unknown>): Station {
  const aqi = (raw.aqi as number) || 0;
  const sources = Array.isArray(raw.sources)
    ? raw.sources.map((s: Record<string, unknown>) => ({
        source: (s.source as string) || "Unknown",
        percentage: (s.percentage as number) || 0,
        confidence: (s.confidence as number) || 0.5,
        color: SOURCE_COLORS[(s.source as string)] || "#94a3b8",
      }))
    : [];

  return {
    id: (raw.station_id as string) || (raw.id as string) || "",
    name: (raw.station_name as string) || (raw.name as string) || "",
    city: (raw.city as string) || "",
    lat: (raw.lat as number) || 0,
    lng: (raw.lng as number) || 0,
    aqi,
    pm25: (raw.pm25 as number) || 0,
    pm10: (raw.pm10 as number) || 0,
    no2: (raw.no2 as number) || 0,
    so2: (raw.so2 as number) || 0,
    co: (raw.co as number) || 0,
    o3: (raw.o3 as number) || 0,
    category: (raw.category as AQICategory) || getAQICategory(aqi),
    dominantPollutant: (raw.dominant_pollutant as string) || "PM2.5",
    lastUpdated: (raw.timestamp as string) || new Date().toISOString(),
    sources,
    trend: (raw.trend as Station["trend"]) || "stable",
  };
}

export function mapApiEnforcement(raw: Record<string, unknown>): EnforcementAction {
  return {
    id: (raw.id as string) || "",
    priority: (raw.priority as EnforcementAction["priority"]) || "medium",
    location: (raw.station_name as string) || (raw.location as string) || "",
    city: (raw.city as string) || "",
    lat: (raw.lat as number) || 0,
    lng: (raw.lng as number) || 0,
    type: (raw.action_type as string) || (raw.type as string) || "",
    description: (raw.description as string) || "",
    evidence: Array.isArray(raw.evidence) ? raw.evidence as string[] : [],
    estimatedImpact: `${raw.affected_population || "N/A"}. AQI reduction: ${raw.estimated_aqi_reduction || "N/A"}.`,
    status: (raw.status as EnforcementAction["status"]) || "pending",
  };
}

export function mapApiCity(raw: Record<string, unknown>): CityStats {
  const avgAqi = (raw.avg_aqi as number) || 0;
  return {
    city: (raw.city as string) || "",
    avgAqi,
    category: (raw.category as AQICategory) || getAQICategory(avgAqi),
    stationCount: (raw.station_count as number) || 0,
    criticalStations: (raw.critical_stations as number) || 0,
    population: (raw.population as string) || "N/A",
    trend: (raw.trend as Station["trend"]) || "stable",
  };
}

export function mapApiPrediction(raw: Record<string, unknown>, index: number): Prediction {
  const aqi = (raw.predicted_aqi as number) || (raw.aqi as number) || 0;
  return {
    hour: (raw.hour as number) ?? index,
    label: (raw.time_label as string) || (raw.label as string) || `+${index}h`,
    aqi: Math.round(aqi),
    category: (raw.category as AQICategory) || getAQICategory(aqi),
    confidence: raw.confidence as number | undefined,
  };
}
