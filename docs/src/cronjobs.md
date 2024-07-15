# Cronjobs

We don't use cron but systemd timers for jobs that need to run recurringly.

## Process email notifications

```sh
python manage.py processnotifications
```

Sends notification emails for new blog posts.

Triggers daily at 10AM server time.

## Email blog exports

```sh
python manage.py mailexports
```

Emails users their blog exports.

Triggers monthly, first day of the month, 6AM server time.

## Database backup

```
./backup-database.sh
```

Triggers every 6 hours.
