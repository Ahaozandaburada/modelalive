FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY modelalive ./modelalive
COPY registry ./registry
COPY api ./api
COPY scripts/sync_registry.py ./scripts/sync_registry.py

RUN pip install --no-cache-dir -e ".[api]" && python scripts/sync_registry.py

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
