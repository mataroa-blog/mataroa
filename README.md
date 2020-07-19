# mataroa

Minimal blogging platform with export as first-class feature.

## Contributing

Feel free to open a PR on [GitHub](https://github.com/sirodoht/mataroa/fork) or
send an email patch to [~sirodoht/mataroa-devel@lists.sr.ht](~sirodoht/mataroa-devel@lists.sr.ht).

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

You need to create a new file named `.env` in the root of this project once you cloned it.

`.env` should contain the following env variables:

```sh
SECRET_KEY="thisisthesecretkey"
DATABASE_URL="postgres://username:password@localhost:5432/db_name"
EMAIL_HOST_USER="smtp_user"
EMAIL_HOST_PASSWORD="smtp_password"
```

### Database

This project uses PostgreSQL. See above on how to configure access to it using
the `.env` file.

There is no need to create manually one if you're using Docker and
[Docker Compose](https://docs.docker.com/compose/). Run this to spin up the
database in the background:

```sh
docker-compose up -d db
```

The database data will be saved in a gitignored directory, `db_data`, in the root of
the project.

To create the database schema:

```sh
python manage.py migrate
```

### Subdomains

To develop locally with subdomains, you need to add something like that in your `/etc/hosts`:

```
127.0.0.1 mataroalocal.blog
127.0.0.1 yourlocaluser.mataroalocal.blog
127.0.0.1 random.mataroalocal.blog
127.0.0.1 test.mataroalocal.blog 
```

### Serve

To run the Django development server:

```sh
python manage.py runserver
```

Or, if you prefer to run the web server under Docker:

```sh
docker-compose up web
```

In which case, `DATABASE_URL` in `.env` should be like this:

```sh
DATABASE_URL="postgres://postgres:postgres@db:5432/postgres"
```

You can also run just the database using Docker and the webserver without,
in which case `.env` would be like this:

```sh
DATABASE_URL="postgres://postgres:postgres@127.0.0.1:5432/postgres"
```

and you would start the database like so:

```sh
docker-compose up db
```

## Testing

```sh
python manage.py test
```

## Code linting & formatting

```sh
black . && isort --profile black . && flake8
```

## Deployment

Deployment [is configured](uwsgi.ini) using the production-grade
[uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/) server.

```sh
uwsgi --ini=uwsgi.ini -H venv/
```

You also need to populate your shell environment:

```sh
export SECRET_KEY="thisisthesecretkey"
export DATABASE_URL="postgres://username:password@localhost:5432/db_name"
export EMAIL_HOST_USER="smtp_user"
export EMAIL_HOST_PASSWORD="smtp_password"
```

## Dokku

This project is also configured to deploy to [dokku](http://dokku.viewdocs.io/dokku/).

* [Procfile](Procfile): app init command
* [app.json](app.json): predeploy tasks
* [DOKKU_SCALE](DOKKU_SCALE): process scaling

## License

This software is licensed under the MIT license.
For more information, read the [LICENSE](LICENSE) file.
