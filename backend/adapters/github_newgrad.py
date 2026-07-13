"""SimplifyJobs New-Grad-Positions community feed.

Ingests https://github.com/SimplifyJobs/New-Grad-Positions via its machine-
readable listings.json (~11MB, thousands of entries, updated within hours by
the community). Covers companies with unscrapeable career sites (Google, Meta,
Apple, Microsoft, ...) plus hundreds of other US early-career SWE openings.
Each listing carries a sponsorship flag which we surface on the dashboard.

Listings keep their real company name in the `company` column; the poll-health
row for this source logs under the configured feed name.
"""

import re
from datetime import datetime, timezone

import httpx

from .base import Company, normalize

LISTINGS_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"

# Feed categories worth ingesting (skips Hardware, Product, etc.)
CATEGORIES = {
    "software",
    "software engineering",
    "ai/ml/data",
    "data science, ai & machine learning",
    "quant",
}

US_STATE_ABBRS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}
US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
}


def _is_us_location(loc: str) -> bool:
    t = loc.strip().lower()
    if not t:
        return False
    if "usa" in t or "united states" in t:
        return True
    if t in US_STATE_NAMES:
        return True
    # "City, ST" or "City, ST, USA" style
    m = re.search(r",\s*([a-z]{2})\b", t)
    if m and m.group(1) in US_STATE_ABBRS:
        return True
    # bare "Remote" in a US-centric feed -> treat as US unless another country is named
    if t == "remote":
        return True
    return False


def _posted_iso(entry: dict) -> str:
    ts = entry.get("date_posted") or entry.get("date_updated")
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (ValueError, OSError, OverflowError):
        return ""


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    resp = await client.get(LISTINGS_URL, timeout=90, follow_redirects=True)
    resp.raise_for_status()
    entries = resp.json()

    jobs = []
    for e in entries:
        if not (e.get("active") and e.get("is_visible")):
            continue
        if (e.get("category") or "").lower() not in CATEGORIES:
            continue
        locations = e.get("locations") or []
        us_locs = [l for l in locations if _is_us_location(l)]
        if not us_locs:
            continue
        sponsorship = e.get("sponsorship")
        jobs.append(
            normalize(
                job_id=str(e["id"]),
                company=e.get("company_name", "Unknown"),
                title=e.get("title", ""),
                location="; ".join(us_locs[:3]) + (f" (+{len(us_locs) - 3} more)" if len(us_locs) > 3 else ""),
                url=e.get("url", ""),
                posted_at=_posted_iso(e),
                source="github",
                sponsorship=sponsorship if sponsorship and sponsorship != "Other" else None,
            )
        )
    return jobs
