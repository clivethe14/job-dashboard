from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# WHICH JOBS TO KEEP
#
# A posting is kept only if its TITLE contains at least one INCLUDE_KEYWORDS
# phrase AND none of the EXCLUDE_KEYWORDS words. Matching is case-insensitive.
#
# To tune your feed, just edit the two lists below and restart the server.
#   - INCLUDE_KEYWORDS: substring match (use specific phrases, keep lowercase).
#   - EXCLUDE_KEYWORDS: whole-word match (so "intern" won't hit "international").
# ---------------------------------------------------------------------------

INCLUDE_KEYWORDS = [
    # --- Core software engineering ---
    "software engineer",
    "software developer",
    "software development engineer",
    "swe",
    "backend engineer",
    "back-end engineer",
    "frontend engineer",
    "front-end engineer",
    "full stack",
    "fullstack",
    "full-stack",
    "web developer",
    "application developer",
    "application engineer",

    # --- AI / ML / GenAI ---
    "machine learning engineer",
    "ml engineer",
    "machine learning",
    "ai engineer",
    "artificial intelligence engineer",
    "applied ai",
    "applied scientist",
    "research engineer",
    "generative ai",
    "genai",
    "llm engineer",
    "nlp engineer",
    "computer vision engineer",
    "deep learning",
    "mlops",
    "ml ops",
    "prompt engineer",
    "ai/ml",

    # --- Mobile ---
    "mobile engineer",
    "mobile developer",
    "android engineer",
    "android developer",
    "ios engineer",
    "ios developer",
    "flutter",
    "react native",

    # --- Data ---
    "data engineer",
    "data scientist",
    "data science",
    "analytics engineer",

    # --- DevOps / Cloud / SRE ---
    "devops",
    "site reliability",
    "reliability engineer",
    "platform engineer",
    "infrastructure engineer",
    "cloud engineer",
]

EXCLUDE_KEYWORDS = [
    # --- Seniority: drop anything above entry/mid level ---
    "senior",
    "sr",
    "staff",
    "principal",
    "lead",
    "manager",
    "director",
    "vp",
    "vice president",
    "head of",
    "distinguished",
    "fellow",

    # --- Internships / co-ops: full-time roles only ---
    "intern",
    "internship",
    "co-op",
    "coop",

    # --- Non-engineering roles that mention engineering keywords ---
    "recruiter",
    "recruiting",
]


@dataclass
class Company:
    name: str
    ats: str  # "greenhouse" | "lever" | "workday" | "custom"
    token: str = ""
    extra: dict = field(default_factory=dict)
    keywords: list[str] = field(default_factory=lambda: list(INCLUDE_KEYWORDS))


def matches_keywords(title: str, keywords: list[str] | None = None, exclude: list[str] | None = None) -> bool:
    t = title.lower()
    includes = keywords if keywords is not None else INCLUDE_KEYWORDS
    excludes = exclude if exclude is not None else EXCLUDE_KEYWORDS

    if not any(k in t for k in includes):
        return False
    # whole-word match for excludes so short words don't hit inside other words
    for e in excludes:
        if re.search(r"\b" + re.escape(e) + r"\b", t):
            return False
    return True


def normalize(
    job_id: str,
    company: str,
    title: str,
    location: str | None,
    url: str,
    posted_at: str | None = None,
    source: str = "ats",
    sponsorship: str | None = None,
) -> dict:
    return {
        "id": f"{company}:{job_id}",
        "company": company,
        "title": title,
        "location": location or "",
        "url": url,
        "posted_at": posted_at or "",
        "source": source,
        "sponsorship": sponsorship,
    }
