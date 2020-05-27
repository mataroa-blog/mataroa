FROM python:3.8.2
ENV PYTHONUNBUFFERED 1
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    swig \
    libssl-dev \
    dpkg-dev \
    netcat \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install -U pip && pip install -Ur /code/requirements.txt

WORKDIR /code
COPY . /code/
RUN /code/manage.py collectstatic --noinput
