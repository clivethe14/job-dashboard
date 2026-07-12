import httpx

from .base import Company, normalize


def _resolve_location(job: dict) -> str:
    """Greenhouse's location.name is usually a city string, but some companies
    (notably Stripe) put "N/A" there for country-level roles and stash the real
    place in the `offices` array. Fall back to office names when name is missing.
    The `offices` array is only present when the board is fetched with
    content=true (see Company.extra["content"])."""
    name = (job.get("location") or {}).get("name") or ""
    if name.strip() and name.strip().upper() != "N/A":
        return name
    office_names = [o.get("name") for o in (job.get("offices") or []) if o.get("name")]
    if office_names:
        return " / ".join(office_names)
    return name


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    # content=true is heavier (full HTML descriptions) but is the only way to get
    # the `offices` array; enable it per-company via extra={"content": True}.
    content = "true" if company.extra.get("content") else "false"
    url = f"https://boards-api.greenhouse.io/v1/boards/{company.token}/jobs?content={content}"
    resp = await client.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    jobs = []
    for j in data.get("jobs", []):
        jobs.append(
            normalize(
                job_id=str(j["id"]),
                company=company.name,
                title=j["title"],
                location=_resolve_location(j),
                url=j.get("absolute_url", ""),
                posted_at=j.get("updated_at"),
            )
        )
    return jobs
