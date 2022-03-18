#!/usr/local/bin/bash

set -e
set -x

# make sure linting checks pass
make lint

# static
python manage.py collectstatic --noinput

# start postgres server
set +e
DID_WE_START_PG=0
PGDATA=postgres-data/ pg_ctl status | grep 'is running'
# if pg is running, grep will succeed, which means exit code 0
if [ ${PIPESTATUS[1]} -eq 1 ]; then
    PGDATA=postgres-data/ pg_ctl start
    DID_WE_START_PG=1
fi
set -e

# make sure latest requirements are installed
pip install -U pip
pip install -r requirements.txt

# make sure tests pass
python manage.py test

# stop postgres server
if [ $DID_WE_START_PG -eq 1 ]; then
    PGDATA=postgres-data/ pg_ctl stop
fi

# push origin srht
git push -v origin master

# push on github
git push -v github master

# pull on server and reload
ssh roa@95.217.177.163 'cd mataroa \
    && git pull \
    && source venv/bin/activate \
    && pip install -U pip \
    && pip install -r requirements.txt \
    && python manage.py collectstatic --noinput \
    && source .envrc && python manage.py migrate \
    && uwsgi --reload mataroa.pid'
