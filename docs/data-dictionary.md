# Data dictionary

| Field | Meaning |
|---|---|
| `forecast_initialization_time` | UTC NWP forecast-cycle timestamp |
| `valid_time` | UTC time the forecast is valid |
| `lead_day` | Days from initialization to validity (1–10) |
| `latitude`, `longitude` | WGS84 point coordinates |
| `variable` | `precipitation`, `temperature_2m`, or `wind_speed` |
| `forecast_value`, `observation_value` | Values in the declared units |
| `ensemble_spread` | Ensemble standard deviation, if available |
| `absolute_error` | `abs(forecast_value - observation_value)` |
| `bust_binary` | Label generated with an historical, lead-specific threshold |
| `data_mode` | `synthetic` or `real`; must be retained end-to-end |

Temperature is Celsius, precipitation is mm/day, and wind speed is m/s in synthetic
mode. Real adapters validate declared source units and never silently convert them.
