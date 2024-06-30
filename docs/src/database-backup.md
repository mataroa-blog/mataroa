# Database Backup

## Shell Script

We use the script [`backup-database.sh`](backup-database.sh) to dump the
database and upload it into an S3-compatible object storage cloud using the
[MinIO client](https://min.io/). This script needs the database password
as an environment variable. The key must be `PGPASSWORD`. The variable can live
in `.envrc` as such:

```sh
export PGPASSWORD=db-password
```

## Commands

To create a database dump run:

```sh
pg_dump -Fc --no-acl mataroa -h localhost -U mataroa -f /home/deploy/mataroa.dump -w
```

To restore a database dump run:

```sh
pg_restore -v -h localhost -cO --if-exists -d mataroa -U mataroa -W mataroa.dump
```

## Initialise and configure backup script

```sh
cp /var/www/mataroa/backup-database.sh /home/deploy/
```

## Download and install MinIO client

```sh
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
mv mc /usr/local/bin/
```

## Setup MinIO client to use S3-compatible storage

1. Create bucket on Scaleway or any other S3-compatible object storage.
1. Find bucket URL.
    * On Scaleway: it's on Bucket Settings.
1. Acquire IAM Access Key ID and Secret Key.
    * On Scaleway: IAM -> Applications -> Project default -> API Keys
1. Add `mc` alias using the command below (run as `deploy` user):

```sh
mc alias set s3scw https://purple.s3.nl-ams.scw.cloud xxx xxx --api S3v4

# verify entry
cat /home/deploy/.mc/config.json
mc ls s3scw
```

## Setup cronjob

Run as `deploy` user:

```sh
crontab -e
```

Append:

```
0 */6 * * * /home/deploy/backup-database.sh
```

This means "run every 6 hours".
