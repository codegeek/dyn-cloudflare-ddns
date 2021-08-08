FROM python:3.9.6-alpine3.14

RUN useradd --home-dir /app dyncfdns
WORKDIR /app
RUN chown dyncfdns /app
USER dyncfdns

