#!/usr/local/bin/bash

set -e
set -x

# pull latest changes
ssh roa@95.217.177.163 'cd mataroa && git pull'

# sync requirements
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && pip install -r requirements.txt'

# collect static
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && python manage.py collectstatic --noinput'

# migrate database
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && source .envrc && python manage.py migrate'

# reload
ssh roa@95.217.177.163 'cd mataroa && source venv/bin/activate && uwsgi --reload mataroa.pid'
