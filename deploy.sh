#!/usr/local/bin/bash

set -e

# pull latest changes
ssh roa@95.217.177.163 'cd mataroa && git pull'

# sync requirements
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && pip install -r requirements.txt'

# collect static
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && python manage.py collectstatic --noinput'

# migrate database
env $(cat .env.prod | xargs) ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && python manage.py migrate'

# reload
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && uwsgi --reload mataroa.pid'
