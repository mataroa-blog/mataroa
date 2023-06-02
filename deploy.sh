#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
if [[ "${TRACE-0}" == "1" ]]; then
    set -o xtrace
fi

if [[ "${1-}" =~ ^-*h(elp)?$ ]]; then
    echo 'Usage: ./deploy.sh

This script deploys the service in the production server.'
    exit
fi

cd "$(dirname "$0")"

main() {
    # check venv is enabled
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        exit
    fi

    # make sure linting checks pass
    make lint

    # static
    python manage.py collectstatic --noinput

    # start postgres server
    set +e
    DID_WE_START_PG=0
    PGDATA=postgres-data/ pg_ctl status | grep 'is running'
    # if pg is running, grep will succeed, which means exit code 0
    if [ "${PIPESTATUS[1]}" -eq 1 ]; then
        PGDATA=postgres-data/ pg_ctl start
        DID_WE_START_PG=1
    fi
    set -e

    # make sure latest requirements are installed
    pip install -U pip
    pip install -r requirements.txt

    # make sure tests pass

    # stop postgres server
    if [ $DID_WE_START_PG -eq 1 ]; then
        PGDATA=postgres-data/ pg_ctl stop
    fi
    make test

    # push origin srht
    git push -v origin master

    # push on github
    git push -v github master

    # pull on server and reload
    ssh roa@95.217.177.163 'cd mataroa ' \
        '&& git pull ' \
        '&& source venv/bin/activate ' \
        '&& pip install -U pip ' \
        '&& pip install -r requirements.txt ' \
        '&& python manage.py collectstatic --noinput ' \
        '&& source .envrc && python manage.py migrate ' \
        '&& uwsgi --reload mataroa.pid'
}

main "$@"
