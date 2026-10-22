import React from 'react';
import {
  X,
  Compass,
  Zap,
  TrendingDown,
  Activity,
  Layers,
  ChevronRight,
  ShieldAlert,
  HelpCircle,
  FileText
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  Legend
} from 'recharts';

export default function XaiDiagnosticDrawer({
  isOpen,
  onClose,
  explainData,
  summaryTimeline,
  leadDay,
  isLoading
}) {
  if (!isOpen) return null;

  // Prepare variable attribution chart data
  const attributionChartData = explainData?.variable_attributions
    ? Object.entries(explainData.variable_attributions).map(([key, val]) => ({
        key,
        name: key.toUpperCase(),
        fullName: val.name,
        percentage: val.percentage,
        importance: val.importance_score,
      }))
    : [];

  // Lead-time decay timeline for the selected cell
  const timelineData = summaryTimeline?.map((t) => ({
    day: `D${t.lead_day}`,
    lead: t.lead_day,
    confidence: (t.mean_confidence * 100).toFixed(0),
    bustRisk: (t.max_bust_probability * 100).toFixed(0),
  })) || [];

  return (
    <aside className="w-96 xl:w-[420px] bg-meteor-900/95 backdrop-blur-xl border-l border-meteor-700/80 h-full flex flex-col z-30 shadow-2xl overflow-hidden select-none transition-all">
      {/* Drawer Header */}
      <div className="p-4 border-b border-meteor-700/60 flex items-center justify-between bg-meteor-950/60">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-red-950 border border-red-500/40 flex items-center justify-center text-red-400 shadow-[0_0_12px_rgba(239,68,68,0.3)]">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
              <span>XAI SYNOPTIC DIAGNOSTICS</span>
            </h2>
            <p className="text-[10px] font-mono text-cyan-400">
              CAPTUM INTEGRATED GRADIENTS ENGINE
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-meteor-800 text-slate-400 hover:text-slate-200 transition-colors border border-meteor-700/50"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
            <Activity className="w-8 h-8 text-cyan-400 animate-spin" />
            <p className="font-mono text-xs text-slate-300">Computing Gradient Attributions...</p>
            <p className="font-mono text-[11px] text-slate-500">Backpropagating across 5 synoptic tensors</p>
          </div>
        ) : explainData ? (
          <>
            {/* Coordinate & Subdivision Card */}
            <div className="bg-meteor-850 border border-meteor-700/80 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400 flex items-center gap-1">
                  <Compass className="w-3.5 h-3.5 text-cyan-400" />
                  Target Coordinate
                </span>
                <span className="text-cyan-300 font-bold bg-meteor-900 px-2 py-0.5 rounded border border-meteor-700">
                  {explainData.coordinate.lat}°N, {explainData.coordinate.lon}°E
                </span>
              </div>
              <div className="text-xs font-semibold text-slate-200">
                {explainData.subdivision}
              </div>

              {/* Current Point Metrics */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-meteor-700/50">
                <div className="bg-meteor-900/80 p-2 rounded-lg border border-meteor-750">
                  <span className="text-[10px] font-mono text-slate-400 block">Forecast Confidence</span>
                  <span
                    className={`text-base font-mono font-bold ${
                      explainData.confidence >= 0.7
                        ? 'text-emerald-400'
                        : explainData.confidence >= 0.45
                        ? 'text-amber-400'
                        : 'text-red-400'
                    }`}
                  >
                    {(explainData.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-meteor-900/80 p-2 rounded-lg border border-meteor-750">
                  <span className="text-[10px] font-mono text-slate-400 block">Bust Risk P(Bust)</span>
                  <span className="text-base font-mono font-bold text-red-400">
                    {(explainData.bust_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Primary Driver Banner */}
            <div className="bg-red-950/40 border border-red-500/40 rounded-xl p-3.5 space-y-1.5">
              <div className="flex items-center space-x-1.5 text-red-400 text-xs font-mono font-bold">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>PRIMARY SYNOPTIC FAILURE DRIVER</span>
              </div>
              <div className="text-sm font-bold text-slate-100 flex items-center justify-between">
                <span>{explainData.primary_driver}</span>
                <span className="font-mono text-amber-400 ml-2 font-extrabold text-base">
                  {explainData.primary_driver_pct}%
                </span>
              </div>
              <p className="text-[11px] text-slate-400 pt-0.5">
                Secondary Factor: <span className="text-slate-300 font-medium">{explainData.secondary_driver}</span> ({explainData.secondary_driver_pct}%)
              </p>
            </div>

            {/* Variable Attribution Chart */}
            <div className="bg-meteor-850 border border-meteor-700/80 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  Meteorological Sensitivity (%)
                </span>
                <span className="text-[10px] font-mono text-slate-400">Captum IG</span>
              </div>

              <div className="h-44 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={attributionChartData}
                    layout="vertical"
                    margin={{ top: 5, right: 15, left: 25, bottom: 5 }}
                  >
                    <XAxis
                      type="number"
                      domain={[0, 100]}
                      tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                      unit="%"
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      tick={{ fill: '#cbd5e1', fontSize: 10, fontFamily: 'monospace' }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-meteor-950 border border-slate-700 p-2 rounded shadow-xl text-xs font-mono">
                              <p className="text-cyan-300 font-bold">{data.fullName}</p>
                              <p className="text-slate-200 mt-1">
                                Sensitivity Contribution: <span className="text-amber-400 font-bold">{data.percentage}%</span>
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar
                      dataKey="percentage"
                      fill="#06b6d4"
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Operational Briefing Narrative */}
            <div className="bg-meteor-850 border border-meteor-700/80 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center space-x-2 text-xs font-mono font-bold text-cyan-300">
                <FileText className="w-4 h-4 text-cyan-400" />
                <span>OPERATIONAL FORECASTER BRIEFING</span>
              </div>
              <div className="bg-meteor-950/70 p-3 rounded-lg border border-meteor-750 text-xs leading-relaxed text-slate-300">
                "{explainData.meteorological_briefing}"
              </div>
            </div>

            {/* 10-Day Degradation Timeline */}
            <div className="bg-meteor-850 border border-meteor-700/80 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                  Day 1 to 10 Skill Degradation
                </span>
                <span className="text-[10px] font-mono text-cyan-400">Current: D{leadDay}</span>
              </div>

              <div className="h-44 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timelineData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="day"
                      tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                      unit="%"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0b1325',
                        borderColor: '#334155',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                      }}
                    />
                    <Legend
                      wrapperStyle={{ fontSize: '10px', fontFamily: 'monospace', paddingTop: '4px' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="confidence"
                      name="Confidence %"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="bustRisk"
                      name="Bust Risk %"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        ) : (
          <div className="py-20 text-center text-slate-400 text-xs font-mono space-y-2">
            <HelpCircle className="w-8 h-8 text-slate-500 mx-auto" />
            <p>Click any location on the map or select an Alert Zone polygon to trigger real-time XAI synoptic attribution.</p>
          </div>
        )}
      </div>
    </aside>
  );
}
