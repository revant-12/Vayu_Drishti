"use client";

import { Station, getAQICategoryLabel, getAQIColor, getAQICategory, mapApiPrediction, type Prediction } from "@/lib/aqi-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Wind, Droplets, ThermometerSun, MapPin, Clock, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchPredictions } from "@/lib/api";

interface StationDetailProps {
  station: Station;
}

export default function StationDetail({ station }: StationDetailProps) {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loadingPredictions, setLoadingPredictions] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoadingPredictions(true);

    fetchPredictions(station.id, 72)
      .then((res) => {
        if (cancelled) return;
        const mapped = (res.predictions || []).map(
          (p: Record<string, unknown>, i: number) => mapApiPrediction(p, i)
        );
        setPredictions(mapped);
      })
      .catch((err) => {
        console.error("Failed to fetch predictions:", err);
        if (!cancelled) setPredictions([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingPredictions(false);
      });

    return () => { cancelled = true; };
  }, [station.id]);

  const next24 = predictions.slice(0, 24);

  const trendIcon = station.trend === "worsening"
    ? <TrendingUp className="w-4 h-4 text-red-500" />
    : station.trend === "improving"
    ? <TrendingDown className="w-4 h-4 text-green-500" />
    : <Minus className="w-4 h-4 text-yellow-500" />;

  const maxPredicted = next24.length ? Math.max(...next24.map((p) => p.aqi)) : 0;
  const minPredicted = next24.length ? Math.min(...next24.map((p) => p.aqi)) : 0;
  const peakHour = next24.find((p) => p.aqi === maxPredicted);

  return (
    <div className="space-y-4">
      {/* Main AQI Display */}
      <Card className="border-0 bg-zinc-900">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <MapPin className="w-4 h-4 text-zinc-400" />
                <span className="text-sm text-zinc-400">{station.city}</span>
              </div>
              <h2 className="text-xl font-bold text-white">{station.name}</h2>
              <div className="flex items-center gap-2 mt-1">
                <Clock className="w-3 h-3 text-zinc-500" />
                <span className="text-xs text-zinc-500">
                  {new Date(station.lastUpdated).toLocaleTimeString("en-IN")}
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-5xl font-black" style={{ color: getAQIColor(station.category) }}>
                {station.aqi}
              </div>
              <Badge
                className="mt-1 text-white border-0"
                style={{ backgroundColor: getAQIColor(station.category) }}
              >
                {getAQICategoryLabel(station.category)}
              </Badge>
              <div className="flex items-center gap-1 mt-2 justify-end">
                {trendIcon}
                <span className="text-xs text-zinc-400 capitalize">{station.trend}</span>
              </div>
            </div>
          </div>

          {/* Pollutant Breakdown */}
          <div className="grid grid-cols-3 gap-3 mt-5">
            {[
              { label: "PM2.5", value: station.pm25, unit: "µg/m³", icon: Wind },
              { label: "PM10", value: station.pm10, unit: "µg/m³", icon: Droplets },
              { label: "NO₂", value: station.no2, unit: "ppb", icon: ThermometerSun },
            ].map((p) => (
              <div key={p.label} className="bg-zinc-800 rounded-lg p-3 text-center">
                <p.icon className="w-4 h-4 text-zinc-500 mx-auto mb-1" />
                <div className="text-lg font-bold text-white">{Math.round(p.value)}</div>
                <div className="text-[10px] text-zinc-500">{p.label} ({p.unit})</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Source Attribution */}
      <Card className="border-0 bg-zinc-900">
        <CardHeader className="pb-2 pt-4 px-5">
          <CardTitle className="text-sm font-semibold text-zinc-300">Source Attribution</CardTitle>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          <div className="space-y-3">
            {station.sources.map((src) => (
              <div key={src.source}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-zinc-300">{src.source}</span>
                  <span className="text-zinc-400 font-mono">{Math.round(src.percentage)}%</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-700"
                    style={{
                      width: `${src.percentage}%`,
                      backgroundColor: src.color,
                      opacity: 0.5 + src.confidence * 0.5,
                    }}
                  />
                </div>
                <div className="text-[10px] text-zinc-600 mt-0.5">
                  Confidence: {Math.round(src.confidence * 100)}%
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 24h Prediction */}
      <Card className="border-0 bg-zinc-900">
        <CardHeader className="pb-2 pt-4 px-5">
          <CardTitle className="text-sm font-semibold text-zinc-300">24-Hour Forecast</CardTitle>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          {loadingPredictions ? (
            <div className="flex items-center justify-center h-24 text-zinc-500">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              <span className="text-xs">Loading ML predictions...</span>
            </div>
          ) : next24.length === 0 ? (
            <div className="text-xs text-zinc-500 text-center py-6">No predictions available</div>
          ) : (
            <>
              <div className="flex items-center gap-4 mb-3">
                <div className="text-center">
                  <div className="text-[10px] text-zinc-500 uppercase">Peak</div>
                  <div className="text-lg font-bold text-red-400">{maxPredicted}</div>
                  <div className="text-[10px] text-zinc-500">{peakHour?.label}</div>
                </div>
                <div className="text-center">
                  <div className="text-[10px] text-zinc-500 uppercase">Low</div>
                  <div className="text-lg font-bold text-green-400">{minPredicted}</div>
                </div>
              </div>
              {/* Mini bar chart */}
              <div className="flex items-end gap-[2px] h-16">
                {next24.map((p, i) => {
                  const height = Math.max(4, (p.aqi / 500) * 64);
                  return (
                    <div
                      key={i}
                      className="flex-1 rounded-t-sm transition-all duration-300"
                      style={{
                        height: `${height}px`,
                        backgroundColor: getAQIColor(p.category),
                        opacity: 0.7,
                      }}
                      title={`${p.label}: AQI ${p.aqi}`}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between text-[10px] text-zinc-600 mt-1">
                <span>Now</span>
                <span>+6h</span>
                <span>+12h</span>
                <span>+18h</span>
                <span>+24h</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
