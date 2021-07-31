#!/usr/local/bin/bash

set -e
set -x

# push origin
git push origin master

# make sure tests pass
source venv/bin/activate
python manage.py test
deactivate

# pull and reload on server
ssh roa@95.217.177.163 'cd mataroa \
    && git pull \
    && source venv/bin/activate \
    && pip install -r requirements.txt \
    && python manage.py collectstatic --noinput \
    && source .envrc \
    && python manage.py migrate \
    && uwsgi --reload mataroa.pid'
