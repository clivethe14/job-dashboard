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


def _epoch_to_iso(ts) -> str:
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return ""


def _find_key(obj, key, depth=0):
    if depth > 8:
        return None
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _find_key(v, key, depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_key(v, key, depth + 1)
            if r is not None:
                return r
    return None


async def apple(client: httpx.AsyncClient, company: Company) -> list[dict]:
    """Apple's job list is server-rendered into window.__staticRouterHydrationData
    (React Router). No public JSON API, but the hydration blob is stable to parse.
    Sorted newest-first, so a handful of pages covers fresh postings."""
    import json
    import re

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
    jobs = []
    max_pages = 15
    for page in range(1, max_pages + 1):
        url = f"https://jobs.apple.com/en-us/search?search=software%20engineer&sort=newest&location=united-states-USA&page={page}"
        resp = await client.get(url, headers=headers, timeout=25, follow_redirects=True)
        resp.raise_for_status()
        html = resp.content.decode("utf-8", errors="replace")
        m = re.search(r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("(.*?)"\);', html, re.S)
        if not m:
            break
        data = json.loads(json.loads('"' + m.group(1) + '"'))
        results = _find_key(data, "searchResults") or []
        if not results:
            break
        for j in results:
            pid = j.get("positionId")
            slug = j.get("transformedPostingTitle", "")
            jobs.append(
                normalize(
                    job_id=str(pid),
                    company=company.name,
                    title=j.get("postingTitle", ""),
                    location="; ".join(l.get("name", "") for l in j.get("locations", [])[:3]),
                    url=f"https://jobs.apple.com/en-us/details/{pid}/{slug}",
                    posted_at=j.get("postDateInGMT") or j.get("postingDate"),
                )
            )
    return jobs


async def google(client: httpx.AsyncClient, company: Company) -> list[dict]:
    """Google Careers server-renders jobs into AF_initDataCallback blocks
    (positional arrays, no clean API). sort_by=date + page=N paginate. Positional
    indices are brittle — this fails loudly (poll_log error) if Google reshapes
    the payload."""
    import json
    import re

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
    jobs = []
    max_pages = 10
    seen_ids = set()
    for page in range(1, max_pages + 1):
        url = (
            "https://www.google.com/about/careers/applications/jobs/results/"
            f"?q=software%20engineer&location=United%20States&sort_by=date&page={page}"
        )
        resp = await client.get(url, headers=headers, timeout=25, follow_redirects=True)
        resp.raise_for_status()
        html = resp.content.decode("utf-8", errors="replace")
        block = None
        for b in re.findall(r"AF_initDataCallback\((\{.*?\})\);", html, re.S):
            if b.count("Software Engineer") > 3:
                block = b
                break
        if not block:
            break
        m = re.search(r"data:(\[.*\]), sideChannel", block, re.S) or re.search(r"data:(\[.*\])\}$", block, re.S)  # noqa: E501
        if not m:
            break
        records = json.loads(m.group(1))[0]
        new_this_page = 0
        for j in records:
            jid = str(j[0])
            if jid in seen_ids:
                continue
            seen_ids.add(jid)
            new_this_page += 1
            try:
                location = j[9][0][0]
            except (IndexError, TypeError):
                location = ""
            try:
                posted = _epoch_to_iso(j[12][0])
            except (IndexError, TypeError):
                posted = ""
            jobs.append(
                normalize(
                    job_id=jid,
                    company=company.name,
                    title=j[1],
                    location=location,
                    url=f"https://www.google.com/about/careers/applications/jobs/results/{jid}",
                    posted_at=posted,
                )
            )
        if new_this_page == 0:
            break
    return jobs


async def microsoft(client: httpx.AsyncClient, company: Company) -> list[dict]:
    """Microsoft careers moved to a PCS/Eightfold-style API on
    apply.careers.microsoft.com. Public JSON, no auth. Paginates by 10."""
    base = "https://apply.careers.microsoft.com/api/pcsx/search"
    params = {"domain": "microsoft.com", "query": "software engineer", "location": "United States"}
    jobs = []
    start = 0
    page_size = 10
    max_pages = 60
    for _ in range(max_pages):
        resp = await client.get(base, params={**params, "start": start}, timeout=25)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        positions = data.get("positions", [])
        if not positions:
            break
        for p in positions:
            jobs.append(
                normalize(
                    job_id=str(p.get("id")),
                    company=company.name,
                    title=p.get("name", ""),
                    location="; ".join(p.get("locations", [])[:3]),
                    url=f"https://jobs.careers.microsoft.com/global/en/job/{p.get('id')}",
                    posted_at=_epoch_to_iso(p.get("postedTs")),
                )
            )
        start += page_size
        if start >= data.get("count", 0):
            break
    return jobs
