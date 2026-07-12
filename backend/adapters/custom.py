"""Per-company adapters for career sites that aren't on a standard ATS.

Each function takes (client, company) and returns a list of normalized job dicts
via `normalize()`. Register the function name in a company's `extra={"fn": "..."}`
in config.py.
"""

import httpx

from .base import Company, normalize


async def amazon(client: httpx.AsyncClient, company: Company) -> list[dict]:
    url = "https://www.amazon.jobs/en/search.json"
    jobs = []
    offset = 0
    limit = 100
    query = company.extra.get("base_query", "software engineer")
    while True:
        resp = await client.get(
            url,
            params={
                "base_query": query,
                "normalized_country_code[]": "USA",
                "result_limit": limit,
                "offset": offset,
                "sort": "recent",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("jobs", [])
        if not results:
            break
        for j in results:
            jobs.append(
                normalize(
                    job_id=j.get("id_icims", j.get("job_path", "")),
                    company=company.name,
                    title=j.get("title", ""),
                    location=j.get("normalized_location"),
                    url="https://www.amazon.jobs" + j.get("job_path", ""),
                    posted_at=j.get("posted_date"),
                )
            )
        offset += limit
        if offset >= data.get("hits", 0):
            break
    return jobs


def _format_loc(loc: dict) -> str:
    # Uber's "region" is the county (e.g. "King", "Santa Clara"), not the state,
    # so it's dropped to avoid noisy/redundant strings like "Seattle, King, USA".
    if not isinstance(loc, dict):
        return ""
    parts = [loc.get("city"), loc.get("country")]
    return ", ".join(p for p in parts if p)


def _uber_location(j: dict) -> str:
    primary = _format_loc(j.get("location") or {})
    all_locs = j.get("allLocations") or []
    extra = len(all_locs) - 1
    if primary and extra > 0:
        return f"{primary} (+{extra} more)"
    return primary


async def uber(client: httpx.AsyncClient, company: Company) -> list[dict]:
    """Uber's internal careers search API. Brittle/unofficial — grabs a session
    cookie from the careers page first, then calls the search endpoint."""
    await client.get("https://www.uber.com/us/en/careers/list/", timeout=20)
    resp = await client.post(
        "https://www.uber.com/api/loadSearchJobsResults",
        json={"params": {"query": "software engineer", "limit": 100, "page": 0}},
        headers={"x-csrf-token": "x"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    results = (data.get("data") or {}).get("results", [])
    jobs = []
    for j in results:
        jobs.append(
            normalize(
                job_id=str(j.get("id")),
                company=company.name,
                title=j.get("title", ""),
                location=_uber_location(j),
                url=f"https://www.uber.com/us/en/careers/list/{j.get('id')}/",
                posted_at=j.get("creationDate"),
            )
        )
    return jobs
