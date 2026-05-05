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

## Agentic Ops MVP

Layer 2 of OneLoop. Consumes Event Intelligence outputs and produces the actual
ops needed to run a 100-person curated event in one week: outreach drafts,
guest/venue/sponsor CRMs, RSVP + retention math, and a basic run-of-show.

**What it does**
- Generates workstreams, blockers, next actions, and a one-week timeline.
- Drafts personalized outreach per ranked prospect (channel-aware: email / LinkedIn / Poke).
- Builds guest, venue, and sponsor/partner CRMs.
- Computes RSVP / retention math (over-invite target, per-guest risk, reminder cadence).
- Produces a basic ops checklist and run-of-show.
- Ingests replies from `data/replies.csv` and updates all CRMs in place.

**How to run**
```bash
python -m packages.ops.run_ops
# later, when replies arrive
python -m packages.ops.reply_tracker
```

**Inputs (consumed from Event Intelligence)**
- `data/event_state.json`
- `data/ranked_people.csv`
- `docs/intelligence_summary.md` (optional)

**Outputs**
- `data/outreach_queue.csv`, `data/guest_crm.csv`, `data/venue_crm.csv`,
  `data/sponsor_partner_crm.csv`, `data/retention_tracker.csv`
- `docs/run_of_show.md`, `docs/basic_ops_checklist.md`,
  `docs/one_week_timeline.md`, `docs/retention_plan.md`,
  `docs/ops_summary.md`, `docs/structure_map.md`
- `drafts/venue_outreach_email.md`, `drafts/sponsor_partner_outreach.md`,
  `drafts/luma_event_page.md`, `drafts/poke_messages.csv`, `drafts/emails/*.md`
- updates to `data/event_state.json` (`ops`, `venues`, `sponsors`, `state`, `visibility` only)
- appends to `logs/agent_runs.jsonl` and `docs/agent_activity_log.md`

**Stubbed (no real auth/network)** — see `packages/integrations/*_stub.py`:
Gmail draft creation, Google Sheets sync, Poke/LinkedIn message queue, Luma
event-page creation. Each stub has the same shape its real connector will
have, so swapping them in later is local to one file.

**Branch coordination**
- This branch: `feature/agentic-ops-mvp`. Sister branch:
  `feature/event-intelligence-mvp`.
- Shared contract: `packages/shared/event_state.py`,
  `packages/shared/visibility.py`, `data/event_state.json`,
  `data/ranked_people.csv`, `logs/agent_runs.jsonl`,
  `docs/agent_activity_log.md`, `docs/structure_map.md`.
- Agentic Ops only writes `event_state.{ops,venues,sponsors,state,visibility}`;
  Event Intelligence owns `event_state.{event,intelligence,people}`.

**Visibility / observability**
Every ops agent appends a structured trace (`run_id`, `timestamp`,
`branch_context="agentic_ops"`, `agent_name`, `input_summary`,
`output_summary`, `decisions_made`, `reasoning_summary`, `confidence`,
`files_read`, `files_written`, `blockers`, `next_actions`) to
`logs/agent_runs.jsonl` and a human-readable entry to
`docs/agent_activity_log.md`. No private chain-of-thought is exposed.

See [docs/structure_map.md](docs/structure_map.md) for the full architecture,
file map, data flow, and modification guide.

## Docs

See `/docs` for architecture decisions, data models, and API reference.
