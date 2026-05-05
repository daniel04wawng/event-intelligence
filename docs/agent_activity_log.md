# Agent Activity Log

Human-readable trace of all agent runs in the Event Intelligence branch.

## 2026-05-05T06:48:54.519282+00:00 — objective_agent (`objective_agent-356ebdf6`)

- **Input:** Raw event brief (218 chars)
- **Output:** Normalized objective for a 100-person curated tech community event in SF.
- **Reasoning:** Used keyword matching over the brief to infer event size, city, and event type. Goal sentence is the first sentence containing 'goal' or the longest sentence as fallback.
- **Confidence:** medium
- **Decisions:**
  - Inferred event_type='curated tech community event' from brief keywords.
  - Inferred target_size=100.
  - Inferred city='SF'.
- **Next actions:**
  - Run audience_agent to define ICP and avoid personas.

## 2026-05-05T06:48:54.520083+00:00 — audience_agent (`audience_agent-9ba734b4`)

- **Input:** Objective for 'curated tech community event' in SF.
- **Output:** Defined 5 ICP personas and 4 avoid personas; emitted scoring rubric.
- **Reasoning:** Personas are weighted by likely contribution to room quality. Avoid personas reflect the highest-frequency negative signals at curated AI events: generic networkers and sales-only attendees. The rubric is rule-based so scores are auditable.
- **Confidence:** medium
- **Decisions:**
  - Selected AI-builder persona library based on goal/event_type keywords.
  - Set high-fit threshold to 75.
- **Next actions:**
  - Run sourcing_agent to define queries and ingest seed CSV.

## 2026-05-05T06:48:54.520532+00:00 — sourcing_agent (`sourcing_agent-7fd08044`)

- **Input:** Objective + audience ICP. Seed CSV: True (10 rows).
- **Output:** Generated 5 sourcing queries, normalized 10 prospects from seed CSV.
- **Reasoning:** MVP avoids live scraping; instead produces explicit queries and channels so a human (or the Agentic Ops branch) can run sourcing. Normalizing the seed CSV early makes downstream scoring deterministic.
- **Confidence:** medium
- **Decisions:**
  - Built 5 sourcing queries weighted to in-theme builders.
  - Capped per-company attendance at ~3 to preserve room diversity.
- **Files read:** data/people_seed.csv
- **Next actions:**
  - Score prospects with packages/scoring/attendee_fit.py.

## 2026-05-05T06:48:54.520970+00:00 — room_balance_agent (`room_balance_agent-f10e02a3`)

- **Input:** 10 ranked prospects; target_size=100.
- **Output:** Top 6 prospects: gaps in ai_agent_founder, ai_infra_builder; overrepresented: none.
- **Reasoning:** Room balance compares actual persona counts in the top cut to the target mix. A persona is 'gap' if it has <70% of its target slot, and 'overrepresented' at >130%.
- **Confidence:** medium
- **Decisions:**
  - Compared top 6 non-flagged prospects against target mix.
  - Identified 5 persona gap(s).
- **Next actions:**
  - Run sourcing pass focused on top-gap persona.

## 2026-05-05T06:48:54.523740+00:00 — run_intelligence (`run_intelligence-dd5c31bc`)

- **Input:** brief=data/event_brief.txt, seed=data/people_seed.csv
- **Output:** Pipeline complete: 10 prospects scored, 4 high-priority, top_gap=ai_agent_founder.
- **Reasoning:** Sequential pipeline; each stage writes to event_state and emits its own visibility trace.
- **Confidence:** medium
- **Decisions:**
  - Ran objective → audience → sourcing → scoring → room_balance pipeline.
- **Files read:** data/event_brief.txt, data/people_seed.csv
- **Files written:** data/event_state.json, data/ranked_people.csv, docs/intelligence_summary.md, docs/structure_map.md
- **Next actions:**
  - Hand event_state.json + ranked_people.csv to Agentic Ops branch.

## 2026-05-05T06:49:18.012033+00:00 — pm_agent (`pm_agent-9dd2c506`)

- **Input:** target=100, ranked=10, venue_confirmed=False
- **Output:** set 6 workstreams, 4 next actions, 1 blockers
- **Reasoning:** Curated event for ~100 in one week needs parallel guest, venue, sponsor, RSVP, retention, and basic-ops tracks. Blockers prioritized by what gates the next decision.
- **Confidence:** medium
- **Decisions:**
  - Workstreams: guest_outreach, venue_outreach, sponsor_partner_outreach, rsvp_tracking, retention, basic_ops
  - One-week timeline generated
- **Files read:** data/event_state.json, data/ranked_people.csv, docs/intelligence_summary.md
- **Files written:** docs/one_week_timeline.md
- **Blockers:**
  - Venue not confirmed
- **Next actions:**
  - Send first batch of 10 high-priority guest invites
  - Contact 10 venue candidates and request availability + capacity + AV
  - Create event page copy for Luma / manual ticketing
  - Schedule 48h and day-of reminder cadence

## 2026-05-05T06:49:18.013336+00:00 — outreach_agent (`outreach_agent-0d2cb501`)

- **Input:** 8 ranked prospects
- **Output:** 8 drafts (high=3, med=3, low=2)
- **Reasoning:** Generate channel-appropriate drafts with a short personal angle per prospect; do not send. Tone is casual/high-signal, suited to an SF builder community.
- **Confidence:** medium
- **Decisions:**
  - Channel: email if email present, else linkedin if profile present, else poke/manual
  - Priority bucketed from explicit field or fit_score thresholds (>=.75 high, >=.5 medium)
- **Files read:** data/ranked_people.csv
- **Files written:** data/outreach_queue.csv, data/guest_crm.csv
- **Next actions:**
  - Review 3 high-priority drafts and approve for send
  - Connect Gmail/Poke when ready (see packages/integrations stubs)

## 2026-05-05T06:49:18.013897+00:00 — venue_agent (`venue_agent-617f1582`)

- **Input:** 5 venue candidates (sample)
- **Output:** venue_crm.csv (5 rows) + venue_outreach_email.md
- **Reasoning:** We don't do live venue search in MVP; produce a CRM + a parametric outreach email the organizer can fire to known candidates.
- **Confidence:** medium
- **Decisions:**
  - Standard 8-question venue intake (capacity, AV, food, load-in, insurance, floor plan)
  - Default status = to_contact
- **Files written:** data/venue_crm.csv, drafts/venue_outreach_email.md
- **Next actions:**
  - Send venue_outreach_email.md to top 5 candidates
  - Update venue_crm.csv as replies come in

## 2026-05-05T06:49:18.014419+00:00 — sponsor_partner_agent (`sponsor_partner_agent-598cf283`)

- **Input:** 6 ICP categories
- **Output:** sponsor_partner_crm.csv (6 rows) + outreach drafts
- **Reasoning:** Partner economics for a 100-person event aren't worth heavy sponsor packaging. Produce a category list, sample CRM, and a one-paragraph ask.
- **Confidence:** medium
- **Decisions:**
  - Lightweight: no deck, no tiers — single ask is co-host or food/drinks
- **Files written:** data/sponsor_partner_crm.csv, drafts/sponsor_partner_outreach.md
- **Next actions:**
  - Identify warm intros; replace sample list with real targets

## 2026-05-05T06:49:18.015049+00:00 — retention_agent (`retention_agent-de7b890c`)

- **Input:** target=100, guests_tracked=8
- **Output:** need ~133 accepted RSVPs at 75% show-up; 3 high-risk
- **Reasoning:** Retention math drives invite volume. Curated rooms run higher show-up than open events; we still over-invite to absorb declines and no-shows.
- **Confidence:** medium
- **Decisions:**
  - Show-up assumption 75% (curated/private default)
  - Accepted-RSVP target = ceil(target / show_up) = 133
- **Files read:** data/guest_crm.csv
- **Files written:** data/retention_tracker.csv, docs/retention_plan.md
- **Next actions:**
  - Confirm 133 accepted RSVPs by T-3d
  - Personally nudge high-risk high-priority guests at T-24h

## 2026-05-05T06:49:18.015704+00:00 — basic_ops_agent (`basic_ops_agent-c5cfb12e`)

- **Input:** target_size=100
- **Output:** basic_ops_checklist.md + run_of_show.md generated
- **Reasoning:** MVP-grade event production: enough to run a 100-person night without surprises, no full vendor sourcing or production schedule.
- **Confidence:** medium
- **Decisions:**
  - Catering estimate uses 1.0x bites and 2.5x drinks per attendee
  - Staff sized at max(3, target/35) = 3
- **Files written:** docs/basic_ops_checklist.md, docs/run_of_show.md
- **Next actions:**
  - Confirm caterer T-3d
  - Walk venue T-1d

## 2026-05-05T06:49:26.157286+00:00 — reply_tracker (`reply_tracker-3b8d87a3`)

- **Input:** 4 replies
- **Output:** updated guest_crm=4, queue=4, tracker=4
- **Reasoning:** Reply ingestion is the heartbeat of RSVP/retention; this is the MVP file-based version.
- **Confidence:** high
- **Decisions:**
  - Match by lowercased name; last_touch timestamp updated on match
- **Files read:** data/replies.csv
- **Files written:** data/guest_crm.csv, data/outreach_queue.csv, data/retention_tracker.csv
- **Next actions:**
  - Re-run retention_agent to recompute RSVP math

