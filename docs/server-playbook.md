# Server Playbook

This is a basic playbook on how to setup a new server for hosting a mataroa instance.

This playbook is based on Ubuntu 20.04.

## Timezone

```sh
timedatectl set-timezone UTC
```

## Python and Git

```sh
apt install python3 python3-dev python3-venv build-essential git
```

## Caddy

```sh
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | apt-key add -
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee -a /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install caddy
```

## User

```sh
useradd -m -s /bin/bash roa
passwd roa
```

## PostgreSQL

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

## Let's Encrypt

```sh
apt install snapd
snap install core && snap refresh core
snap install --classic certbot
snap set certbot trust-plugin-with-root=ok
```

### DNSimple plugin for Let's Encrypt

Only useful if DNS is managed by [DNSimple](https://dnsimple.com/).

```sh
snap install certbot-dns-dnsimple
vim /root/.secrets/certbot/dnsimple.ini
chmod 600 /root/.secrets/certbot/dnsimple.ini
```

## Disable root SSH

```sh
vim /etc/ssh/sshd_config
# change line 34 to PermitRootLogin no
# change line 58 to PasswordAuthentication no
systemctl restart ssh
```

## Clone and Start

```sh
sudo -i -u roa
git clone https://github.com/sirodoht/mataroa.git
cd mataroa/
uwsgi uwsgi.ini
caddy start --config /home/roa/mataroa/Caddyfile
```

## Cron

```sh
apt install postfix # for cron log to send local emails
apt install mailutils
```

## minio / mc

```sh
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
mv mc /usr/local/bin/
```
