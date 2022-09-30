.PHONY: all
all: format lint cov

.PHONY: format
format:
	$(info Formating Python code)
	black --exclude '/(\.direnv|\.pyenv)/' .
	isort --skip-glob .pyenv --profile black .

.PHONY: lint
lint:
	$(info Running Python linters)
	flake8 --exclude=.pyenv/,.direnv/ --ignore=E203,E501,W503
	isort --check-only --skip-glob .pyenv --profile black .
	black --check --exclude '/(\.direnv|\.pyenv)/' .
	shellcheck -x *.sh

.PHONY: test
test:
	$(info Running test suite)
	python -Wall manage.py test

.PHONY: cov
cov:
	$(info Generating coverage report)
	coverage run --source='.' --omit '.pyenv/*' manage.py test
	coverage report -m

.PHONY: pginit
pginit:
	$(info Initialising PostgreSQL database files)
	PGDATA=postgres-data/ pg_ctl init
	PGDATA=postgres-data/ pg_ctl start
	createuser mataroa
	psql -U postgres -c "ALTER USER mataroa CREATEDB;"
	psql -U mataroa -d postgres -c "CREATE DATABASE mataroa;"

.PHONY: pgstart
pgstart:
	$(info Start PostgreSQL)
	PGDATA=postgres-data/ pg_ctl start

.PHONY: pgstop
pgstop:
	$(info Stop PostgreSQL)
	PGDATA=postgres-data/ pg_ctl stop
