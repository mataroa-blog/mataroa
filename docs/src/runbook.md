# Runbook

So, mataroa is down. What do we do?

Firstly, panic. Run around in circles with your hands up in despair. It's important to
do this, don't think this is a joke! Ok, once that's done:

## 1. Check Caddy

Caddy is the first point of contact inside the server from the outside world.

First ssh into server:

```sh
ssh root@mataroa.blog
```

Caddy runs as a systemd service. Check status with:

```sh
systemctl status caddy
```

Exit with `q`. If the service is not running and is errored restart with:

```sh
systemctl restart caddy
```

If restart does not work, check logs:

```sh
journalctl -u caddy -r
```

`-r` is for reverse. Use `-f` to follow logs real time:

```sh
journalctl -u caddy -f
```

To search within all logs do slash and then the keyword itself, eg: `/keyword-here`,
then hit enter.

The config for Caddy is:

```sh
cat /etc/caddy/Caddyfile
```

One entry is to serve anything with *.mataroa.blog host, and the second is for anything
not in that domain, which is exclusively all the blogs custom domains.

The systemd config for Caddy is:

```sh
cat /etc/systemd/system/multi-user.target.wants/caddy.service
```

## 2. Check gunicorn

After caddy receives the request, it forwards it to gunicorn. Gunicorn is what runs the
mataroa Django instances, so it's named `mataroa`. It also runs as a systemd service.

To see status:

```sh
systemctl status mataroa
```

To restart:

```sh
systemctl restart mataroa
```

To see logs:

```sh
journalctl -u mataroa -r
```

and to follow them:

```sh
journalctl -u mataroa -f
```

The systemd config for mataroa/gunicorn is:

```sh
cat /etc/systemd/system/multi-user.target.wants/mataroa.service
```

Note that the env variables for production live inside the systemd service file.

## 3. How to hotfix code

Here's where the code lives and how to access it:

```sh
sudo -i -u deploy
cd /var/www/mataroa/
source .envrc  # load env variables for manual runs
source .venv/bin/activate  # activate venv
python manage.py
```

If you make a change in the source code files (inside `/var/www/mataroa`) you need to
restart the service for the changes to take effect:

```sh
systemctl restart mataroa
```
