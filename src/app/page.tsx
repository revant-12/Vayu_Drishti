"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  getAQIColor,
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
} from "lucide-react";
import { fetchStations, fetchEnforcement, fetchCities } from "@/lib/api";

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
  const [activeTab, setActiveTab] = useState("overview");
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

      const mappedStations = (stationsRes.stations || []).map(
        (s: Record<string, unknown>) => mapApiStation(s)
      );
      setStations(mappedStations);

      const mappedCities = (citiesRes.cities || []).map(
        (c: Record<string, unknown>) => mapApiCity(c)
      );
      setCityStats(mappedCities);

      const mappedEnforcement = (enforcementRes.actions || []).map(
        (a: Record<string, unknown>) => mapApiEnforcement(a)
      );
      setEnforcementActions(mappedEnforcement);

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
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loadData]);

  const filteredStations = selectedCity
    ? stations.filter((s) => s.city === selectedCity)
    : stations;

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
    setActiveTab("station");
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
          <h2 className="text-lg font-bold">VayuBudhi</h2>
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
    <div className="h-screen flex flex-col bg-zinc-950 text-white overflow-hidden">
      {/* Top Bar */}
      <header className="flex-shrink-0 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur-sm z-50">
        <div className="flex items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
              <Wind className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight">
                VayuBudhi
              </h1>
              <p className="text-[10px] text-zinc-500 uppercase tracking-widest">
                Urban Air Quality Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-4">
              <div className="text-center">
                <div className="text-[10px] text-zinc-500 uppercase">National Avg</div>
                <div className="text-lg font-bold" style={{ color: getAQIColor(stations[0]?.category || "moderate") }}>
                  {avgNationalAqi}
                </div>
              </div>
              <div className="w-px h-8 bg-zinc-800" />
              <div className="text-center">
                <div className="text-[10px] text-zinc-500 uppercase">Stations</div>
                <div className="text-lg font-bold text-zinc-300">{stations.length}</div>
              </div>
              <div className="w-px h-8 bg-zinc-800" />
              <div className="text-center">
                <div className="text-[10px] text-zinc-500 uppercase">Severe</div>
                <div className="text-lg font-bold text-red-400">{severeCount}</div>
              </div>
              <div className="w-px h-8 bg-zinc-800" />
              <div className="text-center">
                <div className="text-[10px] text-zinc-500 uppercase">Poor+</div>
                <div className="text-lg font-bold text-orange-400">{poorCount}</div>
              </div>
            </div>

            <button
              onClick={() => loadData(true)}
              className="p-1.5 rounded-md hover:bg-zinc-800 transition-colors"
              title={lastRefresh ? `Last refresh: ${lastRefresh.toLocaleTimeString()}` : "Refresh"}
            >
              <RefreshCw className={`w-4 h-4 text-zinc-400 ${refreshing ? "animate-spin" : ""}`} />
            </button>

            <Badge className="bg-green-500/20 text-green-400 border border-green-500/30 animate-pulse">
              <Activity className="w-3 h-3 mr-1" />
              Live
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <div className="w-[380px] flex-shrink-0 border-r border-zinc-800 overflow-y-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="flex-shrink-0 bg-zinc-900 border-b border-zinc-800 rounded-none h-auto p-1 mx-3 mt-3">
              <TabsTrigger value="overview" className="text-xs gap-1 data-[state=active]:bg-zinc-700">
                <BarChart3 className="w-3 h-3" />
                Cities
              </TabsTrigger>
              <TabsTrigger value="station" className="text-xs gap-1 data-[state=active]:bg-zinc-700">
                <MapPin className="w-3 h-3" />
                Station
              </TabsTrigger>
              <TabsTrigger value="enforce" className="text-xs gap-1 data-[state=active]:bg-zinc-700">
                <Shield className="w-3 h-3" />
                Enforce
              </TabsTrigger>
              <TabsTrigger value="compare" className="text-xs gap-1 data-[state=active]:bg-zinc-700">
                <GitCompare className="w-3 h-3" />
                Compare
              </TabsTrigger>
              <TabsTrigger value="chat" className="text-xs gap-1 data-[state=active]:bg-zinc-700">
                <MessageCircle className="w-3 h-3" />
                Chat
              </TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-y-auto p-3">
              <TabsContent value="overview" className="mt-0">
                <CityOverview
                  cities={cityStats}
                  selectedCity={selectedCity}
                  onSelectCity={handleSelectCity}
                />
              </TabsContent>

              <TabsContent value="station" className="mt-0">
                {selectedStation ? (
                  <StationDetail station={selectedStation} />
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
                    <Eye className="w-8 h-8 mb-3 opacity-50" />
                    <p className="text-sm">Select a station on the map</p>
                    <p className="text-xs text-zinc-600 mt-1">
                      Click any marker to see detailed analysis
                    </p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="enforce" className="mt-0">
                <EnforcementPanel actions={enforcementActions} selectedCity={selectedCity} />
              </TabsContent>

              <TabsContent value="compare" className="mt-0">
                <ComparativeDashboard />
              </TabsContent>

              <TabsContent value="chat" className="mt-0 h-[calc(100vh-140px)]">
                <CitizenChat />
              </TabsContent>
            </div>
          </Tabs>
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

          {/* Map Legend */}
          <div className="absolute bottom-4 left-4 bg-zinc-900/90 backdrop-blur-sm rounded-lg p-3 border border-zinc-800">
            <div className="text-[10px] text-zinc-500 uppercase font-semibold mb-2">AQI Scale</div>
            <div className="flex gap-1">
              {(["good", "satisfactory", "moderate", "poor", "very_poor", "severe"] as const).map(
                (cat) => (
                  <div key={cat} className="text-center">
                    <div
                      className="w-6 h-3 rounded-sm"
                      style={{ backgroundColor: getAQIColor(cat) }}
                    />
                    <div className="text-[8px] text-zinc-500 mt-0.5">
                      {getAQICategoryLabel(cat).split(" ")[0]}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Selected city indicator */}
          {selectedCity && (
            <div className="absolute top-4 left-4 bg-zinc-900/90 backdrop-blur-sm rounded-lg px-3 py-2 border border-zinc-700">
              <div className="flex items-center gap-2">
                <MapPin className="w-3 h-3 text-cyan-400" />
                <span className="text-sm font-medium text-white">{selectedCity}</span>
                <button
                  onClick={() => {
                    setSelectedCity(null);
                    setMapCenter([22.5, 78.9]);
                    setMapZoom(5);
                  }}
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
