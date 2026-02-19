FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini
COPY README.md /app/README.md

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir .

RUN useradd -m appuser && mkdir -p /var/log/app && chown -R appuser:appuser /var/log/app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
