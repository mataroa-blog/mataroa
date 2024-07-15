# Database Backup

## Shell Script

We use the script [`backup-database.sh`](backup-database.sh) to dump the
database and upload it into an S3-compatible object storage cloud using
[rclone](https://rclone.org/). This script needs the database password
as an environment variable. The key must be `PGPASSWORD`. The variable can live
in `.envrc` as such:

```sh
export PGPASSWORD=db-password
```

## Commands

To create a database dump run:

```sh
pg_dump -Fc --no-acl mataroa -h localhost -U mataroa -f /home/deploy/mataroa.dump -W
```

To restore a database dump run:

```sh
pg_restore --disable-triggers -j 4 -v -h localhost -cO --if-exists -d mataroa -U mataroa -W mataroa.dump
```

## Initialise and configure backup script

```sh
cp /var/www/mataroa/backup-database.sh /home/deploy/
```

## Setup rclone

1. Create bucket on Scaleway or any other S3-compatible object storage.
1. Find bucket URL.
    * On Scaleway: it's on Bucket Settings.
1. Acquire IAM Access Key ID and Secret Key.
    * On Scaleway: IAM -> Applications -> Project default -> API Keys

```sh
rclone config
```
