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

## Event Intelligence MVP

The Event Intelligence layer answers *who should be in the room and why?* It
is a small, rule-based pipeline that runs end-to-end with one command and
produces structured artifacts that the Agentic Ops branch consumes.

**What it does**
- Normalizes a raw event brief into a structured objective.
- Defines target ICP and avoid personas, plus an explainable scoring rubric.
- Generates sourcing queries / channels and ingests an optional seed CSV.
- Scores each prospect (0-100) with a transparent reason breakdown.
- Analyzes room balance and surfaces sourcing gaps.

**How to run**
```bash
python -m packages.agents.run_intelligence
# optional: python -m packages.agents.run_intelligence <brief_path> <seed_csv_path>
```

**Inputs**
- `data/event_brief.txt` — raw brief (required)
- `data/people_seed.csv` — seed prospects (optional)

**Outputs**
- `data/event_state.json` — canonical shared state (handoff to Agentic Ops)
- `data/ranked_people.csv` — scored, ranked prospects (handoff to Agentic Ops)
- `docs/intelligence_summary.md` — human-readable rollup
- `docs/agent_activity_log.md` — human-readable agent trace
- `logs/agent_runs.jsonl` — machine-readable agent trace
- `docs/structure_map.md` — full architecture / file map / modification guide

**How Agentic Ops consumes the outputs**
- Read `data/event_state.json` and `data/ranked_people.csv`.
- Filter `priority == "high"` for first-wave outreach.
- Use `why_relevant` and `tags` to personalize.
- Write back into `state.ops.*` and `state.people.{approved,waitlist,rejected}`.
- Treat `state.intelligence.*` and `state.people.ranked_prospects` as read-only.

**Branch coordination**
- This branch (`feature/event-intelligence-mvp`) defines the shared schema in
  `packages/shared/event_state.py` and the visibility layer in
  `packages/shared/visibility.py`. Treat both as the API between branches.
- The sister branch (`feature/agentic-ops-mvp`) consumes the outputs above.

**Visibility / observability**
Every agent run appends a structured trace entry (run_id, timestamp, agent,
input/output summary, decisions, reasoning summary, confidence, files
read/written, blockers, next actions) to both the JSONL log and the
Markdown activity log. No private chain-of-thought is exposed.

See [docs/structure_map.md](docs/structure_map.md) for the full architecture, file map, data flow, and modification guide.

## Docs

See `/docs` for architecture decisions, data models, and API reference.
