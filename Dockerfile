FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN pip install uv

# Create the virtual environment directory
RUN python -m venv $VIRTUAL_ENV

WORKDIR /code

COPY pyproject.toml uv.lock /code/

RUN uv sync --all-groups --project .

RUN rm -rf /code/pyproject.toml /code/uv.lock

# mount local code over /code, but /opt/venv remains untouched
COPY . /code/

# Expose port 8000 for the Django development server
EXPOSE 8000

# Command to run the Django development server (can be overridden by docker-compose.yml)
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
