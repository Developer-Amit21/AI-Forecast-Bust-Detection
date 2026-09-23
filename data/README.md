# Data layout

`raw/` is for immutable source files, `interim/` for normalized records, and
`processed/` for verified feature tables. `synthetic/` is exclusively for generated
development data. Synthetic and real records must never be joined without an explicit
`data_mode` column and a documented decision.

Large source grids are referenced by metadata; they are not stored in the database.
