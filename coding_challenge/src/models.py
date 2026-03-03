from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Foundation:
    number: int
    name: str
    url: str


@dataclass
class Project:
    name: str
    description: str
    country: str
    target_location: str
    budget_total: float
    self_financing: float
    funding_sought: float
    currency: str
    duration_months: int
    start_date: str
    target_group: str
    focus_areas: list[str] = field(default_factory=list)


@dataclass
class ScrapedPage:
    url: str
    text: str
    raw_html: str
    success: bool
    error: Optional[str] = None


@dataclass
class EligibilityResult:
    foundation: Foundation
    eligible: Optional[bool]
    confidence: str  # "high" | "medium" | "low"
    reasoning: str
    key_criteria_matched: list[str] = field(default_factory=list)
    key_criteria_missed: list[str] = field(default_factory=list)
    scraped_urls: list[str] = field(default_factory=list)
    scrape_errors: list[str] = field(default_factory=list)
