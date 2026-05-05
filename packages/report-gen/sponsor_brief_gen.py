"""
Generates the pre-event sponsor-attendee alignment brief.
Uses Anthropic API to produce a polished, CFO-presentable report.
"""
import anthropic

class SponsorBriefGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic()

    async def generate(self, event: dict, sponsor: dict, shortlist: list) -> str:
        prompt = self._build_prompt(event, sponsor, shortlist)
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _build_prompt(self, event, sponsor, shortlist) -> str:
        return f"""
You are generating a pre-event sponsor brief for {sponsor['name']}.

Event: {event['name']}
Sponsor Goal: {sponsor['goal']}
Sponsor ICP: {sponsor['icp']}

Top matched attendees:
{shortlist}

Generate a concise, professional brief (3-4 paragraphs) that:
1. Summarizes the attendee quality relative to their ICP
2. Highlights the top 5 attendees they should prioritize meeting
3. Suggests 2-3 specific introductions the organizer should facilitate
4. Ends with a clear ROI headline (e.g., "18 of 42 confirmed attendees match your Series A hiring profile")

Tone: confident, data-grounded, executive-ready.
"""
