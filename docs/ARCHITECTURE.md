# Architecture

## Overview

```
Web (React/Vite) → API (FastAPI) → Agent Pipeline (packages/)
                                 ↘ PostgreSQL + Redis (jobs/cache)
```

## Data Flow

### Pre-Event: Guest Curation
1. Organizer creates event + defines sponsor ICP
2. API triggers `CurationAgent`
3. Agent → `enrichment` package → LinkedIn, GitHub, Twitter profiles
4. Agent → `scoring` package → ICP score + rationale per profile
5. Ranked shortlist stored in DB and returned to UI

### Pre-Event: Sponsor Brief
1. 48h before event, `AlignmentAgent` fires (cron or manual trigger)
2. Maps confirmed RSVPs to each sponsor's ICP scores
3. `report-gen` generates brief via LLM (Anthropic)
4. PDF exported and delivered to sponsor

### Post-Event: Conversion
1. Organizer uploads Luma/Partiful CSV export
2. `ConversionAgent` re-scores attendees → hot / warm / cold tiers
3. Outreach drafts generated per tier
4. Push to Clay / Airtable / HubSpot via `integrations`

## Key Design Decisions

- **Packages are framework-agnostic** — no FastAPI imports inside `packages/`
- **Agents are orchestrators** — they call enrichment + scoring, never do enrichment themselves
- **All LLM calls live in `report-gen`** — keeps prompt management centralized
- **Integrations are push-only in v1** — write to Clay/Airtable; no bidirectional sync yet
