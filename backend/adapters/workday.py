import httpx

from .base import Company, normalize


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    """Workday CXS API. company.extra must include: tenant, site (career site slug), host (wdN)."""
    tenant = company.extra["tenant"]
    site = company.extra["site"]
    host = company.extra.get("host", "wd1")
    url = f"https://{tenant}.{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"

    jobs = []
    offset = 0
    limit = 20
    while True:
        resp = await client.post(
            url,
            json={"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        postings = data.get("jobPostings", [])
        if not postings:
            break
        for p in postings:
            path = p.get("externalPath", "")
            jobs.append(
                normalize(
                    job_id=path or p.get("title", ""),
                    company=company.name,
                    title=p.get("title", ""),
                    location=p.get("locationsText"),
                    url=f"https://{tenant}.{host}.myworkdayjobs.com/{site}{path}",
                    posted_at=p.get("postedOn"),
                )
            )
        offset += limit
        total = data.get("total", 0)
        if offset >= total:
            break
    return jobs
