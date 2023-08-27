#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail
if [[ "${TRACE-0}" == "1" ]]; then
    set -o xtrace
fi

if [[ "${1-}" =~ ^-*h(elp)?$ ]]; then
    echo 'Usage: ./backup-database.sh

This script dumps the mataroa postgres database and uploads it into an S3-compatible server.'
    exit
fi

cd "$(dirname "$0")"

main() {
    # shellcheck disable=SC1091
    # source for PGPASSWORD variable
    source /var/www/mataroa/.envrc

    # dump database in the home folder
    pg_dump -Fc --no-acl mataroa -h localhost -U mataroa -f /home/deploy/mataroa.dump -w

    # upload using minio client
    /usr/local/bin/mc cp /home/deploy/mataroa.dump s3scw/mataroa/backups/postgres-mataroa-"$(date --utc +%Y-%m-%d-%H-%M-%S)"/
}

main "$@"
