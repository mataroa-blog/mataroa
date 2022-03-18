.PHONY: format lint cov

all: format lint cov

format:
	@echo Formating Python code
	black --exclude '/(\.direnv|\.pyenv)/' .
	isort --skip-glob .pyenv --profile black .

lint:
	@echo Linting Python code
	flake8 --exclude=.pyenv/,.direnv/ --ignore=E203,E501,W503
	isort --check-only --skip-glob .pyenv --profile black .
	black --check --exclude '/(\.direnv|\.pyenv)/' .

cov:
	coverage run --source='.' --omit '.pyenv/*' manage.py test
	coverage report -m
