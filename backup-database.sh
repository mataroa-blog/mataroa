#!/usr/bin/env bash

cd /home/roa/mataroa || exit 1

source .envrc

pg_dump -Fc --no-acl mataroa -h localhost -U mataroa -f /home/roa/mataroa.dump -w
/usr/local/bin/mc cp /home/roa/mataroa.dump s3scw/tamaroa/backups/postgres-mataroa-"$(date --utc +%Y-%m-%d-%H-%M-%S)"/
