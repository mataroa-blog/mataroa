# Server Playbook

This is a basic playbook on how to setup a new mataroa instance.

Based and tested on Ubuntu 22.04.

## Set editor

Optional.

```sh
select-editor
update-alternatives --config editor
echo 'export EDITOR=vim;' >> ~/.bashrc
source ~/.bashrc
```

## Set timezone

```sh
timedatectl set-timezone UTC
```

## Update system

```sh
apt update
unattended-upgrade
```

## Install Python and Git

```sh
apt install -y python3 python3-dev python3-venv build-essential git
```

## Install Caddy

From: https://caddyserver.com/docs/install#debian-ubuntu-raspbian

```sh
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install caddy
```

## Setup deploy user

```sh
adduser deploy  # leave password empty three times
adduser deploy caddy
adduser deploy www-data
cd /var/
mkdir www
chown -R deploy:www-data www
```

## Install and setup PostgreSQL

```sh
apt install postgresql
sudo -i -u postgres
createdb mataroa
createuser mataroa
psql
ALTER USER mataroa WITH PASSWORD 'xxx';
exit
exit
```

Note: Change 'xxx' with whatever password you choose.

## Install acme.sh and get certificates

We use Automatic DNS API integration with DNSimple in this case, because
wildcard domain auto-renew is much harder otherwise.

https://github.com/acmesh-official/acme.sh/wiki/dnsapi#dns_dnsimple

```sh
curl https://get.acme.sh | sh -s email=person@example.com
# installation also inserts a cronjob for auto-renewal

# setup DNSimple API
echo 'export DNSimple_OAUTH_TOKEN="token-here"' >> /root/.acme.sh/acme.sh.env

# issue cert
acme.sh --issue --dns dns_dnsimple -d mataroa.blog -d *.mataroa.blog

# we "install" (copy) the cert because we should not use the cert from acme.sh's internal store
acme.sh --install-cert -d mataroa.blog -d *.mataroa.blog --key-file /etc/caddy/mataroa-blog-key.pem --fullchain-file /etc/caddy/mataroa-blog-cert.pem --reloadcmd "chown caddy:www-data /etc/caddy/mataroa-blog-{cert,key}.pem && systemctl restart caddy"
```

Note: acme.sh's default SSL provider is ZeroSSL which does not accept email with
plus-subaddressing. It will not error gracefully, just fail with a cryptic
message (tested with acmesh v3.0.7).

## Clone repository and configure

```sh
sudo -i -u deploy
cd /var/www/
git clone https://git.sr.ht/~sirodoht/mataroa

cd mataroa/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic

# setup uwsgi
cp uwsgi.example.ini uwsgi.ini
vim uwsgi.ini  # edit env variables
exit

# setup caddy
cp Caddyfile /etc/caddy/
sudo vim /etc/caddy/Caddyfile  # edit caddyfile as required
```

Note: We could install uWSGI from Ubuntu's repositories (it's written in C
after all) but uWSGI has multiple extensions and compile options which change
depending on the distribution. For this reason, we install from PyPI, which is
consistent.

## Add systemd entry

```sh
cp /var/www/mataroa/mataroa.uwsgi.service /lib/systemd/system/mataroa.uwsgi.service

# edit and add env variables as required
vim /lib/systemd/system/mataroa.uwsgi.service

ln -s /lib/systemd/system/mataroa.uwsgi.service /etc/systemd/system/multi-user.target.wants/
systemctl daemon-reload
systemctl enable mataroa.uwsgi
systemctl start mataroa.uwsgi
systemctl status mataroa.uwsgi
```

At this point DNS should also be set and just rebooting should result in the
instance showing the landing.

## Setup Cronjobs

One at 10am for email notifications (newsletters):

```
0 10 * * * * bash -c 'cd /var/www/mataroa && source .venv/bin/activate && source .envrc && python manage.py processnotifications'
```

One monthly for mail exports

```
0 0 * * * bash -c 'cd /var/www/mataroa && source .venv/bin/activate && source .envrc && python manage.py mail_exports'
```
