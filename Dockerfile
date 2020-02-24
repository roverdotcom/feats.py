FROM python:3.6-alpine

COPY requirements.txt /
COPY requirements-dev.txt /
RUN pip install -r /requirements.txt
RUN pip install -r /requirements-dev.txt

COPY . /app
WORKDIR /app
