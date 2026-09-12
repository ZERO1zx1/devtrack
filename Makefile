PYTHON := .venv/Scripts/python
PIP    := .venv/Scripts/pip

.PHONY: setup run run-port test test-cov lint format check clean

## Environment
setup:                      ## create venv and install all requirements
	python -m venv .venv
	$(PIP) install -r requirements.txt -r requirements-dev.txt

## Run
run:                        ## run dev server (default port)
	$(PYTHON) run.py

run-port:                   ## run dev server on port 5001 (avoids clashes)
	PORT=5001 $(PYTHON) run.py

## Quality
test:                       ## run the full pytest suite
	$(PYTHON) -m pytest

test-cov:                   ## run tests with coverage report
	$(PYTHON) -m pytest --cov=app --cov-report=term-missing

lint:                       ## static analysis
	$(PYTHON) -m ruff check app tests run.py config.py

format:                     ## auto-format python code
	$(PYTHON) -m black app tests run.py config.py

check: test lint             ## test + lint in one step

## Housekeeping
clean:                      ## remove venv, caches and database
	rm -rf .venv .pytest_cache instance __pycache__
	find . -name "__pycache__" -type d -prune -exec rm -rf {} \;