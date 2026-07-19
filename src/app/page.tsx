"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { Badge } from "@/components/ui/badge";
import {
  getAQIColor,
  getAQICategory,
  getAQICategoryLabel,
  mapApiStation,
  mapApiEnforcement,
  mapApiCity,
  type Station,
  type EnforcementAction,
  type CityStats,
} from "@/lib/aqi-data";
import StationDetail from "@/components/station-detail";
import EnforcementPanel from "@/components/enforcement-panel";
import CityOverview from "@/components/city-overview";
import CitizenChat from "@/components/citizen-chat";
import ComparativeDashboard from "@/components/comparative-dashboard";
import HealthImpact from "@/components/health-impact";
import AlertPanel from "@/components/alert-panel";
import HeroLanding from "@/components/hero-landing";
import {
  MapPin,
  Shield,
  BarChart3,
  Activity,
  Eye,
  Wind,
  RefreshCw,
  MessageCircle,
  GitCompare,
  Heart,
  Bell,
} from "lucide-react";
import { fetchStations, fetchEnforcement, fetchCities } from "@/lib/api";
import { AnimatedDock } from "@/components/ui/animated-dock";

const AQIMap = dynamic(() => import("@/components/aqi-map"), { ssr: false });

const cityCoords: Record<string, [number, number]> = {
  Delhi: [28.6139, 77.209],
  Mumbai: [19.076, 72.8777],
  Kolkata: [22.5726, 88.3639],
  Bengaluru: [12.9716, 77.5946],
  Chennai: [13.0827, 80.2707],
  Lucknow: [26.8467, 80.9462],
  Patna: [25.6093, 85.1376],
  Hyderabad: [17.385, 78.4867],
};

const NAV_ITEMS = [
  { id: "overview", icon: BarChart3, label: "Cities" },
  { id: "station", icon: MapPin, label: "Station" },
  { id: "enforce", icon: Shield, label: "Enforce" },
  { id: "compare", icon: GitCompare, label: "Compare" },
  { id: "health", icon: Heart, label: "Health" },
  { id: "alerts", icon: Bell, label: "Alerts" },
  { id: "chat", icon: MessageCircle, label: "Chat" },
] as const;

type PanelId = (typeof NAV_ITEMS)[number]["id"];

export default function Dashboard() {
  const [stations, setStations] = useState<Station[]>([]);
  const [cityStats, setCityStats] = useState<CityStats[]>([]);
  const [enforcementActions, setEnforcementActions] = useState<EnforcementAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [showHero, setShowHero] = useState(true);
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState<PanelId>("overview");
  const [mapCenter, setMapCenter] = useState<[number, number]>([22.5, 78.9]);
  const [mapZoom, setMapZoom] = useState(5);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      const [stationsRes, enforcementRes, citiesRes] = await Promise.all([
        fetchStations(),
        fetchEnforcement(),
        fetchCities(),
      ]);

      const newStations = (stationsRes.stations || []).map((s: Record<string, unknown>) => mapApiStation(s));
      setStations(newStations);
      setCityStats((citiesRes.cities || []).map((c: Record<string, unknown>) => mapApiCity(c)));
      setEnforcementActions((enforcementRes.actions || []).map((a: Record<string, unknown>) => mapApiEnforcement(a)));
      setSelectedStation((prev) => prev ? newStations.find((s) => s.id === prev.id) ?? null : null);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    intervalRef.current = setInterval(() => loadData(true), 5 * 60 * 1000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [loadData]);

  const filteredStations = selectedCity ? stations.filter((s) => s.city === selectedCity) : stations;

  const handleSelectCity = useCallback((city: string) => {
    setSelectedCity((prev) => (prev === city ? null : city));
    setSelectedStation(null);
    if (cityCoords[city]) {
      setMapCenter(cityCoords[city]);
      setMapZoom(11);
    }
  }, []);

  const handleSelectStation = useCallback((station: Station) => {
    setSelectedStation(station);
    setActivePanel("station");
  }, []);

  const avgNationalAqi = stations.length
    ? Math.round(stations.reduce((a, s) => a + s.aqi, 0) / stations.length)
    : 0;
  const severeCount = stations.filter((s) => s.aqi > 300).length;
  const poorCount = stations.filter((s) => s.aqi > 200).length;
  const uniqueCities = new Set(stations.map((s) => s.city)).size;

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-zinc-950 text-white">
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Wind className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-lg font-bold">VayuDrishti</h2>
          <p className="text-sm text-zinc-500 mt-1">Loading air quality intelligence...</p>
        </div>
      </div>
    );
  }

  if (showHero) {
    return (
      <HeroLanding
        onEnter={() => setShowHero(false)}
        stationCount={stations.length}
        cityCount={uniqueCities}
        avgAqi={avgNationalAqi}
      />
    );
  }

  return (
    <div className="h-screen flex bg-zinc-950 text-white overflow-hidden">

      {/* ── Animated Dock Rail ── */}
      <nav className="w-[68px] flex-shrink-0 bg-zinc-900 border-r border-zinc-800 flex flex-col items-center py-3">
        {/* Logo */}
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center mb-2">
          <Wind className="w-6 h-6 text-white" />
        </div>

        {/* Animated Dock */}
        <AnimatedDock
          items={NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return {
              id: item.id,
              label: item.label,
              Icon: <Icon className="w-[18px] h-[18px]" />,
              onClick: () => setActivePanel(item.id),
              isActive: activePanel === item.id,
            };
          })}
        />

        {/* Spacer */}
        <div className="flex-1" />

        {/* Bottom: Refresh + Live */}
        <button
          onClick={() => loadData(true)}
          className="w-10 h-10 rounded-lg flex items-center justify-center hover:bg-zinc-800 transition-colors"
          title={lastRefresh ? `Last: ${lastRefresh.toLocaleTimeString()}` : "Refresh"}
        >
          <RefreshCw className={`w-4 h-4 text-zinc-500 ${refreshing ? "animate-spin" : ""}`} />
        </button>

        <div className="w-10 h-10 rounded-lg flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" title="Live" />
        </div>
      </nav>

      {/* ── Content Panel ── */}
      <div className="w-[360px] flex-shrink-0 border-r border-zinc-800 flex flex-col overflow-hidden">
        {/* Panel Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
          <h2 className="text-sm font-bold text-zinc-200">
            {NAV_ITEMS.find((n) => n.id === activePanel)?.label}
          </h2>
          <div className="flex items-center gap-2">
            {activePanel === "overview" && (
              <span className="text-[10px] text-zinc-500">{stations.length} stations</span>
            )}
            {activePanel === "alerts" && (
              <Badge className="text-[9px] bg-red-500/20 text-red-400 border border-red-500/30 px-1.5 py-0">
                Live
              </Badge>
            )}
            {activePanel === "enforce" && (
              <Badge className="text-[9px] bg-red-500/20 text-red-400 border border-red-500/30 px-1.5 py-0">
                {enforcementActions.filter((a) => a.priority === "critical").length} critical
              </Badge>
            )}
          </div>
        </div>

        {/* Panel Content */}
        <div key={activePanel} className="flex-1 overflow-y-auto p-3 panel-enter">
          {activePanel === "overview" && (
            <CityOverview
              cities={cityStats}
              selectedCity={selectedCity}
              onSelectCity={handleSelectCity}
            />
          )}

          {activePanel === "station" && (
            selectedStation ? (
              <StationDetail station={selectedStation} />
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
                <Eye className="w-8 h-8 mb-3 opacity-50" />
                <p className="text-sm">Select a station on the map</p>
                <p className="text-xs text-zinc-600 mt-1">Click any marker to see detailed analysis</p>
              </div>
            )
          )}

          {activePanel === "enforce" && (
            <EnforcementPanel actions={enforcementActions} selectedCity={selectedCity} />
          )}

          {activePanel === "compare" && <ComparativeDashboard />}
          {activePanel === "health" && <HealthImpact />}
          {activePanel === "alerts" && <AlertPanel />}

          {activePanel === "chat" && (
            <div className="h-[calc(100vh-80px)]">
              <CitizenChat />
            </div>
          )}
        </div>
      </div>

      {/* ── Map + Stats Bar ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Stats Bar */}
        <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/30">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold text-zinc-300">VayuDrishti</h1>
            <span className="text-[10px] text-zinc-600">Urban Air Quality Intelligence</span>
          </div>
          <div className="flex items-center gap-5">
            <div className="text-center">
              <div className="text-[9px] text-zinc-500 uppercase">Avg AQI</div>
              <div className="text-base font-bold tabular-nums" style={{ color: getAQIColor(getAQICategory(avgNationalAqi)) }}>
                {avgNationalAqi}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[9px] text-zinc-500 uppercase">Stations</div>
              <div className="text-base font-bold text-zinc-300 tabular-nums">{stations.length}</div>
            </div>
            <div className="text-center">
              <div className="text-[9px] text-zinc-500 uppercase">Severe</div>
              <div className="text-base font-bold text-red-400 tabular-nums">{severeCount}</div>
            </div>
            <div className="text-center">
              <div className="text-[9px] text-zinc-500 uppercase">Poor+</div>
              <div className="text-base font-bold text-orange-400 tabular-nums">{poorCount}</div>
            </div>
            <Badge className="bg-green-500/20 text-green-400 border border-green-500/30 animate-pulse text-[10px]">
              <Activity className="w-3 h-3 mr-1" />
              Live
            </Badge>
          </div>
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          <AQIMap
            stations={filteredStations}
            selectedStation={selectedStation}
            onSelectStation={handleSelectStation}
            center={mapCenter}
            zoom={mapZoom}
          />

          {/* AQI Legend */}
          <div className="absolute bottom-4 left-4 bg-zinc-900/90 backdrop-blur-sm rounded-lg p-2.5 border border-zinc-800">
            <div className="text-[9px] text-zinc-500 uppercase font-semibold mb-1.5">AQI Scale</div>
            <div className="flex gap-1">
              {(["good", "satisfactory", "moderate", "poor", "very_poor", "severe"] as const).map((cat) => (
                <div key={cat} className="text-center">
                  <div className="w-5 h-2.5 rounded-sm" style={{ backgroundColor: getAQIColor(cat) }} />
                  <div className="text-[7px] text-zinc-500 mt-0.5">{getAQICategoryLabel(cat).split(" ")[0]}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Selected city */}
          {selectedCity && (
            <div className="absolute top-4 left-4 bg-zinc-900/90 backdrop-blur-sm rounded-lg px-3 py-2 border border-zinc-700">
              <div className="flex items-center gap-2">
                <MapPin className="w-3 h-3 text-cyan-400" />
                <span className="text-sm font-medium text-white">{selectedCity}</span>
                <button
                  onClick={() => { setSelectedCity(null); setMapCenter([22.5, 78.9]); setMapZoom(5); }}
                  className="text-xs text-zinc-400 hover:text-white ml-2"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
