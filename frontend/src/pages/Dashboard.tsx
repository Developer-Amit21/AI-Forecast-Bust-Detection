import { useCallback, useState } from "react";
import { ControlBar } from "../components/ControlBar";
import { InsightPanel } from "../components/InsightPanel";
import { MapPanel } from "../components/MapPanel";
import { TrendChart } from "../components/TrendChart";
import { useDashboard } from "../hooks/useDashboard";
import type { Prediction, Variable } from "../types/api";
export function Dashboard() {
  const [variable, setVariable] = useState<Variable>("precipitation");
  const [leadDay, setLeadDay] = useState(5);
  const { predictions, selected, setSelected, explanation, loading, error } =
    useDashboard(variable, leadDay);
  const choose = useCallback(
    (item: Prediction) => setSelected(item),
    [setSelected],
  );
  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">NCMRWF / MoES · decision support prototype</p>
          <h1>AI Forecast Bust Detection</h1>
        </div>
        <div className="status">
          <span className="badge">SYNTHETIC DATA</span>
          <span>{loading ? "Updating…" : "Latest cycle loaded"}</span>
        </div>
      </header>
      <div className="warning">
        DEVELOPMENT SIMULATION ONLY — NOT FOR OPERATIONAL WEATHER GUIDANCE. All
        forecasts, observations, risk indicators, and map markers shown in this
        application use synthetic data and are intended solely for research,
        development, and demonstration purposes. This system must not be used
        for real-world weather decisions, emergency response, or operational
        forecasting.
      </div>
      <ControlBar
        variable={variable}
        setVariable={setVariable}
        leadDay={leadDay}
        setLeadDay={setLeadDay}
      />
      {error ? (
        <div className="error">
          {error}. Start the backend after running{" "}
          <code>python scripts/run_inference.py --bootstrap</code>.
        </div>
      ) : (
        <div className="grid">
          <MapPanel
            predictions={predictions.filter((row) => row.lead_day === leadDay)}
            selected={selected}
            onSelect={choose}
          />
          <InsightPanel selected={selected} explanation={explanation} />
        </div>
      )}
      <TrendChart predictions={predictions} region={selected?.region_id} />
      <footer>
        Colors indicate calibrated bust probability. Environmental indicators
        identify conditions associated with model risk; they do not diagnose
        events.
      </footer>
    </main>
  );
}
