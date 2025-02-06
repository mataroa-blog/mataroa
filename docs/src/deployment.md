# Deployment

## Step 1: Ansible

We use ansible to provision a Debian 12 Linux server.

(1a) First, set up configuration files:

```sh
cd ansible/
# Make a copy of the example file
cp .envrc.example .envrc

# Edit parameters as required
vim .envrc

# Load variables into environment
source .envrc
```

(1b) Then, provision:

```sh
ansible-playbook playbook.yaml -v
```

## Step 2: Wildcard certificates

We use Automatic DNS API integration with DNSimple:

* https://github.com/acmesh-official/acme.sh?tab=readme-ov-file#1-how-to-install
* https://github.com/acmesh-official/acme.sh/wiki/dnsapi#dns_dnsimple

Note: acme.sh's default SSL provider is ZeroSSL which does not accept email with
plus-subaddressing. It will not error gracefully, just fail with a cryptic
message (tested with acmesh v3.0.7).

```sh
curl https://get.acme.sh | sh -s email=person@example.com
# Note: Installation inserts a cronjob for auto-renewal

# Setup DNSimple API
echo 'export DNSimple_OAUTH_TOKEN="token-here"' >> /root/.acme.sh/acme.sh.env

# Issue cert
acme.sh --issue --dns dns_dnsimple -d mataroa.blog -d *.mataroa.blog

# We "install" (copy) the cert because we should not use the cert from acme.sh's internal store
acme.sh --install-cert -d mataroa.blog -d *.mataroa.blog --key-file /etc/caddy/mataroa-blog-key.pem --fullchain-file /etc/caddy/mataroa-blog-cert.pem --reloadcmd "chown caddy:www-data /etc/caddy/mataroa-blog-{cert,key}.pem && systemctl restart caddy"
```

## Step 3: Cronjobs and Automated backups

There are a few cronjobs that need setting up and, of course, backups are essential:

* (3a) [Cronjobs](./cronjobs.md)
* (3b) [Database Backup](./database-backup.md)

## Step 4: Deploy changes

```sh
git push origin main
source .venv/bin/activate
cd ansible/
ansible-playbook -v deploy.yaml
```
