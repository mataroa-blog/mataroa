# Deployment

How to deploy a new mataroa instance?

1. Get a linux server
1. Follow the [server playbook](./server-playbook.md)
1. Update [mataroa/settings](../mataroa/settings.py)
    * `ADMINS`
    * `CANONICAL_HOST`
    * `EMAIL_HOST` and `EMAIL_HOST_BROADCAST`
1. Adjust the [deploy.sh](../deploy.sh) script
    * Change IP
1. Enable `deploy` user to reload the uwsgi systemd service. To do this...

...add `deploy` user to sudo/wheel group:

```sh
adduser deploy sudo
```

Then, edit sudoers with:

```sh
visudo
```

and add the following:

```
# Allow deploy user to restart apps
%deploy ALL=NOPASSWD: /usr/bin/systemctl reload mataroa.uwsgi
```

Rumours are the only way to see the results is to reboot :/

But once you do (!) — then:

```sh
sudo -i -u deploy
sudo systemctl reload mataroa.uwsgi
```
