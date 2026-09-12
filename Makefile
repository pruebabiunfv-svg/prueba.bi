install:
	python -m pip install -r requirements.txt

init-db:
	python scripts/init_db.py

seed-demo:
	python scripts/seed_demo.py

run:
	python main.py

pipeline:
	python jobs/run_pipeline.py

test:
	pytest -q

check:
	python scripts/check_connections.py
