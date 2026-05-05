# Data Model

## Core Entities

| Entity | Key Fields |
|--------|------------|
| Event | id, name, date, format, target_count, organizer_id |
| Sponsor | id, name, company, icp, event_id |
| Profile | id, name, title, company, linkedin_url, github_username |
| AttendeeScore | profile_id, event_id, sponsor_id, score, tier, rationale |
| Report | id, event_id, sponsor_id, brief_md, generated_at, delivered_at |

## Relationships

```
Event ──< Sponsor
Event ──< AttendeeScore >── Profile
Event ──< Report >── Sponsor
```
