# API design

All endpoints are under `/api`. Responses include `data_mode`, forecast cycle,
lead-day, and model version. Key routes: `GET /health`, `GET /forecast/latest`,
`GET /forecast/confidence`, `GET /forecast/bust-probability`, `GET /forecast/error`,
`GET /regions`, `GET /regions/{id}`, `GET /explanations/{id}`, `GET /model/info`,
`GET /verification`, `GET /metrics`, `POST /predict`, `POST /data/ingest`, and
`POST /model/train`. OpenAPI is served at `/docs`.
