.PHONY: format lint cov

lint:
	flake8
	isort --check-only --profile black .
	black --check .

format:
	black .
	isort --profile black .

cov:
	coverage run --source='.' --omit 'venv/*' manage.py test
	coverage report -m
