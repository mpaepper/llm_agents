.PHONY: setup install lint test run clean

# Create conda environment
setup:
	conda env create -f environment.yml
	conda activate llm-agent-server
	make install

# Install dependencies
install:
	poetry install

# Run linting
lint:
	poetry run ruff src tests

# Run tests
test:
	poetry run pytest

# Run the server
run:
	poetry run uvicorn src.fast_api_server.main:app --reload

# Clean up
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info 