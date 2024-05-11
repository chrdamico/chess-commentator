FROM python:3.11-slim-bullseye

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     libportaudio2 \
     portaudio19-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install ".[dev]"

COPY voices voices
COPY src src
COPY data data

ENV OPENAI_API_KEY "your-openai-api-key"

RUN python src/manage.py connect-socket