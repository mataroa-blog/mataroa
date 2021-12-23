#!/usr/local/bin/bash

set -e
set -x

# load ssh
eval $(ssh-agent) && ssh-add ~/.ssh/id_ed25519

# push origin srht
git push -v origin master

# push on github
git push -v github master

# make sure tests pass
python manage.py test

# pull on server and reload
ssh roa@95.217.177.163 'cd mataroa \
    && git pull \
    && source venv/bin/activate \
    && pip install -r requirements.txt \
    && python manage.py collectstatic --noinput \
    && source .envrc && python manage.py migrate \
    && uwsgi --reload mataroa.pid'
