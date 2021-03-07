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

### Dependencies

Using [venv](https://docs.python.org/3/library/venv.html):

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

This project also uses [pip-tools](https://github.com/jazzband/pip-tools) for
dependencies management.

### Environment variables

A file named `.env` is used to define the environment variables required for this
project to function. There is an example environment file one can copy as base:

```sh
cp .env.example .env
```

`.env` should contain the following variables:

```sh
SECRET_KEY="thisisthesecretkey"
DATABASE_URL="postgres://mataroa:password@db:5432/mataroa"
EMAIL_HOST_USER="smtp_user"
EMAIL_HOST_PASSWORD="smtp_password"
```

When on production, also include the following variable
(though not using `.env`; see [Deployment](#Deployment)):

```
NODEBUG=1
```

### Database

This project uses PostgreSQL. See above on how to configure access to it using
the `.env` file.

If on Docker, there is a also [Docker Compose](https://docs.docker.com/compose/)
configuration that can be used to spin up a database in the background:

```sh
docker-compose up -d db
```

The database data will be saved in the git-ignored directory `db_data`,
located in the root of the project.

To create the database schema:

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

As `/etc/hosts` does not support wildcard entries, there needs to be one
entry for each mataroa user/blog.

### Serve

To run the Django development server:

```sh
python manage.py runserver
```

Or, if Docker is preferred for running the web server:

```sh
docker-compose up web
```

If opting for the Docker case, `DATABASE_URL` in `.env` should be like this:

```sh
DATABASE_URL="postgres://postgres:postgres@db:5432/postgres"
```

There is also the alternative of running just the database using Docker and
the webserver without. In this case `.env` should be like this:

```sh
DATABASE_URL="postgres://postgres:postgres@127.0.0.1:5432/postgres"
```

And the database would start like so:

```sh
docker-compose up db
```

## Testing

Using the Django test runner:

```sh
python manage.py test
```

For coverage, run:

```sh
coverage run --source='.' --omit 'venv/*' manage.py test
coverage report -m
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

Deployment [is configured](uwsgi.ini) using the production-grade
[uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/) server.

```sh
uwsgi --ini=uwsgi.ini -H venv/
```

The shell environmental need also be populated, as `uwsgi` does not read
the `.env` file:

```sh
export SECRET_KEY="thisisthesecretkey"
export DATABASE_URL="postgres://username:password@localhost:5432/db_name"
export EMAIL_HOST_USER="smtp_user"
export EMAIL_HOST_PASSWORD="smtp_password"
export NODEBUG=1
```

Also, two cronjobs (used by the email newsletter feature) are needed to be
installed. The schedule is subject to the administrator's preference. Indicatively:

```
*/5 * * * * /usr/bin/dokku run mataroa python manage.py enqueue_notifications
*/10 * * * * /usr/bin/dokku run mataroa python manage.py process_notifications
```

Documentation about the commands can be found in section [Management](#Management).

## Dokku

The project is also configured to deploy to a 
[dokku](http://dokku.viewdocs.io/dokku/) server.

* [Procfile](Procfile): app init command
* [app.json](app.json): predeploy tasks
* [DOKKU_SCALE](DOKKU_SCALE): process scaling

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
