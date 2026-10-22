import React from 'react';
import { AlertTriangle, TrendingDown, ShieldAlert, Compass, Sparkles } from 'lucide-react';

export default function SummaryStats({ summary, leadDay }) {
  if (!summary) return null;

  const currentDayStats = summary.timeline?.find((t) => t.lead_day === leadDay);

  return (
    <div className="bg-meteor-900/90 backdrop-blur border-b border-meteor-700/50 px-4 py-2 text-xs flex flex-wrap items-center justify-between gap-3 z-20">
      {/* Synoptic Briefing Banner */}
      <div className="flex items-center space-x-2 text-slate-300 max-w-xl">
        <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
        <span className="text-slate-400 font-mono text-[11px] shrink-0">SYNOPTIC STATUS:</span>
        <span className="text-slate-200 truncate font-medium">
          {summary.scenario_description}
        </span>
      </div>

      {/* Metric Indicators */}
      <div className="flex items-center space-x-4 ml-auto">
        {/* Day Lead Confidence */}
        <div className="flex items-center space-x-1.5 bg-meteor-850 px-2.5 py-1 rounded border border-meteor-700/70">
          <span className="text-slate-400 font-mono text-[11px]">Day {leadDay} Confidence:</span>
          <span
            className={`font-mono font-bold ${
              (currentDayStats?.mean_confidence ?? 1.0) >= 0.7
                ? 'text-emerald-400'
                : (currentDayStats?.mean_confidence ?? 1.0) >= 0.45
                ? 'text-amber-400'
                : 'text-red-400'
            }`}
          >
            {((currentDayStats?.mean_confidence ?? 0.8) * 100).toFixed(1)}%
          </span>
        </div>

        {/* Max Bust Risk */}
        <div className="flex items-center space-x-1.5 bg-meteor-850 px-2.5 py-1 rounded border border-meteor-700/70">
          <TrendingDown className="w-3.5 h-3.5 text-red-400" />
          <span className="text-slate-400 font-mono text-[11px]">Max Bust Prob:</span>
          <span className="font-mono font-bold text-red-400">
            {((currentDayStats?.max_bust_probability ?? 0.2) * 100).toFixed(1)}%
          </span>
        </div>

        {/* Peak Risk Day */}
        <div className="flex items-center space-x-1.5 bg-meteor-850 px-2.5 py-1 rounded border border-meteor-700/70">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400 font-mono text-[11px]">Peak Bust Day:</span>
          <span className="font-mono font-bold text-amber-300">
            Day {summary.peak_risk_day}
          </span>
        </div>

        {/* Active Alert Zones */}
        <div className="flex items-center space-x-1.5 bg-meteor-850 px-2.5 py-1 rounded border border-meteor-700/70">
          <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400 font-mono text-[11px]">Alert Zones (D{leadDay}):</span>
          <span className="font-mono font-bold text-cyan-300">
            {currentDayStats?.active_alert_zones ?? 0}
          </span>
        </div>

        {/* Critical Subdivisions Tag */}
        {summary.critical_subdivisions && summary.critical_subdivisions.length > 0 && (
          <div className="hidden xl:flex items-center space-x-1.5 text-[11px] text-slate-300">
            <Compass className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Hotspots:</span>
            <span className="text-amber-200/90 font-mono">
              {summary.critical_subdivisions.slice(0, 2).join(', ')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
