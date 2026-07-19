"use client";

import { useState, useEffect } from "react";
import { fetchHealthImpact } from "@/lib/api";
import { Heart, Skull, Stethoscope, Baby, Briefcase, IndianRupee, Loader2 } from "lucide-react";

interface CityImpact {
  city: string;
  population: number;
  current_pm25: number;
  current_aqi: number;
  who_exceedance_factor: number;
  health_metrics: {
    premature_deaths_annual: number;
    respiratory_hospitalizations: number;
    cardiovascular_events: number;
    childhood_asthma_attacks: number;
    life_years_lost: number;
    work_days_lost: number;
  };
  economic_impact: {
    total_cost_crore: number;
    mortality_cost_crore: number;
    healthcare_cost_crore: number;
    productivity_loss_crore: number;
  };
  risk_factors: {
    relative_risk_mortality: number;
    paf_mortality: number;
  };
}

interface HealthData {
  cities: CityImpact[];
  summary: {
    total_premature_deaths: number;
    total_economic_cost_crore: number;
    cities_analyzed: number;
  };
}

function formatNumber(n: number): string {
  if (n >= 100000) return `${(n / 100000).toFixed(1)}L`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString("en-IN");
}

export default function HealthImpact() {
  const [data, setData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetchHealthImpact()
      .then(setData)
      .catch((err) => console.error("Health impact error:", err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-zinc-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin mr-2" />
        Calculating health impact...
      </div>
    );
  }

  if (!data || !data.cities.length) {
    return <div className="text-zinc-500 text-sm p-4">No health data available.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-300">Health Impact Estimator</h3>
        <span className="text-[9px] text-zinc-600 bg-zinc-800 px-2 py-0.5 rounded">WHO/IHME Model</span>
      </div>

      {/* National summary */}
      <div className="bg-red-950/30 border border-red-900/40 rounded-lg p-3">
        <div className="text-[10px] text-red-400 uppercase font-semibold mb-2">
          Estimated Annual Burden — {data.summary.cities_analyzed} Cities
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-2xl font-black text-red-400">
              {formatNumber(data.summary.total_premature_deaths)}
            </div>
            <div className="text-[10px] text-zinc-500">Premature Deaths / Year</div>
          </div>
          <div>
            <div className="text-2xl font-black text-amber-400">
              ₹{formatNumber(data.summary.total_economic_cost_crore)} Cr
            </div>
            <div className="text-[10px] text-zinc-500">Economic Cost / Year</div>
          </div>
        </div>
      </div>

      {/* Per-city breakdown */}
      <div className="space-y-2">
        {data.cities.map((city) => {
          const isExpanded = expanded === city.city;
          const m = city.health_metrics;
          const e = city.economic_impact;

          return (
            <div key={city.city} className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
              <button
                onClick={() => setExpanded(isExpanded ? null : city.city)}
                className="w-full flex items-center justify-between p-3 text-left hover:bg-zinc-800/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
                    <Heart className="w-4 h-4 text-red-400" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-zinc-200">{city.city}</div>
                    <div className="text-[10px] text-zinc-500">
                      PM2.5: {city.current_pm25} µg/m³ · {city.who_exceedance_factor}x WHO limit
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-red-400">
                    {formatNumber(m.premature_deaths_annual)}
                  </div>
                  <div className="text-[9px] text-zinc-500">deaths/yr</div>
                </div>
              </button>

              {isExpanded && (
                <div className="px-3 pb-3 border-t border-zinc-800/50 pt-2 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-zinc-800/50 rounded-md p-2 flex items-center gap-2">
                      <Skull className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-bold text-zinc-200">{formatNumber(m.premature_deaths_annual)}</div>
                        <div className="text-[9px] text-zinc-500">Premature Deaths</div>
                      </div>
                    </div>
                    <div className="bg-zinc-800/50 rounded-md p-2 flex items-center gap-2">
                      <Stethoscope className="w-3.5 h-3.5 text-orange-400 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-bold text-zinc-200">{formatNumber(m.respiratory_hospitalizations)}</div>
                        <div className="text-[9px] text-zinc-500">Hospitalizations</div>
                      </div>
                    </div>
                    <div className="bg-zinc-800/50 rounded-md p-2 flex items-center gap-2">
                      <Baby className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-bold text-zinc-200">{formatNumber(m.childhood_asthma_attacks)}</div>
                        <div className="text-[9px] text-zinc-500">Child Asthma Attacks</div>
                      </div>
                    </div>
                    <div className="bg-zinc-800/50 rounded-md p-2 flex items-center gap-2">
                      <Briefcase className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                      <div>
                        <div className="text-xs font-bold text-zinc-200">{formatNumber(m.work_days_lost)}</div>
                        <div className="text-[9px] text-zinc-500">Work Days Lost</div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-zinc-800/30 rounded-md p-2">
                    <div className="flex items-center gap-1.5 mb-1">
                      <IndianRupee className="w-3 h-3 text-amber-400" />
                      <span className="text-[10px] font-semibold text-zinc-400">Economic Cost Breakdown</span>
                    </div>
                    <div className="space-y-1">
                      {[
                        { label: "Mortality cost", value: e.mortality_cost_crore, color: "#ef4444" },
                        { label: "Healthcare cost", value: e.healthcare_cost_crore, color: "#f97316" },
                        { label: "Productivity loss", value: e.productivity_loss_crore, color: "#eab308" },
                      ].map((item) => {
                        const pct = e.total_cost_crore > 0 ? (item.value / e.total_cost_crore) * 100 : 0;
                        return (
                          <div key={item.label}>
                            <div className="flex justify-between text-[10px]">
                              <span className="text-zinc-400">{item.label}</span>
                              <span className="text-zinc-300 font-mono">₹{formatNumber(item.value)} Cr</span>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-1 mt-0.5">
                              <div
                                className="h-1 rounded-full"
                                style={{ width: `${pct}%`, backgroundColor: item.color }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="text-[9px] text-zinc-600 leading-relaxed">
                    Relative risk: {city.risk_factors.relative_risk_mortality}x baseline mortality.
                    Life years lost: {formatNumber(m.life_years_lost)}/yr.
                    Based on WHO/GBD 2019 concentration-response functions.
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="text-[9px] text-zinc-600 leading-relaxed border-t border-zinc-800 pt-2">
        Estimates based on WHO/IHME Global Burden of Disease methodology. PM2.5 concentration-response
        functions from Burnett et al. (2018). Economic valuation uses India-adjusted VSL (₹1.87 Cr).
      </div>
    </div>
  );
}
