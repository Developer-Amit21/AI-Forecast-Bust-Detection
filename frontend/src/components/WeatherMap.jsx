import React, { useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  useMapEvents,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

// Custom Map Click Listener Component
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Canvas-based Meteorological Grid Overlay Layer
function GridOverlay({ gridData, activeLayer, opacity, lats, lons }) {
  const map = useMap();
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!gridData || !lats || !lons || !map) return;

    let canvasLayer = L.gridLayer({
      tileSize: 256,
      opacity: opacity,
      zIndex: 10,
    });

    // Helper: color interpolation for meteorology
    const getColor = (val, layer) => {
      if (layer === 'bust_prob') {
        // 0.0 (dark) -> 0.4 (amber) -> 0.8+ (crimson)
        if (val < 0.2) return `rgba(15, 23, 42, 0.2)`;
        if (val < 0.45) return `rgba(245, 158, 11, ${(val * 1.5).toFixed(2)})`;
        return `rgba(239, 68, 68, ${Math.min(0.95, 0.4 + val * 0.55).toFixed(2)})`;
      } else if (layer === 'confidence') {
        // 0.0 (red) -> 0.5 (amber) -> 1.0 (emerald)
        if (val > 0.7) return `rgba(16, 185, 129, ${(val * 0.7).toFixed(2)})`;
        if (val > 0.45) return `rgba(245, 158, 11, 0.65)`;
        return `rgba(239, 68, 68, ${(0.85 - val * 0.5).toFixed(2)})`;
      } else if (layer === 'precip') {
        // 0 to 150+ mm
        if (val < 5.0) return `rgba(15, 23, 42, 0.1)`;
        if (val < 35.0) return `rgba(6, 182, 212, ${(val / 50.0).toFixed(2)})`;
        if (val < 80.0) return `rgba(37, 99, 235, 0.75)`;
        return `rgba(147, 51, 234, 0.85)`;
      } else if (layer === 'mslp') {
        // 995 to 1018 hPa
        const norm = Math.max(0, Math.min(1, (val - 996.0) / 20.0));
        return `rgba(${Math.round((1 - norm) * 220 + 20)}, ${Math.round(norm * 180)}, 240, 0.65)`;
      } else {
        // z500 or vort
        return `rgba(56, 189, 248, 0.55)`;
      }
    };

    // Create custom Canvas layer over India domain
    const canvas = L.DomUtil.create('canvas', 'meteor-grid-canvas');
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '400';
    map.getPanes().overlayPane.appendChild(canvas);

    const render = () => {
      const size = map.getSize();
      canvas.width = size.x;
      canvas.height = size.y;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, size.x, size.y);

      const topLeft = map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setPosition(canvas, topLeft);

      let gridArray = null;
      if (activeLayer === 'bust_prob') gridArray = gridData.bust_prob_grid;
      else if (activeLayer === 'confidence') gridArray = gridData.confidence_grid;
      else if (activeLayer === 'precip') gridArray = gridData.precip_grid;
      else if (activeLayer === 'mslp') gridArray = gridData.mslp_grid;
      else if (activeLayer === 'z500') gridArray = gridData.z500_grid;
      else if (activeLayer === 'vort850') gridArray = gridData.vort850_grid;

      if (!gridArray) return;

      const nLat = lats.length;
      const nLon = lons.length;

      ctx.globalAlpha = opacity;

      // Draw grid cells with anti-aliasing
      for (let r = 0; r < nLat; r++) {
        for (let c = 0; c < nLon; c++) {
          const lat = lats[r];
          const lon = lons[c];
          const val = gridArray[r][c];

          // Compute cell bounding box (0.5 deg around center)
          const p1 = map.latLngToContainerPoint([lat - 0.5, lon - 0.5]);
          const p2 = map.latLngToContainerPoint([lat + 0.5, lon + 0.5]);

          const x = Math.min(p1.x, p2.x);
          const y = Math.min(p1.y, p2.y);
          const w = Math.abs(p1.x - p2.x);
          const h = Math.abs(p1.y - p2.y);

          // Cull offscreen cells
          if (x + w < 0 || x > size.x || y + h < 0 || y > size.y) continue;

          ctx.fillStyle = getColor(val, activeLayer);
          ctx.fillRect(x, y, w + 1, h + 1);
        }
      }
    };

    render();
    map.on('moveend zoomend resize', render);

    return () => {
      map.off('moveend zoomend resize', render);
      if (canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
    };
  }, [gridData, activeLayer, opacity, lats, lons, map]);

  return null;
}

export default function WeatherMap({
  gridData,
  activeLayer,
  gridOpacity,
  showAlerts,
  basemap = 'dark',
  selectedCoord,
  onSelectCoord,
}) {
  // Leaflet style for Alert Zone polygons
  const alertStyle = (feature) => {
    const sev = feature.properties?.severity;
    let strokeColor = '#06b6d4'; // WATCH
    let fillColor = '#06b6d4';

    if (sev === 'CRITICAL') {
      strokeColor = '#ef4444';
      fillColor = '#ef4444';
    } else if (sev === 'WARNING') {
      strokeColor = '#f59e0b';
      fillColor = '#f59e0b';
    }

    return {
      color: strokeColor,
      weight: sev === 'CRITICAL' ? 3 : 2,
      opacity: 0.9,
      fillColor: fillColor,
      fillOpacity: sev === 'CRITICAL' ? 0.35 : 0.2,
      dashArray: sev === 'CRITICAL' ? null : '4, 4',
      className: sev === 'CRITICAL' ? 'alert-polygon-critical' : '',
    };
  };

  const onEachAlertFeature = (feature, layer) => {
    const p = feature.properties;
    layer.bindTooltip(
      `
      <div class="p-1 font-mono text-xs">
        <div class="font-bold text-red-400 flex items-center gap-1">
          <span>⚠️ ${p.severity} ALERT: ${p.alert_id}</span>
        </div>
        <div class="text-slate-200 mt-1">${p.subdivision}</div>
        <div class="text-slate-300">Max Bust Prob: <b>${(p.max_bust_prob * 100).toFixed(1)}%</b></div>
        <div class="text-slate-400 text-[10px]">Area: ${p.area_sq_km.toLocaleString()} km²</div>
        <div class="text-cyan-400 text-[10px] mt-1 italic">Click to inspect synoptic drivers</div>
      </div>
      `,
      { sticky: true, className: 'bg-meteor-900 border border-slate-700 text-slate-100 rounded shadow-xl' }
    );

    layer.on('click', () => {
      onSelectCoord(p.center_lat, p.center_lon);
    });
  };

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={[22.5, 80.5]}
        zoom={5}
        minZoom={4}
        maxZoom={10}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        {/* High-Performance Dark GIS Basemap (100% Free - No API Key Required) */}
        {basemap === 'satellite' ? (
          <TileLayer
            attribution='Tiles &copy; Esri &mdash; World Imagery'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            maxZoom={18}
          />
        ) : (
          <>
            <TileLayer
              attribution='Tiles &copy; Esri &mdash; Dark Gray Canvas'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
              maxZoom={16}
            />
            <TileLayer
              attribution=''
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
              maxZoom={16}
              opacity={0.8}
            />
          </>
        )}

        {/* Dynamic Meteorological Canvas Grid Layer */}
        {gridData && (
          <GridOverlay
            gridData={gridData}
            activeLayer={activeLayer}
            opacity={gridOpacity}
            lats={gridData.lats}
            lons={gridData.lons}
          />
        )}

        {/* Error-Prone Alert Polygons */}
        {showAlerts && gridData?.alert_zones && (
          <GeoJSON
            key={`alerts-${gridData.lead_day}-${gridData.alert_zones.features.length}`}
            data={gridData.alert_zones}
            style={alertStyle}
            onEachFeature={onEachAlertFeature}
          />
        )}

        {/* Selected Inspection Coordinate Crosshair Marker */}
        {selectedCoord && (
          <CircleMarker
            center={[selectedCoord.lat, selectedCoord.lon]}
            radius={8}
            pathOptions={{
              color: '#06b6d4',
              fillColor: '#22d3ee',
              fillOpacity: 0.8,
              weight: 2,
            }}
          />
        )}

        {/* Map Click Listener */}
        <MapClickHandler onMapClick={onSelectCoord} />
      </MapContainer>

      {/* Domain Watermark Tag */}
      <div className="absolute top-4 left-14 z-[400] bg-meteor-900/80 backdrop-blur px-2.5 py-1 rounded-md border border-meteor-700/60 text-[10px] font-mono text-slate-400 pointer-events-none shadow">
        BOUNDS: 5.0°N–38.0°N | 65.0°E–100.0°E
      </div>
    </div>
  );
}
