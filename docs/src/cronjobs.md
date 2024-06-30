# Cronjobs

Two every 5/10 minutes for notifications:

```
*/5 * * * * bash -c 'cd /var/www/mataroa && source .venv/bin/activate && source .envrc && python manage.py enqueue_notifications'
*/10 * * * * bash -c 'cd /var/www/mataroa && source .venv/bin/activate && source .envrc && python manage.py process_notifications'
```

One monthly for mail exports

```
0 0 * * * bash -c 'cd /var/www/mataroa && source .venv/bin/activate && source .envrc && python manage.py mail_exports'
```
