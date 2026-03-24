FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

# Railway/Render inject PORT at runtime
ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT}
