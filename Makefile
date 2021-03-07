.PHONY: format lint

lint:
	flake8
	isort --check-only --profile black .
	black --check .

format:
	black .
	isort --profile black .
