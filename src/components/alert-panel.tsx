"use client";

import { useState, useEffect } from "react";
import { fetchAlerts } from "@/lib/api";
import {
  AlertTriangle, AlertCircle, TrendingUp, TrendingDown,
  Zap, Globe, Flame, Skull, Bell, Loader2,
} from "lucide-react";

interface Alert {
  id: string;
  type: string;
  level: string;
  color: string;
  icon: string;
  title: string;
  station: string;
  city: string;
  aqi: number;
  message: string;
  severity: number;
  minutes_ago: number;
}

const ICON_MAP: Record<string, typeof AlertTriangle> = {
  "skull": Skull,
  "alert-triangle": AlertTriangle,
  "alert-circle": AlertCircle,
  "trending-up": TrendingUp,
  "trending-down": TrendingDown,
  "zap": Zap,
  "globe": Globe,
  "flame": Flame,
};

const LEVEL_STYLES: Record<string, string> = {
  emergency: "border-red-900/60 bg-red-950/40",
  critical: "border-red-800/50 bg-red-950/20",
  high: "border-red-700/40 bg-red-950/10",
  warning: "border-amber-700/40 bg-amber-950/10",
  info: "border-cyan-700/30 bg-cyan-950/10",
};

const LEVEL_BADGE: Record<string, string> = {
  emergency: "bg-red-600 text-white",
  critical: "bg-red-700 text-red-100",
  high: "bg-red-500/20 text-red-400",
  warning: "bg-amber-500/20 text-amber-400",
  info: "bg-cyan-500/20 text-cyan-400",
};

export default function AlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    fetchAlerts()
      .then((res) => setAlerts(res.alerts || []))
      .catch((err) => console.error("Alert error:", err))
      .finally(() => setLoading(false));

    const interval = setInterval(() => {
      fetchAlerts()
        .then((res) => setAlerts(res.alerts || []))
        .catch(() => {});
    }, 60_000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-zinc-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin mr-2" />
        Scanning for alerts...
      </div>
    );
  }

  const emergencyCount = alerts.filter((a) => a.level === "emergency" || a.level === "critical").length;
  const warningCount = alerts.filter((a) => a.level === "high" || a.level === "warning").length;

  const filtered = filter === "all"
    ? alerts
    : alerts.filter((a) => {
        if (filter === "critical") return a.level === "emergency" || a.level === "critical";
        if (filter === "warning") return a.level === "high" || a.level === "warning";
        return a.level === "info";
      });

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-zinc-300">Live Alerts</h3>
          {emergencyCount > 0 && (
            <span className="flex items-center gap-1 text-[10px] bg-red-600 text-white px-1.5 py-0.5 rounded-full animate-pulse">
              <Bell className="w-2.5 h-2.5" />
              {emergencyCount}
            </span>
          )}
        </div>
        <span className="text-[9px] text-zinc-600">{alerts.length} active</span>
      </div>

      {/* Summary bar */}
      <div className="flex gap-2">
        {[
          { key: "all", label: "All", count: alerts.length },
          { key: "critical", label: "Critical", count: emergencyCount },
          { key: "warning", label: "Warning", count: warningCount },
          { key: "info", label: "Info", count: alerts.length - emergencyCount - warningCount },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`text-[10px] px-2 py-1 rounded transition-colors ${
              filter === f.key
                ? "bg-cyan-600 text-white"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {f.label} ({f.count})
          </button>
        ))}
      </div>

      {/* Alert list */}
      <div className="space-y-2 max-h-[calc(100vh-240px)] overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-zinc-500 text-sm">
            No alerts in this category
          </div>
        ) : (
          filtered.map((alert) => {
            const Icon = ICON_MAP[alert.icon] || AlertCircle;
            const style = LEVEL_STYLES[alert.level] || LEVEL_STYLES.info;
            const badge = LEVEL_BADGE[alert.level] || LEVEL_BADGE.info;

            return (
              <div
                key={alert.id}
                className={`border rounded-lg p-3 ${style} transition-all`}
              >
                <div className="flex items-start gap-2.5">
                  <div
                    className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: `${alert.color}20` }}
                  >
                    <Icon className="w-3.5 h-3.5" style={{ color: alert.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${badge}`}>
                        {alert.level}
                      </span>
                      <span className="text-[10px] text-zinc-500">{alert.minutes_ago}m ago</span>
                    </div>
                    <div className="text-xs font-semibold text-zinc-200 mb-0.5">
                      {alert.title}
                    </div>
                    <div className="text-[10px] text-zinc-500 mb-1">
                      {alert.station} · {alert.city}
                      {alert.aqi > 0 && (
                        <span className="ml-1 font-mono" style={{ color: alert.color }}>
                          AQI {alert.aqi}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-zinc-400 leading-relaxed">
                      {alert.message}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
