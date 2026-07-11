"use client";

import { type CityStats, getAQIColor, getAQICategoryLabel } from "@/lib/aqi-data";
import { TrendingUp, TrendingDown, Minus, Users, Radio } from "lucide-react";

interface CityOverviewProps {
  cities: CityStats[];
  selectedCity: string | null;
  onSelectCity: (city: string) => void;
}

export default function CityOverview({ cities, selectedCity, onSelectCity }: CityOverviewProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-zinc-300 mb-3">City Rankings</h3>
      {cities.map((city, i) => {
        const isSelected = selectedCity === city.city;
        const trendIcon = city.trend === "worsening"
          ? <TrendingUp className="w-3 h-3 text-red-500" />
          : city.trend === "improving"
          ? <TrendingDown className="w-3 h-3 text-green-500" />
          : <Minus className="w-3 h-3 text-yellow-500" />;

        return (
          <button
            key={city.city}
            onClick={() => onSelectCity(city.city)}
            className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${
              isSelected
                ? "bg-zinc-800 ring-1 ring-zinc-600"
                : "bg-zinc-900 hover:bg-zinc-800/70"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="text-lg font-black w-8 text-center"
                  style={{ color: getAQIColor(city.category) }}
                >
                  {i + 1}
                </div>
                <div>
                  <div className="text-sm font-semibold text-white">{city.city}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Users className="w-3 h-3 text-zinc-500" />
                    <span className="text-[10px] text-zinc-500">{city.population}</span>
                    <Radio className="w-3 h-3 text-zinc-500" />
                    <span className="text-[10px] text-zinc-500">{city.stationCount} stations</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 justify-end">
                  <span
                    className="text-xl font-bold"
                    style={{ color: getAQIColor(city.category) }}
                  >
                    {city.avgAqi}
                  </span>
                  {trendIcon}
                </div>
                <div
                  className="text-[10px] font-medium"
                  style={{ color: getAQIColor(city.category) }}
                >
                  {getAQICategoryLabel(city.category)}
                </div>
                {city.criticalStations > 0 && (
                  <div className="text-[10px] text-red-400 mt-0.5">
                    {city.criticalStations} critical
                  </div>
                )}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
