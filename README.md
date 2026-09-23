# AeroBust — AI-based forecast bust detection

AeroBust estimates where a medium-range NWP forecast may be unreliable, when risk grows across Day 1–10, and which forecast/environmental signals are associated with that assessment. It is a decision-support prototype for the MoES/NCMRWF Smart India Hackathon problem.

> **Current default mode is `synthetic`.** The included model, metrics, map markers, and forecast/observation values are generated development data. They must not be interpreted as operational weather forecasts or model skill claims.

## What runs today

- A schema-based provider layer with synthetic, CSV/Parquet, NetCDF and GRIB extension points.
- Physical/time validation, forecast-observation alignment, verification, and precipitation categorical metrics.
- Lead- and variable-specific, historical percentile bust labels fitted only on the temporal training period.
- Leakage-aware history features, probabilistic rapidly-evolving-system indicators, calibrated error/bust models, confidence score, and local/global explanations.
- Temporal holdout evaluation (MAE, RMSE, R², bias, precision, recall, F1, ROC-AUC, PR-AUC, Brier) stratified by variable and lead day.
- FastAPI, SQLAlchemy persistence (SQLite locally / PostgreSQL in Docker), and a React MapLibre + Plotly dashboard.

## Architecture and data flow

```text
Forecast provider + observation provider
  → common schema validation → valid-time/spatial alignment → error verification
  → historical, lead-specific bust threshold/labels → leakage-safe feature table
  → calibrated classifier + error regressor → explanations / confidence / risk clusters
  → database metadata + predictions → FastAPI → map and lead-time dashboard
```

The common forecast fields are initialization and valid time, lead day, latitude, longitude, region, variable, forecast value, optional ensemble information, model ID, and `data_mode`. See [the data dictionary](docs/data-dictionary.md).

## Forecast-bust definition and confidence

The default bust label is an absolute error above the **90th percentile of earlier training-period errors for the same variable and lead day**. It is configurable through `BustDefinition`; absolute and normalized modes are included too. This avoids treating expected Day-10 error as a Day-1 failure.

Confidence is deliberately not merely `1 - P(bust)`. The documented formula combines:

`100 × (0.55 × (1 − calibrated bust probability) + 0.25 × historical reliability + 0.15 × data quality + 0.05 × calibration quality)`.

Each result records model version, forecast cycle, lead day, prediction timestamp, and data mode. SHAP/fallback contributions describe model association, never physical causation or a categorical cyclone/depression diagnosis.

## Quick start

Requires Python 3.10+ and Node 20+.

```bash
cp .env.example .env
make install
make demo
make serve
```

In a second terminal:

```bash
make frontend
```

Open `http://localhost:5173`; API documentation is `http://localhost:8000/docs`.

## Development commands

```bash
.venv/bin/python scripts/generate_synthetic_data.py --cycles 180
.venv/bin/python scripts/preprocess_data.py
.venv/bin/python scripts/calculate_errors.py
.venv/bin/python scripts/generate_labels.py
.venv/bin/python scripts/train_model.py --force
.venv/bin/python scripts/evaluate_model.py
.venv/bin/python scripts/run_inference.py --bootstrap --variable precipitation --lead-day 5
make test
```

For a multi-container deployment, set a strong `POSTGRES_PASSWORD` in `.env`, then:

```bash
docker compose up --build
```

## API

`GET /api/health`, `/forecast/latest`, `/forecast/confidence`, `/forecast/bust-probability`, `/forecast/error`, `/regions`, `/regions/{region_id}`, `/explanations/{region_id}`, `/model/info`, `/verification`, and `/metrics` provide read access. `POST /api/predict` scores a validated same-mode record, `POST /api/data/ingest` stages validated records, and `POST /api/model/train` trains the current synthetic corpus. The interactive contract is at `/docs`.

## Real-data mode

Implement the variable/coordinate/unit mapping in `NetCDFDataProvider` or `GRIBDataProvider`, preserve the common schema, declare the source/data mode, and train a new real-data model on historic matched observations. The current synthetic model refuses `data_mode=real` direct scoring. Files are referenced externally; only metadata and prediction summaries belong in PostgreSQL.

## Dashboard

Choose variable and lead day. Marker colour is calibrated bust probability; click a marker to inspect confidence, expected error, association-based feature explanation, and the Day-1–10 probability/confidence chart. MapLibre consumes prediction coordinates / GeoJSON-ready region records, rather than a hardcoded geographic dataset. A production deployment should add licensed state/district boundary GeoJSON.

## Limitations and future work

- Bust prediction is probabilistic and depends on non-stationary historical behavior.
- Extreme cases are rare; missing or biased observations weaken verification.
- Synthetic metrics convey only pipeline behavior, never real-world accuracy.
- SHAP/feature importance is an association with the model, not causality.
- Outputs support trained meteorologists; they do not replace forecast expertise.

Future work: verified IMD/NCMRWF source adapters, regional geometry ingestion, spatial connected-component clusters, monitoring/drift checks, and operational model approval gates.
