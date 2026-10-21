FROM python:3.15-alpine AS base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

WORKDIR /app

FROM base AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.5.1

RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv
ENV VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH"

COPY poetry.lock pyproject.toml ./
RUN poetry sync --only main --no-root --no-interaction

COPY . .
RUN poetry build && /venv/bin/pip install --no-deps dist/*.whl

FROM base AS final

RUN apk add --no-cache libffi
COPY --from=builder /venv /venv
COPY dyn-cloudflare-ddns ./dyn-cloudflare-ddns
COPY docker-entrypoint.sh crontab ./
RUN chmod +x ./docker-entrypoint.sh
RUN crontab crontab

CMD [ "crond", "-f" ]
