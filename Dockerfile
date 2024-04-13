FROM python:3.12.2-alpine as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONBUFFERED=1 \
    PYTHONHASHSEED=random

WORKDIR /app

FROM base as builder

ENV PIC_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    CRYPTOGRAPHY_DONT_BUILD_RUST=1 \
    POETRY_VERSION=1.8.2

RUN apk add --no-cache gcc openssl-dev python3-dev libffi-dev musl-dev
RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv

COPY poetry.lock pyproject.toml ./
RUN poetry export -f requirements.txt | /venv/bin/pip install -r /dev/stdin

COPY . .
RUN poetry build && /venv/bin/pip install dist/*.whl

FROM base as final

RUN apk add --no-cache libffi
COPY --from=builder /venv /venv
COPY dyn-cloudflare-ddns ./dyn-cloudflare-ddns
COPY docker-entrypoint.sh crontab ./
RUN chmod +x ./docker-entrypoint.sh
RUN crontab crontab

CMD [ "crond", "-f" ]