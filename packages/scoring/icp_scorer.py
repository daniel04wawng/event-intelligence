"""
ICPScorer: scores a profile against a sponsor ICP.

Signals used:
- Role / seniority match
- Company stage / type match
- GitHub activity (for dev tool sponsors)
- Past event attendance (cross-event graph)
- Mutual connections to organizer network
"""
from dataclasses import dataclass

@dataclass
class ICPScore:
    profile_id: str
    score: float          # 0.0 - 1.0
    tier: str             # "hot" | "warm" | "cold"
    rationale: str

class ICPScorer:
    def score(self, profile: dict, icp: dict) -> ICPScore:
        # TODO: implement
        raise NotImplementedError
