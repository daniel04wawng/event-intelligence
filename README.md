# Event Intelligence Platform

AI-powered guest curation, sponsor alignment, and post-event conversion for tech community events.

## Structure

```
event-intelligence/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # React/Vite frontend
├── packages/
│   ├── agents/       # Orchestration agents (LangGraph / custom)
│   ├── enrichment/   # Profile enrichment (LinkedIn, GitHub, Twitter)
│   ├── scoring/      # ICP scoring & ranking logic
│   ├── report-gen/   # LLM-powered report generation
│   ├── integrations/ # Clay, Airtable, HubSpot, Luma connectors
│   └── shared/       # Types, utils, constants shared across packages
└── infra/
    ├── docker/       # Dockerfiles & compose
    └── scripts/      # DB migrations, seed scripts, deploy helpers
```

## Quickstart

```bash
# Install dependencies
pip install -r apps/api/requirements.txt
cd apps/web && npm install

# Run locally
docker-compose -f infra/docker/docker-compose.dev.yml up
```

## Docs

See `/docs` for architecture decisions, data models, and API reference.
