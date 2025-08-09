FROM python:3.13

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    swig \
    libssl-dev \
    dpkg-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
COPY requirements.dev.txt /code/
RUN pip install -U pip && pip install -Ur /code/requirements.txt && pip install -Ur /code/requirements.dev.txt

WORKDIR /code
COPY . /code/
RUN /code/manage.py collectstatic --noinput
