#!/usr/bin/env bash

cd /home/roa/mataroa
source .envrc
pg_dump -Fc --no-acl mataroa -h localhost -U mataroa -f /home/roa/mataroa.dump -w
/usr/local/bin/aws s3 cp /home/roa/mataroa.dump s3://mataroa/backups/postgres-mataroa-$(date --utc +%Y-%m-%d-%H-%M-%S)/
