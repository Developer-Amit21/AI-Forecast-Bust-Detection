# Forecast bust definition

A bust is a verification label, not a synonym for any non-zero error. The default
rule labels a row a bust when its absolute error exceeds the **historical 90th
percentile for its variable and lead day**, calculated using earlier cycles only.
The threshold is configurable by absolute value, percentile, climatology-normalized
value, variable, and lead time. Thresholds are estimated on training history only.
