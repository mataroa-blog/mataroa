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
