"use client";

import { useState, useEffect } from "react";
import { fetchComparative } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Cell, LineChart, Line,
} from "recharts";

interface CityComparative {
  city: string;
  avg_aqi: number;
  max_aqi: number;
  min_aqi: number;
  station_count: number;
  population: number;
  category: string;
  pollutants: { pm25: number; pm10: number; no2: number; so2: number; o3: number };
  compliance_rate: number;
  critical_stations: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  good: "#22c55e", satisfactory: "#84cc16", moderate: "#eab308",
  poor: "#f97316", very_poor: "#ef4444", severe: "#991b1b",
};

const CITY_SHORT: Record<string, string> = {
  Delhi: "DEL", Mumbai: "MUM", Kolkata: "KOL", Bengaluru: "BLR",
  Chennai: "CHN", Lucknow: "LKO", Patna: "PAT", Hyderabad: "HYD",
};

export default function ComparativeDashboard() {
  const [data, setData] = useState<CityComparative[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"aqi" | "pollutants" | "compliance">("aqi");

  useEffect(() => {
    fetchComparative()
      .then((res) => { setData(res.cities || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-zinc-500 text-sm">
        Loading comparative data...
      </div>
    );
  }

  if (!data.length) {
    return <div className="text-zinc-500 text-sm p-4">No comparative data available.</div>;
  }

  const barData = data.map((c) => ({
    name: CITY_SHORT[c.city] || c.city.slice(0, 3),
    city: c.city,
    aqi: c.avg_aqi,
    max: c.max_aqi,
    min: c.min_aqi,
    color: CATEGORY_COLORS[c.category] || "#71717a",
  }));

  const radarData = [
    { metric: "PM2.5", ...Object.fromEntries(data.slice(0, 4).map((c) => [c.city, c.pollutants.pm25])) },
    { metric: "PM10", ...Object.fromEntries(data.slice(0, 4).map((c) => [c.city, c.pollutants.pm10])) },
    { metric: "NO2", ...Object.fromEntries(data.slice(0, 4).map((c) => [c.city, c.pollutants.no2])) },
    { metric: "SO2", ...Object.fromEntries(data.slice(0, 4).map((c) => [c.city, c.pollutants.so2])) },
    { metric: "O3", ...Object.fromEntries(data.slice(0, 4).map((c) => [c.city, c.pollutants.o3])) },
  ];

  const radarCities = data.slice(0, 4);
  const radarColors = ["#06b6d4", "#f97316", "#a855f7", "#22c55e"];

  const complianceData = data.map((c) => ({
    name: CITY_SHORT[c.city] || c.city.slice(0, 3),
    city: c.city,
    compliance: c.compliance_rate,
    critical: c.critical_stations,
    stations: c.station_count,
  }));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-300">Multi-City Comparison</h3>
        <div className="flex gap-1">
          {(["aqi", "pollutants", "compliance"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`text-[10px] px-2 py-1 rounded ${
                view === v ? "bg-cyan-600 text-white" : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {v === "aqi" ? "AQI" : v === "pollutants" ? "Pollutants" : "Compliance"}
            </button>
          ))}
        </div>
      </div>

      {view === "aqi" && (
        <div className="bg-zinc-900/50 rounded-lg p-3 border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase mb-2 font-semibold">City-wise Average AQI</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 5, right: 5, bottom: 5, left: -15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#a1a1aa" }} />
              <YAxis tick={{ fontSize: 10, fill: "#a1a1aa" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "#e4e4e7" }}
                formatter={(value: number, name: string) => [value, name === "aqi" ? "Avg AQI" : name === "max" ? "Max" : "Min"]}
              />
              <Bar dataKey="aqi" name="Avg AQI" radius={[4, 4, 0, 0]}>
                {barData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Bar>
              <Bar dataKey="max" name="Max" fill="#ef444450" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-3 grid grid-cols-2 gap-2">
            {data.map((c) => (
              <div key={c.city} className="bg-zinc-800/50 rounded-md p-2 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-zinc-500">{c.city}</div>
                  <div className="text-sm font-bold" style={{ color: CATEGORY_COLORS[c.category] }}>
                    {c.avg_aqi}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[9px] text-zinc-500">{c.station_count} stn</div>
                  <div className="text-[9px] text-zinc-500">{(c.population / 1000000).toFixed(1)}M</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {view === "pollutants" && (
        <div className="bg-zinc-900/50 rounded-lg p-3 border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase mb-2 font-semibold">
            Pollutant Profile (Top 4 Cities)
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#3f3f46" />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: "#a1a1aa" }} />
              <PolarRadiusAxis tick={{ fontSize: 8, fill: "#71717a" }} />
              {radarCities.map((c, i) => (
                <Radar
                  key={c.city}
                  name={c.city}
                  dataKey={c.city}
                  stroke={radarColors[i]}
                  fill={radarColors[i]}
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
              ))}
              <Legend
                wrapperStyle={{ fontSize: 10 }}
                formatter={(value) => <span style={{ color: "#d4d4d8" }}>{value}</span>}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, fontSize: 11 }}
              />
            </RadarChart>
          </ResponsiveContainer>

          <div className="mt-2 space-y-1">
            {data.slice(0, 4).map((c, i) => (
              <div key={c.city} className="flex items-center gap-2 text-[10px]">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: radarColors[i] }} />
                <span className="text-zinc-400 w-20">{c.city}</span>
                <span className="text-zinc-500">PM2.5: {c.pollutants.pm25}</span>
                <span className="text-zinc-500">PM10: {c.pollutants.pm10}</span>
                <span className="text-zinc-500">NO2: {c.pollutants.no2}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {view === "compliance" && (
        <div className="bg-zinc-900/50 rounded-lg p-3 border border-zinc-800">
          <div className="text-[10px] text-zinc-500 uppercase mb-2 font-semibold">
            NAAQS Compliance Rate (% stations &le; 100 AQI)
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={complianceData} margin={{ top: 5, right: 5, bottom: 5, left: -15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#a1a1aa" }} />
              <YAxis tick={{ fontSize: 10, fill: "#a1a1aa" }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: 8, fontSize: 12 }}
                formatter={(value: number, name: string) => [
                  name === "compliance" ? `${value}%` : value,
                  name === "compliance" ? "Compliance" : "Critical Stations",
                ]}
              />
              <Bar dataKey="compliance" name="Compliance %" radius={[4, 4, 0, 0]}>
                {complianceData.map((entry, i) => (
                  <Cell key={i} fill={entry.compliance > 70 ? "#22c55e" : entry.compliance > 40 ? "#eab308" : "#ef4444"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-2 space-y-1">
            {data.map((c) => (
              <div key={c.city} className="flex items-center justify-between text-[10px] px-1">
                <span className="text-zinc-400">{c.city}</span>
                <div className="flex items-center gap-3">
                  <span className={c.compliance_rate > 70 ? "text-green-400" : c.compliance_rate > 40 ? "text-yellow-400" : "text-red-400"}>
                    {c.compliance_rate}% compliant
                  </span>
                  {c.critical_stations > 0 && (
                    <span className="text-red-400">{c.critical_stations} critical</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
