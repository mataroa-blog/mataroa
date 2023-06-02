# mataroa

Naked blogging platform.

## Community

We have a mailing list at
[~sirodoht/mataroa-community@lists.sr.ht](mailto:~sirodoht/mataroa-community@lists.sr.ht)
for the mataroa community to introduce themselves, their blogs, and discuss
anything that’s on their mind!

Archives at
[lists.sr.ht/~sirodoht/mataroa-community](https://lists.sr.ht/~sirodoht/mataroa-community)

### Tools

[Victor Freire](https://freire.dev.br/) has created
[mata](https://git.sr.ht/~glorifiedgluer/mata/), a CLI tool for Mataroa.

## Contributing

Feel free to open a PR on [GitHub](https://github.com/mataroa-blog/mataroa) or
send an email patch to
[~sirodoht/public-inbox@lists.sr.ht](mailto:~sirodoht/public-inbox@lists.sr.ht).

On how to contribute using email patches see
[git-send-email.io](https://git-send-email.io/).

Also checkout our docs on:

* [Coding Conventions](docs/coding-conventions.md)
* [Git Commit Message Guidelines](docs/commit-messages.md)
* [File Structure Walkthrough](docs/file-structure-walkthrough.md)
* [Dependencies](docs/dependencies.md)
* [Server Playbook](docs/server-playbook.md)
* [Admin and Moderation](docs/admin-moderation.md)

## Development

This is a [Django](https://www.djangoproject.com/) codebase. Check out the
[Django docs](https://docs.djangoproject.com/) for general technical
documentation.

### Structure

The Django project is [`mataroa`](mataroa). There is one Django app,
[`main`](main), with all business logic. Application CLI commands are generally
divided into two categories, those under `python manage.py` and those under
`make`.

### Dependencies

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_dev.txt
pip install -r requirements.txt
```

### Environment variables

A file named `.envrc` is used to define the environment variables required for
this project to function. One can either export it directly or use
[direnv](https://github.com/direnv/direnv). There is an example environment
file one can copy as base:

```sh
cp .envrc.example .envrc
```

`.envrc` should contain the following variables:

```sh
export DEBUG=1
export SECRET_KEY=some-secret-key
export DATABASE_URL=postgres://mataroa:db-password@db:5432/mataroa
export EMAIL_HOST_USER=smtp-user
export EMAIL_HOST_PASSWORD=smtp-password
```

When on production, also include/update the following variables (see
[Deployment](#Deployment) and [Backup](#Backup)):

```sh
export DEBUG=0
export PGPASSWORD=db-password
```

### Database

This project is using one PostreSQL database for persistence.

One can use the `make pginit` command to initialise a database in the
`postgres-data/` directory.

After setting the `DATABASE_URL` ([see above](#environment-variables)), create
the database schema with:

```sh
python manage.py migrate
```

Initialising the database with some sample development data is possible with:

```sh
python manage.py loaddata dev-data
```

* `dev-data` is defined in [`main/fixtures/dev-data.json`](main/fixtures/dev-data.json)
* Credentials of the fixtured user are `admin` / `admin`.

### Subdomains

To develop locally with subdomains, one needs something like this in their
`/etc/hosts`:

```
127.0.0.1 mataroalocal.blog
127.0.0.1 random.mataroalocal.blog
127.0.0.1 test.mataroalocal.blog
127.0.0.1 mylocalusername.mataroalocal.blog
```

`/etc/hosts` does not support wildcard entries, thus there needs to be one entry
per mataroa user/blog.

### Serve

To run the Django development server:

```sh
python manage.py runserver
```

### Docker

If Docker and docker-compose are preferred, then:

1. Set `DATABASE_URL` in `.envrc` to `postgres://postgres:postgres@db:5432/postgres`
1. Run `docker-compose up -d`.

The database data will be saved in the git-ignored directory / Docker volume
`docker-postgres-data`, located in the root of the project.

## Testing

Using the Django test runner:

```sh
python manage.py test
```

For coverage, run:

```sh
make cov
```

## Code linting & formatting

The following tools are used for code linting and formatting:

* [black](https://github.com/psf/black) for code formatting
* [isort](https://github.com/pycqa/isort) for imports order consistency
* [flake8](https://gitlab.com/pycqa/flake8) for code linting
* [shellcheck](https://github.com/koalaman/shellcheck) for shell scripts

To use:

```sh
make format
make lint
```

## Deployment

Deployment is configured using [uWSGI](https://uwsgi.readthedocs.io/en/latest/)
and [Caddy](https://caddyserver.com/).

A [server playbook](/docs/server-playbook.md) document is also available, based
on Ubuntu 20.04 LTS.

Environment variables for production are defined both in `uwsgi.ini` (for uWSGI)
and in `.envrc` (for manage.py commands such as migrations and cron management
commands).

```sh
cp uwsgi.example.ini uwsgi.ini  # edit environment variables in uwsgi.ini
uwsgi uwsgi.ini  # start djago app
caddy start --config /home/roa/mataroa/Caddyfile  # start caddy server
```

To reload or stop the uWSGI process:

```sh
uwsgi --reload mataroa.pid
uwsgi --stop mataroa.pid

# or find the PID and kill that directly
ps aux|grep uwsgi
kill -9 <PID>
```

To reload or store the Caddy webserver:

```sh
caddy reload --config /home/roa/mataroa/Caddyfile
caddy stop
```

Also, two cronjobs (used by the email newsletter feature) need to be installed.
The schedule is subject to the administrator’s preference. Indicatively:

```sh
*/5 * * * * bash -c 'cd /home/roa/mataroa && source ./venv/bin/activate && source .envrc && python manage.py enqueue_notifications'
*/10 * * * * bash -c 'cd /home/roa/mataroa && source ./venv/bin/activate && source .envrc && python manage.py process_notifications'
0 0 1 * * bash -c 'cd /home/roa/mataroa && source ./venv/bin/activate && source .envrc && python manage.py mail_exports'
```

Documentation about these commands can be found in section [Management](#Management).

Finally, certain [setting variables](mataroa/settings.py) may need to be redefined:

* `ADMINS`
* `CANONICAL_HOST`
* `EMAIL_HOST` and `EMAIL_HOST_BROADCAST`

## Backup

To automate backup, one can run [`backup-database.sh`](backup-database.sh) which
dumps the database and uploads it into any S3-compatible object storage cloud
using the [MinIO client](https://min.io/). This script needs the database password
as an environment variable. The key must be `PGPASSWORD`. The variable can live
in `.envrc` as such:

```sh
export PGPASSWORD=db-password
```

To restore a database dump:

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
* `mail_exports`: emails users of their blog exports.

They are triggered using the standard `manage.py` Django way; eg:

```sh
python manage.py enqueue_notifications
```

## Billing

One can deploy mataroa without setting up billing functionalities. This is
the default case. To handle payments and subscriptions this project uses
[Stripe](https://stripe.com/). To enable Stripe and payments, one needs to have
a Stripe account with a single
[Product](https://stripe.com/docs/billing/prices-guide) (eg. "Mataroa Premium
Plan").

To configure, add the following variables from your Stripe account to your `.envrc`:

```sh
export STRIPE_API_KEY="sk_test_XXX"
export STRIPE_PUBLIC_KEY="pk_test_XXX"
export STRIPE_PRICE_ID="price_XXX"
```

## License

This software is licensed under the MIT license. For more information, read the
[LICENSE](LICENSE) file.
