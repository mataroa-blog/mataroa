# mataroa

Minimal blogging platform with export as first-class feature.

## Contributing

Feel free to open a PR on [GitHub](https://github.com/sirodoht/mataroa/fork) or
send an email patch to [~sirodoht/public-inbox@lists.sr.ht](mailto:~sirodoht/public-inbox@lists.sr.ht).

On how to contribute using email patches see [git-send-email.io](https://git-send-email.io/).

## Development

This is a [Django](https://www.djangoproject.com/) codebase. Check out the
[Django docs](https://docs.djangoproject.com/) for general technical documentation.

### Structure

The Django project is `mataroa`. There is one Django app, `main`,  with all business logic.
Application CLI commands are generally divided into two categories, those under `python manage.py`
and those under `make`.

### Dependencies

Using [venv](https://docs.python.org/3/library/venv.html):

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

This project also uses [pip-tools](https://github.com/jazzband/pip-tools) for dependency
management.

### Environment variables

A file named `.envrc` is used to define the environment variables required for this project to
function. One can either export it directly or use [direnv](https://github.com/direnv/direnv).
There is an example environment file one can copy as base:

```sh
cp .envrc.example .envrc
```

`.envrc` should contain the following variables:

```sh
export SECRET_KEY=some-secret-key
export DATABASE_URL=postgres://mataroa:db-password@db:5432/mataroa
export EMAIL_HOST_USER=smtp-user
export EMAIL_HOST_PASSWORD=smtp-password
```

When on production, also include the following variables (see [Deployment](#Deployment) and
[Backup](#Backup)):

```sh
export NODEBUG=1
export PGPASSWORD=db-password
```

### Database

This project uses PostgreSQL. Assuming one has set the `DATABASE_URL` (see above), to create the
database schema:

```sh
python manage.py migrate
```

Also, initialising the database with some sample development data is possible with:

```sh
python manage.py populate_dev_data
```

### Subdomains

To develop locally with subdomains, one needs something like that in `/etc/hosts`:

```
127.0.0.1 mataroalocal.blog
127.0.0.1 random.mataroalocal.blog
127.0.0.1 test.mataroalocal.blog 
127.0.0.1 mylocalusername.mataroalocal.blog
```

As `/etc/hosts` does not support wildcard entries, there needs to be one entry for each
mataroa user/blog.

### Serve

To run the Django development server:

```sh
python manage.py runserver
```

### Docker

If Docker and docker-compose are preferred, then:

1. Set `DATABASE_URL` in `.envrc` to `postgres://postgres:postgres@db:5432/postgres`
1. Run `docker-compose up -d`.

The database data will be saved in the git-ignored directory / Docker volume `db_data`,
located in the root of the project.

## Testing

Using the Django test runner:

```sh
python manage.py test
```

For coverage, run:

```sh
make coverage
```

## Code linting & formatting

The following tools are used for code linting and formatting:

* [black](https://github.com/psf/black) for code formatting.
* [isort](https://github.com/pycqa/isort) for imports order consistency.
* [flake8](https://gitlab.com/pycqa/flake8) for code linting.

To use:

```sh
make format
make lint
```

## Deployment

Deployment is configured using [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) 
and [Caddy](https://caddyserver.com/).

Remember to set the environment variables before starting `uwsgi`. Depending on the deployment
environment, this could mean directly exporting the variables or just sourcing `.envrc` (with all
production variables — including `NODEBUG`):

```sh
source .envrc
uwsgi uwsgi.ini  # start djago app
caddy start --config /home/roa/mataroa/Caddyfile  # start caddy server
```

Note that the value of the `NODEBUG` variable is ignored. What matters is merely its existence
in the environment.

Also, two cronjobs (used by the email newsletter feature) are needed to be
installed. The schedule is subject to the administrator's preference. Indicatively:

```sh
*/5 * * * * bash -c 'cd /home/roa/mataroa && source ./venv/bin/activate && source .envrc && python manage.py enqueue_notifications'
*/10 * * * * bash -c 'cd /home/roa/mataroa && source ./venv/bin/activate && source .envrc && python manage.py process_notifications'
```

Documentation about the commands can be found in section [Management](#Management).

Finally, certain [setting variables](mataroa/settings.py) may need to be redefined:

* `ADMINS`
* `CANONICAL_HOST`
* `EMAIL_HOST` and `EMAIL_HOST_BROADCAST`

## Backup

To automate backup, there is [a script](backup-database.sh) which dumps the database and uploads
it into AWS S3. The script also needs the database password as an environment variable. The
key needs to be `PGPASSWORD`. The backup script assumes the variable lives in `.envrc` like so:

```sh
export PGPASSWORD=db-password
```

To restore a dump:

```sh
pg_restore -v -h localhost -cO --if-exists -d mataroa -U mataroa -W mataroa.dump
```

To add on cron:

```sh
0 */6 * * * /home/roa/mataroa/backup-database.sh
```

## Management

In addition to the standard Django management commands, there are also:

* `enqueue_notifications`: create records for notification emails to be sent.
* `process_notifications`: sends notification emails for new blog posts of existing records.
* `populate_dev_data`: populate database with sample development data.

They are triggered using the standard `manage.py` Django way:

```sh
python manage.py enqueue_notifications
```

## License

This software is licensed under the MIT license.
For more information, read the [LICENSE](LICENSE) file.
