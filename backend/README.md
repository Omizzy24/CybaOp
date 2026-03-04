# CybaOp Backend

The intelligence layer for SoundCloud creators. FastAPI + LangGraph analytics pipeline.

## Architecture

```
fetch_profile → fetch_tracks → calculate_metrics → detect_trends → generate_insights → format_report
```

Free tier stops after `fetch_tracks` → `format_report` (basic stats).
Pro tier runs the full pipeline including AI-powered insights.

## Quick Start

```bash
# Setup
cp .env.example .env
# Edit .env with your SoundCloud + Google API keys

# Run with Docker
docker-compose up --build

# Or run locally
pip install -e ".[dev]"
uvicorn src.api.app:app --reload
```

## Tests

```bash
pytest tests/ -v
```

## API Endpoints

- `GET /health` — Health check
- `POST /auth/token` — Exchange SoundCloud OAuth code for JWT
- `GET /analytics/insights` — Run analytics pipeline (requires JWT)
