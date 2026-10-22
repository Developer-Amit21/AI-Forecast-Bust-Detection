import React, { useEffect, useState } from 'react';
import { Play, Pause, ChevronLeft, ChevronRight, Zap, Clock } from 'lucide-react';

export default function LeadTimeSlider({
  leadDay,
  onLeadDayChange,
  timeline,
  peakRiskDay
}) {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let interval = null;
    if (isPlaying) {
      interval = setInterval(() => {
        onLeadDayChange((prev) => (prev >= 10 ? 1 : prev + 1));
      }, 1400);
    }
    return () => clearInterval(interval);
  }, [isPlaying, onLeadDayChange]);

  const togglePlay = () => setIsPlaying(!isPlaying);

  return (
    <div className="bg-meteor-900/95 backdrop-blur-md border border-meteor-700/80 rounded-xl p-3 shadow-2xl flex flex-col md:flex-row items-center gap-4 select-none">
      {/* Playback Controls */}
      <div className="flex items-center space-x-2 shrink-0">
        <button
          onClick={() => onLeadDayChange(Math.max(1, leadDay - 1))}
          className="p-1.5 rounded-lg bg-meteor-800 hover:bg-meteor-700 text-slate-300 transition-colors border border-meteor-700"
          title="Previous Lead Day"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <button
          onClick={togglePlay}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-mono text-xs font-semibold tracking-wider transition-all shadow-md ${
            isPlaying
              ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-amber-900/40'
              : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-900/40'
          }`}
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5" />
              <span>PAUSE</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>ANIMATE</span>
            </>
          )}
        </button>

        <button
          onClick={() => onLeadDayChange(Math.min(10, leadDay + 1))}
          className="p-1.5 rounded-lg bg-meteor-800 hover:bg-meteor-700 text-slate-300 transition-colors border border-meteor-700"
          title="Next Lead Day"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Current Lead Day Indicator */}
      <div className="flex items-center space-x-2 font-mono shrink-0">
        <Clock className="w-4 h-4 text-cyan-400" />
        <span className="text-slate-400 text-xs">LEAD TIME:</span>
        <span className="text-base font-bold text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-2.5 py-0.5 rounded-md">
          DAY {leadDay} <span className="text-xs font-normal text-slate-400">({leadDay * 24}h)</span>
        </span>
      </div>

      {/* Timeline Steps with Bust Risk Badges */}
      <div className="flex-1 w-full flex items-center justify-between gap-1.5 px-2">
        {Array.from({ length: 10 }, (_, i) => i + 1).map((day) => {
          const daySummary = timeline?.find((t) => t.lead_day === day);
          const maxBust = daySummary?.max_bust_probability ?? 0.1;
          const isSelected = day === leadDay;
          const isPeak = day === peakRiskDay;

          // Color scale based on bust risk
          let dotColor = 'bg-emerald-500';
          if (maxBust >= 0.65) dotColor = 'bg-red-500';
          else if (maxBust >= 0.35) dotColor = 'bg-amber-500';

          return (
            <button
              key={day}
              onClick={() => onLeadDayChange(day)}
              className={`flex-1 flex flex-col items-center py-1.5 px-1 rounded-lg transition-all relative ${
                isSelected
                  ? 'bg-cyan-950/90 border border-cyan-500 text-cyan-200 shadow-[0_0_12px_rgba(6,182,212,0.3)]'
                  : 'hover:bg-meteor-800/80 text-slate-400 border border-transparent'
              }`}
            >
              {isPeak && (
                <span className="absolute -top-2 px-1 text-[9px] bg-red-600 text-white font-bold rounded-sm uppercase tracking-tighter scale-90">
                  PEAK
                </span>
              )}
              <span className={`text-[11px] font-mono font-bold ${isSelected ? 'text-cyan-300' : ''}`}>
                D{day}
              </span>
              <div className="flex items-center gap-1 mt-1">
                <span className={`w-2 h-2 rounded-full ${dotColor} ${isSelected ? 'ring-2 ring-white/50' : ''}`}></span>
              </div>
              <span className="text-[9px] font-mono text-slate-500 mt-0.5">
                {(maxBust * 100).toFixed(0)}%
              </span>
            </button>
          );
        })}
      </div>

      {/* Quick Jump to Peak Day Button */}
      {peakRiskDay && (
        <button
          onClick={() => onLeadDayChange(peakRiskDay)}
          className="shrink-0 flex items-center space-x-1 text-[11px] font-mono text-red-300 bg-red-950/60 hover:bg-red-900/60 border border-red-500/40 px-2.5 py-1.5 rounded-lg transition-colors"
          title="Jump directly to maximum forecast bust day"
        >
          <Zap className="w-3.5 h-3.5 text-red-400" />
          <span>JUMP TO PEAK (D{peakRiskDay})</span>
        </button>
      )}
    </div>
  );
}
