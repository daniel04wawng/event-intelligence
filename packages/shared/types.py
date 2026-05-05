"""Core data types shared across all packages."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Profile:
    id: str
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    twitter_handle: Optional[str] = None
    enriched_at: Optional[datetime] = None
    raw_data: dict = field(default_factory=dict)

@dataclass
class SponsorICP:
    sponsor_id: str
    target_roles: list[str]
    target_company_stages: list[str]   # e.g. ["seed", "series_a", "series_b"]
    target_industries: list[str]
    hiring_signal: bool = False
    pipeline_signal: bool = False
    notes: Optional[str] = None

@dataclass
class Event:
    id: str
    name: str
    description: str
    date: datetime
    format: str    # "hackathon" | "dinner" | "meetup" | "panel"
    target_count: int
    organizer_id: str
    sponsors: list = field(default_factory=list)
