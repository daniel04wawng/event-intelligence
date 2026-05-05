"""
CurationAgent
-------------
Input:  EventGoal, SponsorICP, seed_profiles (optional)
Output: RankedShortlist

Pipeline:
  1. Fetch candidate profiles from enrichment sources
  2. Score each profile against ICP via scoring package
  3. Run connection-path inference (who in organizer network can intro?)
  4. Return top-N ranked with rationale
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class CurationInput:
    event_id: str
    event_description: str
    sponsor_icp: dict
    target_count: int = 50
    seed_profiles: Optional[list] = None

class CurationAgent:
    def __init__(self, enricher, scorer, llm):
        self.enricher = enricher
        self.scorer = scorer
        self.llm = llm

    async def run(self, input: CurationInput) -> dict:
        # TODO: implement pipeline
        raise NotImplementedError
