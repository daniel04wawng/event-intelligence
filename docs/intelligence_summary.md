# Event Intelligence Summary

_Generated 2026-05-05T06:48:54.522458+00:00_

## 1. Event Objective
- **Goal:** goal is to build brand and community around agent infrastructure.
- **Format:** curated tech community event
- **City:** SF
- **Target size:** 100
- **Success metrics:**
  - 100 RSVPs
  - 60-70 actual attendees
  - 30+ high-fit attendees aligned with the theme
  - 10 meaningful post-event follow-ups

## 2. Target Audience (ICP)
- **ai_agent_founder** (weight 10): Founders building AI agent products or agent infrastructure.
- **ai_infra_builder** (weight 9): Engineers building AI infra, devtools, or agent frameworks.
- **technical_operator** (weight 7): Technical PMs, applied AI leads, or hands-on operators shipping AI products.
- **community_connector** (weight 6): High-signal community organizers, prolific writers, or hub people.
- **investor_high_signal** (weight 4): Investors only if they materially improve room quality (partners at top funds, ex-operators).

## 3. Avoid Personas
- **generic_networker** (penalty 15): Attending purely to network with no clear connection to the theme.
- **sales_only** (penalty 12): Sales-only attendees with no technical or product context.
- **low_context** (penalty 10): Attendees with no clear connection to AI/agent infra theme.
- **free_food_only** (penalty 8): Showing up for the perks rather than the conversation.

## 4. Sourcing Strategy
### queries
- AI agent founders building production agent systems based in SF
- AI infra / devtools engineers shipping agent frameworks based in SF
- Applied AI leads at Series A-C startups based in SF
- Active GitHub contributors to popular agent / LLM tooling repos based in SF
- High-signal community organizers in AI infra space

### sources
- Luma attendee lists from similar events (priority: high)
- Founder/builder Twitter (X) lists (priority: high)
- GitHub contributors to relevant agent/infra repos (priority: high)
- Personal/team networks (warm intros) (priority: high)
- AI infra Slack/Discord communities (priority: medium)
- YC and top-fund portfolio lists (relevant tracks only) (priority: medium)

### prioritization_rules
- Warm intros and known builders go to top of queue.
- Founders/engineers actively building in-theme rank higher than investors.
- If two prospects tie on fit, prefer the one with stronger contribution signal (writing, OSS, talks).
- Cap any single company to ~3 attendees to keep room diverse.
- Reject anyone matching avoid personas regardless of company prestige.

## 5. Scoring Rubric
- **Max score:** 100
- **High threshold:** 75
- **Medium threshold:** 55
- **Notes:** Rule-based and explainable. See packages/scoring/attendee_fit.py.

## 6. Top 10 Ranked Prospects
| # | Name | Company | Role | Persona | Fit | Priority |
|---|------|---------|------|---------|-----|----------|
| 1 | Alex Chen | Loop AI | Founder & CEO | ai_agent_founder | 100 | high |
| 2 | Priya Rao | VectorForge | Staff AI Infra Engineer | ai_infra_builder | 88 | high |
| 3 | Chris Okafor | Forge Capital | Partner | ai_infra_builder | 82 | high |
| 4 | Lina Park | Helios | Head of Platform | ai_infra_builder | 80 | high |
| 5 | Jamie Liu | SignalLabs | Applied AI Lead | technical_operator | 74 | medium |
| 6 | Devon Park | Independent | AI Researcher and Writer | community_connector | 66 | medium |
| 7 | Tomas Reyes | SoloDev | Builder |  | 10 | needs_review |
| 8 | Marcus Webb | DataPipe | Account Executive |  | 0 | needs_review |
| 9 | Riya Shah | GrowthCo | SDR |  | 0 | needs_review |
| 10 | Hana Sato | QuickBiz | Business Development |  | 0 | needs_review |

## 7. Room Balance
- **Summary:** Top 6 prospects: gaps in ai_agent_founder, ai_infra_builder; overrepresented: none.
- **Persona breakdown:** {'ai_agent_founder': 1, 'ai_infra_builder': 3, 'technical_operator': 1, 'community_connector': 1}
- **Gaps:**
  - ai_agent_founder: current 1 / target 30 (deficit 29)
  - ai_infra_builder: current 3 / target 25 (deficit 22)
  - technical_operator: current 1 / target 20 (deficit 19)
  - community_connector: current 1 / target 15 (deficit 14)
  - investor_high_signal: current 0 / target 10 (deficit 10)
- **Recommendations:**
  - Source from YC W24/S24 AI agent batch and recent agent-startup launch posts.
  - Source from GitHub contributors to popular agent/LLM tooling repos and AI infra Slacks.
  - Source from applied-AI / ML lead roles at Series A-C startups via warm intros.

## 8. Open Questions
- Is the event public or invite-only?
- Is there a sponsor or partner goal?
- Is the venue already secured?
- What is the exact date and time?
- Who is the primary host / face of the event?

## 9. Next Recommended Ops Actions
- Approve the top high-priority prospects in `data/ranked_people.csv`.
- Hand `data/event_state.json` and `data/ranked_people.csv` to the Agentic Ops branch.
- Run another sourcing pass focused on the top room-balance gap.

