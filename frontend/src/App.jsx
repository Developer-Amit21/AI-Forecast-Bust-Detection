import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import SummaryStats from './components/SummaryStats';
import WeatherMap from './components/WeatherMap';
import LeadTimeSlider from './components/LeadTimeSlider';
import ControlPanel from './components/ControlPanel';
import XaiDiagnosticDrawer from './components/XaiDiagnosticDrawer';
import UploadModal from './components/UploadModal';
import {
  fetchScenarios,
  fetchForecastSummary,
  fetchForecastGrid,
  fetchForecastExplain,
} from './api/client';

export default function App() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('western_disturbance');
  const [leadDay, setLeadDay] = useState(5);
  const [activeLayer, setActiveLayer] = useState('bust_prob');
  const [gridOpacity, setGridOpacity] = useState(0.85);
  const [showAlerts, setShowAlerts] = useState(true);
  const [basemap, setBasemap] = useState('dark');

  const [summary, setSummary] = useState(null);
  const [gridData, setGridData] = useState(null);
  const [selectedCoord, setSelectedCoord] = useState({ lat: 30.0, lon: 74.0 });
  const [explainData, setExplainData] = useState(null);

  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);

  // Initial load: scenarios and summary
  useEffect(() => {
    async function init() {
      try {
        const scList = await fetchScenarios();
        setScenarios(scList);
      } catch (err) {
        console.error('Failed to load scenarios:', err);
      }
    }
    init();
  }, []);

  // Fetch summary on scenario change
  useEffect(() => {
    async function loadSummary() {
      try {
        const sum = await fetchForecastSummary(selectedScenario);
        setSummary(sum);
      } catch (err) {
        console.error('Failed to load summary:', err);
      }
    }
    loadSummary();
  }, [selectedScenario]);

  // Fetch grid data when scenario or leadDay changes
  useEffect(() => {
    let isCancelled = false;
    async function loadGrid() {
      try {
        const g = await fetchForecastGrid(leadDay, selectedScenario);
        if (!isCancelled) setGridData(g);
      } catch (err) {
        if (!isCancelled) console.error('Failed to load grid:', err);
      }
    }
    loadGrid();
    return () => {
      isCancelled = true;
    };
  }, [leadDay, selectedScenario]);

  // Fetch XAI explanation when selected coordinate, leadDay, or scenario changes
  const runExplanation = useCallback(async (lat, lon, day, sc) => {
    setIsExplaining(true);
    try {
      const exp = await fetchForecastExplain(day, lat, lon, sc);
      setExplainData(exp);
      setIsDrawerOpen(true);
    } catch (err) {
      console.error('Failed to explain coordinate:', err);
    } finally {
      setIsExplaining(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCoord) {
      runExplanation(selectedCoord.lat, selectedCoord.lon, leadDay, selectedScenario);
    }
  }, [selectedCoord, leadDay, selectedScenario, runExplanation]);

  const handleMapCoordClick = (lat, lon) => {
    setSelectedCoord({
      lat: Math.round(lat * 10) / 10,
      lon: Math.round(lon * 10) / 10,
    });
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-meteor-950 font-sans">
      {/* Top Navbar */}
      <Navbar
        scenarios={scenarios}
        selectedScenario={selectedScenario}
        onSelectScenario={setSelectedScenario}
        onOpenUpload={() => setIsUploadOpen(true)}
        summary={summary}
      />

      {/* Operational Summary Bar */}
      <SummaryStats summary={summary} leadDay={leadDay} />

      {/* Main Interactive Ops Workspace */}
      <div className="relative flex-1 flex overflow-hidden">
        {/* Full-view GIS Canvas */}
        <div className="relative flex-1 h-full">
          <WeatherMap
            gridData={gridData}
            activeLayer={activeLayer}
            gridOpacity={gridOpacity}
            showAlerts={showAlerts}
            basemap={basemap}
            selectedCoord={selectedCoord}
            onSelectCoord={handleMapCoordClick}
          />

          {/* Floating Top-Right Layer Control Deck */}
          <div className="absolute top-4 right-4 z-[400] max-w-xs">
            <ControlPanel
              activeLayer={activeLayer}
              onSelectLayer={setActiveLayer}
              showAlerts={showAlerts}
              onToggleAlerts={setShowAlerts}
              gridOpacity={gridOpacity}
              onOpacityChange={setGridOpacity}
              basemap={basemap}
              onSelectBasemap={setBasemap}
            />
          </div>

          {/* Floating Bottom Temporal Scrubber */}
          <div className="absolute bottom-6 left-6 right-6 lg:right-auto lg:w-[calc(100%-480px)] z-[400]">
            <LeadTimeSlider
              leadDay={leadDay}
              onLeadDayChange={setLeadDay}
              timeline={summary?.timeline}
              peakRiskDay={summary?.peak_risk_day}
            />
          </div>
        </div>

        {/* Slide-out XAI Diagnostics Drawer */}
        <XaiDiagnosticDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          explainData={explainData}
          summaryTimeline={summary?.timeline}
          leadDay={leadDay}
          isLoading={isExplaining}
        />
      </div>

      {/* Upload NetCDF Modal */}
      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} />
    </div>
  );
}
