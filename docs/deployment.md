# Deployment

Copy `.env.example` to `.env`, set a non-default PostgreSQL password, then run
`docker compose up --build`. The dashboard is at `http://localhost:5173`; FastAPI
documentation is at `http://localhost:8000/docs`. Keep secrets in deployment
environment variables, not source control.
