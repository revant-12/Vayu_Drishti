"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { Station } from "@/lib/aqi-data";
import { getAQIColor, getAQICategoryLabel } from "@/lib/aqi-data";
import { fetchSatelliteHotspots } from "@/lib/api";

interface AQIMapProps {
  stations: Station[];
  selectedStation: Station | null;
  onSelectStation: (station: Station) => void;
  center?: [number, number];
  zoom?: number;
}

interface Hotspot {
  id: string;
  lat: number;
  lng: number;
  brightness: number;
  frp: number;
  confidence: number;
  type: string;
  sector: string;
  name: string;
  severity: string;
  city: string;
}

export default function AQIMap({
  stations,
  selectedStation,
  onSelectStation,
  center = [22.5, 78.9],
  zoom = 5,
}: AQIMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);
  const fireMarkersRef = useRef<L.CircleMarker[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [showFires, setShowFires] = useState(false);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [firesLoading, setFiresLoading] = useState(false);

  const toggleFires = useCallback(async () => {
    if (showFires) {
      setShowFires(false);
      return;
    }
    setFiresLoading(true);
    try {
      const data = await fetchSatelliteHotspots();
      const allHotspots: Hotspot[] = [];
      for (const cityData of Object.values(data)) {
        const cd = cityData as { hotspots?: Hotspot[] };
        if (cd.hotspots) allHotspots.push(...cd.hotspots);
      }
      setHotspots(allHotspots);
      setShowFires(true);
    } catch (err) {
      console.error("Failed to load satellite data:", err);
    } finally {
      setFiresLoading(false);
    }
  }, [showFires]);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const container = mapRef.current;

    import("leaflet").then((L) => {
      // Guard against double-init in React strict mode
      if ((container as any)._leaflet_id) {
        return;
      }

      const map = L.map(container, {
        center,
        zoom,
        zoomControl: true,
        attributionControl: false,
      });

      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
      setLoaded(true);
    });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!loaded || !mapInstanceRef.current) return;
    mapInstanceRef.current.flyTo(center, zoom, { duration: 1.2 });
  }, [center, zoom, loaded]);

  useEffect(() => {
    if (!loaded || !mapInstanceRef.current) return;
    import("leaflet").then((L) => {
      if (!mapInstanceRef.current) return;
      const map = mapInstanceRef.current;

      // Clear old markers
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      stations.forEach((station) => {
        const color = getAQIColor(station.category);
        const isSelected = selectedStation?.id === station.id;
        const radius = isSelected ? 14 : station.aqi > 200 ? 10 : 7;

        const marker = L.circleMarker([station.lat, station.lng], {
          radius,
          fillColor: color,
          color: isSelected ? "#ffffff" : color,
          weight: isSelected ? 3 : 1.5,
          opacity: 1,
          fillOpacity: 0.85,
        }).addTo(map);

        const popup = L.popup({ className: "aqi-popup" }).setContent(`
          <div style="font-family: system-ui; padding: 4px;">
            <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px;">${station.name}</div>
            <div style="font-size: 12px; color: #9ca3af; margin-bottom: 6px;">${station.city}</div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 28px; font-weight: 800; color: ${color};">${station.aqi}</span>
              <span style="font-size: 11px; color: ${color}; font-weight: 600;">${getAQICategoryLabel(station.category)}</span>
            </div>
            <div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">
              PM2.5: ${station.pm25} · PM10: ${station.pm10} · NO₂: ${station.no2}
            </div>
          </div>
        `);

        marker.bindPopup(popup);
        marker.on("click", () => onSelectStation(station));

        // Pulse animation for severe stations
        if (station.aqi > 300) {
          const pulse = L.circleMarker([station.lat, station.lng], {
            radius: radius + 8,
            fillColor: color,
            color: color,
            weight: 1,
            opacity: 0.3,
            fillOpacity: 0.15,
          }).addTo(map);
          markersRef.current.push(pulse);
        }

        markersRef.current.push(marker);
      });
    });
  }, [stations, selectedStation, loaded, onSelectStation]);

  useEffect(() => {
    if (!loaded || !mapInstanceRef.current || !selectedStation) return;
    mapInstanceRef.current.flyTo([selectedStation.lat, selectedStation.lng], 12, {
      duration: 1.2,
    });
  }, [selectedStation, loaded]);

  useEffect(() => {
    if (!loaded || !mapInstanceRef.current) return;
    import("leaflet").then((L) => {
      if (!mapInstanceRef.current) return;
      const map = mapInstanceRef.current;
      fireMarkersRef.current.forEach((m) => m.remove());
      fireMarkersRef.current = [];

      if (!showFires) return;

      hotspots.forEach((h) => {
        const fireColor = h.type === "crop_burning" ? "#f97316"
          : h.type === "waste" ? "#a855f7"
          : h.type === "power_plant" ? "#ef4444"
          : "#f59e0b";

        const size = h.severity === "high" ? 9 : h.severity === "medium" ? 7 : 5;

        const marker = L.circleMarker([h.lat, h.lng], {
          radius: size,
          fillColor: fireColor,
          color: "#ffffff",
          weight: 1,
          opacity: 0.9,
          fillOpacity: 0.75,
        }).addTo(map);

        const typeLabel = h.type.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
        marker.bindPopup(`
          <div style="font-family: system-ui; padding: 4px; min-width: 180px;">
            <div style="font-weight: 700; font-size: 13px; color: ${fireColor};">🔥 ${typeLabel}</div>
            <div style="font-size: 12px; font-weight: 600; margin: 4px 0;">${h.name}</div>
            <div style="font-size: 11px; color: #9ca3af;">${h.sector}</div>
            <div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">
              FRP: ${h.frp} MW · Brightness: ${h.brightness}K
            </div>
            <div style="font-size: 11px; color: #9ca3af;">
              Confidence: ${h.confidence}% · Satellite: VIIRS
            </div>
          </div>
        `);

        if (h.severity === "high") {
          const glow = L.circleMarker([h.lat, h.lng], {
            radius: size + 6,
            fillColor: fireColor,
            color: fireColor,
            weight: 0,
            fillOpacity: 0.2,
          }).addTo(map);
          fireMarkersRef.current.push(glow);
        }

        fireMarkersRef.current.push(marker);
      });
    });
  }, [showFires, hotspots, loaded]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapRef} className="w-full h-full rounded-xl" />
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-900 rounded-xl">
          <div className="text-zinc-400 text-sm">Loading map...</div>
        </div>
      )}

      <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
        <button
          onClick={toggleFires}
          disabled={firesLoading}
          className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all ${
            showFires
              ? "bg-orange-600/90 border-orange-500 text-white shadow-lg shadow-orange-900/30"
              : "bg-zinc-900/90 border-zinc-700 text-zinc-300 hover:border-orange-500/50"
          }`}
        >
          {firesLoading ? "Loading..." : showFires ? "🔥 Fires ON" : "🛰️ Satellite"}
        </button>
      </div>

      {showFires && hotspots.length > 0 && (
        <div className="absolute bottom-4 right-4 bg-zinc-900/90 backdrop-blur-sm rounded-lg p-3 border border-zinc-800 z-[1000]">
          <div className="text-[10px] text-zinc-500 uppercase font-semibold mb-2">Thermal Hotspots</div>
          <div className="space-y-1">
            {[
              { color: "#ef4444", label: "Power Plant" },
              { color: "#f59e0b", label: "Industrial" },
              { color: "#a855f7", label: "Waste Site" },
              { color: "#f97316", label: "Crop Burning" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-[10px] text-zinc-400">{item.label}</span>
              </div>
            ))}
          </div>
          <div className="text-[9px] text-zinc-600 mt-2">
            Source: NASA FIRMS VIIRS · {hotspots.length} hotspots
          </div>
        </div>
      )}
    </div>
  );
}
