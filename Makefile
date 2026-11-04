.PHONY: install db migrate seed api test eval plot

install:
	python -m pip install -e '.[dev]'

db:
	docker compose up -d postgres

migrate:
	alembic upgrade head

seed:
	PYTHONPATH=src python scripts/seed_demo_data.py

api:
	PYTHONPATH=src uvicorn app.main:app --reload

test:
	pytest -q

eval:
	PYTHONPATH=src python scripts/run_retrieval_evaluation.py

plot:
	PYTHONPATH=src python scripts/plot_retrieval_evaluation.py
