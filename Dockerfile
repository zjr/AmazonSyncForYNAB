# The builder image, used to build the virtual environment
FROM python:3.12.4-bookworm AS builder

RUN pip install poetry==2.1.1

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12.4-slim-bookworm AS runtime

RUN apt update && apt install -y chromium chromium-driver

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/.venv 

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY secrets/ secrets/
COPY src/ .

ENTRYPOINT ["python", "./main.py"]
