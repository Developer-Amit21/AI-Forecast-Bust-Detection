import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Prediction } from '../types/api'

const color = (value: number) => value >= .75 ? '#dc2626' : value >= .5 ? '#f97316' : value >= .25 ? '#eab308' : '#16a34a'
export function MapPanel({ predictions, selected, onSelect }: {predictions: Prediction[]; selected: Prediction | null; onSelect: (prediction: Prediction) => void}) {
  const container = useRef<HTMLDivElement>(null); const map = useRef<maplibregl.Map | null>(null)
  useEffect(() => { if (!container.current || map.current) return; map.current = new maplibregl.Map({container: container.current, center: [79, 22], zoom: 3.7, style: {version: 8, sources: {osm: {type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors'}}, layers: [{id: 'osm', type: 'raster', source: 'osm'}]}}); map.current.addControl(new maplibregl.NavigationControl(), 'top-right'); return () => { map.current?.remove(); map.current = null } }, [])
  useEffect(() => { if (!map.current) return; const markers = predictions.map(prediction => { const marker = new maplibregl.Marker({color: color(prediction.bust_probability)}).setLngLat([prediction.longitude, prediction.latitude]).setPopup(new maplibregl.Popup({offset: 18}).setHTML(`<strong>${prediction.region_name}</strong><br/>Bust risk ${(prediction.bust_probability * 100).toFixed(0)}%<br/>Confidence ${prediction.confidence_score.toFixed(0)}%`)).addTo(map.current!); marker.getElement().addEventListener('click', () => onSelect(prediction)); return marker }); return () => markers.forEach(marker => marker.remove()) }, [predictions, onSelect])
  return <section className="map-card"><div ref={container} className="map"/><div className="legend"><b>Bust probability</b><span><i className="dot low"/>Low &lt;25%</span><span><i className="dot moderate"/>Moderate</span><span><i className="dot high"/>High</span><span><i className="dot severe"/>Severe ≥75%</span></div>{selected && <div className="map-selected">Selected: {selected.region_name}</div>}</section>
}
