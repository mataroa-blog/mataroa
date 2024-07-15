# Server Migration

Sadly or not, nothing lasts forever. One day you might do a server migration.
Among many, mataroa is doing something naughty. We store everything, images
including, in the Postgres database. Naughty indeed, yet makes it much easier to
backup but also migrate.

To start with, one a migrator has setup their new server (see
[Deployment](./deployment.md)) we recommend testing everything in another
domain, other than the main (existing) one.

Once everything works:

1. Verify all production variables and canonical server names exist in settings et al.
1. Disconnect production server from public IP. This is not a zero-downtime migration — to be clear.
1. Run backup-database.sh one last time.
1. Assign elastic/floating IP to new server.
1. Run TLS certificate (naked and wildcard) generations.
1. `scp` database dump into new server.
1. Restore database dump in new server.
1. Start mataroa and caddy systemd services

Later:

1. Setup cronjobs / systemd timers
1. Setup healthcheks for recurring jobs.
1. Verify DEBUG is 0.

The above assume the migrator has a floating IP that they can move around. If
not, there are two problems. The migrator needs to coordinate DNS but much
more problematically all custom domains stop working :/ For this reason we
should implement CNAME custom domains. However, CNAME custom domains do not
support root domains, so what's the point anyway you ask. Good question. I don't
know. I only hope I never decide to switch away from Hetzner.

Peace.
