.PHONY: install demo train serve test frontend docker-up

install:
	python -m venv .venv && .venv/bin/pip install -r requirements.txt

demo:
	.venv/bin/python scripts/run_inference.py --bootstrap

train:
	.venv/bin/python scripts/train_model.py

serve:
	.venv/bin/uvicorn backend.app.main:app --reload --port 8000

test:
	PYTHONPATH=. .venv/bin/pytest -q

frontend:
	cd frontend && npm install && npm run dev

docker-up:
	docker compose up --build
