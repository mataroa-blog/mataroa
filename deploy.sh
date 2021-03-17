#!/usr/local/bin/bash

set -e
set -x

# pull latest changes
ssh roa@mataroa.blog 'cd mataroa && git pull'

# sync requirements
ssh roa@mataroa.blog 'cd mataroa && source venv/bin/activate && pip install -r requirements.txt'

# collect static
ssh roa@mataroa.blog 'cd mataroa && source venv/bin/activate && python manage.py collectstatic --noinput'

# migrate database
ssh roa@mataroa.blog 'cd mataroa && source venv/bin/activate && DATABASE_URL=$DATABASE_URL python manage.py migrate'

# touch uwsgi ini to trigger reload
ssh roa@mataroa.blog 'cd mataroa && source venv/bin/activate && uwsgi --reload mataroa.pid'
