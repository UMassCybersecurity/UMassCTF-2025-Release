# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

WORKDIR /code
COPY requirements.txt /code
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . .

ENV FLASK_APP cache.py
ENV FLASK_RUN_PORT 8000
ENV FLASK_RUN_HOST 0.0.0.0
ENV PYTHONUNBUFFERED yes

EXPOSE 8000

RUN mkdir cache
CMD ["flask", "run"]