import React from 'react';
import { Layers, Eye, Sliders, Shield, CloudRain, Gauge, Wind, Compass, Globe } from 'lucide-react';

export default function ControlPanel({
  activeLayer,
  onSelectLayer,
  showAlerts,
  onToggleAlerts,
  gridOpacity,
  onOpacityChange,
  basemap = 'dark',
  onSelectBasemap,
}) {
  const layerOptions = [
    { id: 'bust_prob', name: 'Bust Probability P(Bust)', icon: Shield, unit: '0 to 100%' },
    { id: 'confidence', name: 'Forecast Confidence Grid', icon: Gauge, unit: '0 to 1.0' },
    { id: 'precip', name: '24-hr Rainfall Forecast', icon: CloudRain, unit: 'mm / 24h' },
    { id: 'mslp', name: 'MSLP Pressure Field', icon: Compass, unit: 'hPa' },
    { id: 'z500', name: '500 hPa Geopotential Ht', icon: Wind, unit: 'gpm' },
    { id: 'vort850', name: '850 hPa Vorticity Shear', icon: Wind, unit: '10⁻⁵ s⁻¹' },
  ];

  return (
    <div className="bg-meteor-900/95 backdrop-blur-md border border-meteor-700/80 rounded-xl p-3.5 shadow-2xl space-y-3.5 select-none w-72">
      {/* Title */}
      <div className="flex items-center justify-between border-b border-meteor-700/60 pb-2">
        <div className="flex items-center space-x-2 text-slate-200">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold uppercase tracking-wider font-mono">Layer Controls</span>
        </div>
        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-800">
          GIS MATRIX
        </span>
      </div>

      {/* Layer Select Buttons */}
      <div className="space-y-1">
        <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
          Active Synoptic Layer
        </label>
        <div className="grid grid-cols-1 gap-1 pt-1">
          {layerOptions.map((opt) => {
            const Icon = opt.icon;
            const isSelected = activeLayer === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => onSelectLayer(opt.id)}
                className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isSelected
                    ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/50 shadow-sm'
                    : 'text-slate-300 hover:bg-meteor-800 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{opt.name}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">{opt.unit}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Overlay Toggles */}
      <div className="pt-2 border-t border-meteor-700/60 space-y-2">
        <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
          Overlays & Visuals
        </label>

        {/* Basemap Style Toggle (No API Key Required) */}
        <div className="flex items-center justify-between text-xs text-slate-300">
          <span className="flex items-center space-x-1.5">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            <span>Basemap</span>
          </span>
          <div className="flex bg-meteor-800 rounded p-0.5 border border-meteor-700">
            <button
              onClick={() => onSelectBasemap('dark')}
              className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors ${
                basemap === 'dark' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Dark GIS
            </button>
            <button
              onClick={() => onSelectBasemap('satellite')}
              className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors ${
                basemap === 'satellite' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Satellite
            </button>
          </div>
        </div>

        {/* Alert Polygons Toggle */}
        <div className="flex items-center justify-between text-xs text-slate-300">
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
            <span>Alert Zone Polygons</span>
          </span>
          <button
            onClick={() => onToggleAlerts(!showAlerts)}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors border ${
              showAlerts
                ? 'bg-red-950 text-red-300 border-red-700 font-bold'
                : 'bg-meteor-800 text-slate-400 border-meteor-700'
            }`}
          >
            {showAlerts ? 'VISIBLE' : 'HIDDEN'}
          </button>
        </div>

        {/* Opacity Slider */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center space-x-1">
              <Sliders className="w-3 h-3" />
              <span>Grid Opacity</span>
            </span>
            <span className="font-mono text-cyan-400">{Math.round(gridOpacity * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.2"
            max="1.0"
            step="0.05"
            value={gridOpacity}
            onChange={(e) => onOpacityChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-meteor-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>
      </div>

      {/* Dynamic Color Scale Legend */}
      <div className="pt-2 border-t border-meteor-700/60 space-y-1.5">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
          Scale: {layerOptions.find((l) => l.id === activeLayer)?.name}
        </span>
        <div className="space-y-1">
          {activeLayer === 'bust_prob' && (
            <>
              <div className="h-2.5 rounded w-full bg-gradient-to-r from-slate-900 via-amber-500 to-red-600 shadow-inner"></div>
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>0% Low</span>
                <span>40% Watch</span>
                <span>70%+ Severe Bust</span>
              </div>
            </>
          )}
          {activeLayer === 'confidence' && (
            <>
              <div className="h-2.5 rounded w-full bg-gradient-to-r from-red-600 via-amber-400 to-emerald-500 shadow-inner"></div>
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>0.0 Complete Bust</span>
                <span>0.5 Moderate</span>
                <span>1.0 High Skill</span>
              </div>
            </>
          )}
          {activeLayer === 'precip' && (
            <>
              <div className="h-2.5 rounded w-full bg-gradient-to-r from-slate-900 via-cyan-500 via-blue-600 to-purple-600 shadow-inner"></div>
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>0 mm</span>
                <span>50 mm</span>
                <span>150+ mm</span>
              </div>
            </>
          )}
          {(activeLayer === 'mslp' || activeLayer === 'z500' || activeLayer === 'vort850') && (
            <>
              <div className="h-2.5 rounded w-full bg-gradient-to-r from-blue-700 via-emerald-600 to-amber-500 shadow-inner"></div>
              <div className="flex justify-between text-[10px] font-mono text-slate-400">
                <span>Low / Depression</span>
                <span>Mean</span>
                <span>High / Ridge</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
