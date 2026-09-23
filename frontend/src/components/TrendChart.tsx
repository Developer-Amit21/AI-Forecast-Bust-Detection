import Plot from "react-plotly.js";
import type { Prediction } from "../types/api";

export function TrendChart({
  predictions,
  region,
}: {
  predictions: Prediction[];
  region: string | undefined;
}) {
  const rows = predictions
    .filter((item) => item.region_id === region)
    .sort((a, b) => a.lead_day - b.lead_day);
  const data: any[] = [
    {
      x: rows.map((x) => x.lead_day),
      y: rows.map((x) => x.bust_probability * 100),
      name: "Bust probability",
      type: "scatter",
      mode: "lines+markers",
      line: { color: "#f97316" },
    },
    {
      x: rows.map((x) => x.lead_day),
      y: rows.map((x) => x.confidence_score),
      name: "Confidence",
      type: "scatter",
      mode: "lines+markers",
      line: { color: "#2563eb" },
    },
  ];

  const layout: any = {
    autosize: true,
    height: 260,
    margin: { l: 40, r: 16, t: 15, b: 35 },
    paper_bgcolor: "white",
    plot_bgcolor: "white",
    xaxis: { title: "Lead day" },
    yaxis: { title: "%", range: [0, 100] },
    legend: { orientation: "h" },
  };

  const config: any = { displayModeBar: false };

  return (
    <section className="chart-card">
      <h2>Lead-time outlook</h2>
      <Plot
        data={data}
        layout={layout}
        config={config}
        style={{ width: "100%" }}
      />
    </section>
  );
}
