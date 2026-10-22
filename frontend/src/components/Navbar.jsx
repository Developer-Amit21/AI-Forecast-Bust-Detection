import React from 'react';
import { CloudLightning, Activity, Radio, UploadCloud, ShieldAlert, Cpu } from 'lucide-react';

export default function Navbar({
  scenarios,
  selectedScenario,
  onSelectScenario,
  onOpenUpload,
  summary
}) {
  return (
    <header className="bg-meteor-900 border-b border-meteor-700/60 px-4 py-2.5 flex items-center justify-between shadow-lg z-30 select-none">
      {/* Brand & System Identity */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
          <CloudLightning className="w-5 h-5 text-cyan-400 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-bold tracking-wide text-slate-100 flex items-center">
              AEROCAST <span className="text-cyan-400 ml-1.5 font-extrabold">BUSTSENTINEL</span>
            </h1>
            <span className="text-[10px] font-mono uppercase bg-cyan-950 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.5 rounded tracking-wider">
              NWP-XAI v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
            <span>Domain: 5°N–38°N, 65°E–100°E (South Asia)</span>
            <span className="text-slate-600">•</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              00Z OPERATIONAL CYCLE
            </span>
          </p>
        </div>
      </div>

      {/* Scenario Selector & Engine Status */}
      <div className="flex items-center space-x-3">
        {/* Synoptic Scenario Switcher */}
        <div className="flex items-center space-x-2 bg-meteor-850 px-2.5 py-1.5 rounded-lg border border-meteor-700/80">
          <Radio className="w-4 h-4 text-amber-400 animate-pulse" />
          <span className="text-xs text-slate-400 uppercase font-mono tracking-wider">Scenario:</span>
          <select
            value={selectedScenario}
            onChange={(e) => onSelectScenario(e.target.value)}
            className="bg-meteor-950 text-xs text-slate-100 font-medium py-1 px-2 rounded border border-meteor-700 focus:outline-none focus:border-cyan-500 transition-colors cursor-pointer"
          >
            {scenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name}
              </option>
            ))}
          </select>
        </div>

        {/* Model Metrics Tag */}
        <div className="hidden lg:flex items-center space-x-3 text-xs font-mono bg-meteor-850 px-3 py-1.5 rounded-lg border border-meteor-700/80">
          <div className="flex items-center space-x-1.5 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>UNet-ConvLSTM</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1 text-emerald-400">
            <span>BSS: +0.798</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1 text-cyan-300">
            <span>ROC-AUC: 0.998</span>
          </div>
        </div>

        {/* NetCDF Upload Modal Button */}
        <button
          onClick={onOpenUpload}
          className="flex items-center space-x-1.5 text-xs font-medium bg-meteor-700 hover:bg-meteor-600 text-slate-100 px-3 py-1.5 rounded-lg border border-slate-600/50 transition-colors shadow-sm"
        >
          <UploadCloud className="w-4 h-4 text-cyan-400" />
          <span>Upload NetCDF</span>
        </button>
      </div>
    </header>
  );
}
