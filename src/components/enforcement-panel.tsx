"use client";

import { useState } from "react";
import { type EnforcementAction } from "@/lib/aqi-data";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, MapPin, FileText, Zap, CheckCircle, Truck, Download, Loader2 } from "lucide-react";
import { downloadEnforcementPDF } from "@/lib/api";

interface EnforcementPanelProps {
  actions: EnforcementAction[];
  selectedCity?: string | null;
}

const priorityConfig = {
  critical: { color: "bg-red-500/20 text-red-400 border-red-500/30", icon: AlertTriangle, label: "Critical" },
  high: { color: "bg-orange-500/20 text-orange-400 border-orange-500/30", icon: Zap, label: "High" },
  medium: { color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", icon: FileText, label: "Medium" },
};

const statusConfig = {
  pending: { color: "bg-zinc-700 text-zinc-300", icon: AlertTriangle, label: "Pending Action" },
  dispatched: { color: "bg-blue-500/20 text-blue-400", icon: Truck, label: "Team Dispatched" },
  resolved: { color: "bg-green-500/20 text-green-400", icon: CheckCircle, label: "Resolved" },
};

export default function EnforcementPanel({ actions, selectedCity }: EnforcementPanelProps) {
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    setDownloading(true);
    try {
      await downloadEnforcementPDF(selectedCity || undefined);
    } catch (err) {
      console.error("PDF download failed:", err);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-300">
          Enforcement Actions
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[10px] font-medium bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-600/30 disabled:opacity-50 transition-colors"
          >
            {downloading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Download className="w-3 h-3" />
            )}
            {downloading ? "Generating..." : "PDF Report"}
          </button>
          <Badge variant="outline" className="text-xs border-red-500/30 text-red-400">
            {actions.filter((a) => a.priority === "critical").length} Critical
          </Badge>
        </div>
      </div>

      {actions.map((action, idx) => {
        const priority = priorityConfig[action.priority];
        const status = statusConfig[action.status];
        const PriorityIcon = priority.icon;
        const StatusIcon = status.icon;

        return (
          <Card key={`${action.id}-${idx}`} className="border-0 bg-zinc-900 overflow-hidden">
            <CardContent className="p-4">
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <PriorityIcon className="w-4 h-4 text-current" />
                  <Badge className={`text-[10px] border ${priority.color}`}>
                    {priority.label}
                  </Badge>
                  <Badge className={`text-[10px] ${status.color}`}>
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {status.label}
                  </Badge>
                </div>
                <span className="text-[10px] text-zinc-600 font-mono">{action.id}</span>
              </div>

              {/* Type */}
              <h4 className="text-sm font-bold text-white mb-1">{action.type}</h4>

              {/* Location */}
              <div className="flex items-center gap-1 mb-2">
                <MapPin className="w-3 h-3 text-zinc-500" />
                <span className="text-xs text-zinc-400">{action.location}, {action.city}</span>
              </div>

              {/* Description */}
              <p className="text-xs text-zinc-400 mb-3 leading-relaxed">
                {action.description}
              </p>

              {/* Evidence */}
              <div className="bg-zinc-800/50 rounded-lg p-3 mb-3">
                <div className="text-[10px] uppercase text-zinc-500 font-semibold mb-2">
                  Supporting Evidence
                </div>
                <ul className="space-y-1">
                  {action.evidence.map((e, i) => (
                    <li key={i} className="text-[11px] text-zinc-400 flex items-start gap-2">
                      <span className="text-zinc-600 mt-0.5">●</span>
                      {e}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Impact */}
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
                <div className="text-[10px] uppercase text-amber-500/70 font-semibold mb-1">
                  Estimated Impact
                </div>
                <p className="text-xs text-amber-200/80">{action.estimatedImpact}</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
