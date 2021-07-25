.PHONY: format lint cov

lint:
	flake8 --exclude=.git/,venv/ --ignore=E203,E501,W503
	isort --check-only --profile black .
	black --check --exclude '/(\.git|venv)/' .

format:
	black --exclude '/(\.git|venv)/' .
	isort --profile black .

cov:
	coverage run --source='.' --omit 'venv/*' manage.py test
	coverage report -m
