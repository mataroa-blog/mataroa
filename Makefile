.PHONY: all
all: format lint cov

.PHONY: format
format:
	@echo Formating Python code
	black --exclude '/(\.direnv|\.pyenv)/' .
	isort --skip-glob .pyenv --profile black .

.PHONY: lint
lint:
	@echo Linting Python code
	flake8 --exclude=.pyenv/,.direnv/ --ignore=E203,E501,W503
	isort --check-only --skip-glob .pyenv --profile black .
	black --check --exclude '/(\.direnv|\.pyenv)/' .

.PHONY: cov
cov:
	coverage run --source='.' --omit '.pyenv/*' manage.py test
	coverage report -m

.PHONY: pginit
pginit:
	PGDATA=postgres-data/ pg_ctl init
	PGDATA=postgres-data/ pg_ctl start
	createuser mataroa
	psql -U postgres -c "ALTER USER mataroa CREATEDB;"
	psql -U mataroa -d postgres -c "CREATE DATABASE mataroa;"

.PHONY: pgstart
pgstart:
	PGDATA=postgres-data/ pg_ctl start

.PHONY: pgstop
pgstop:
	PGDATA=postgres-data/ pg_ctl stop
