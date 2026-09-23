# Architecture

```text
Provider (synthetic / CSV / NetCDF / GRIB)
  -> schema + physical validation -> forecast/observation alignment
  -> verification metrics -> configurable bust labels -> leakage-safe features
  -> calibrated regression + classification models -> explanations/confidence/clusters
  -> SQLAlchemy persistence -> FastAPI -> React/MapLibre/Plotly dashboard
```

The production boundary is `BaseWeatherDataProvider`. Its outputs use the common
tabular schema so replacing the synthetic provider does not alter feature or model
code. Current operational outputs are only valid for the `synthetic` mode unless a
verified real-data training run has been completed.

The current baseline uses a temporal holdout: the newest configured fraction of
forecast cycles is never used in fitting. Feature history is shifted by forecast
cycle, so a row cannot use its own or a future observation/error.
