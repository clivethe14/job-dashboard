import httpx

from .base import Company, normalize


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    url = f"https://api.smartrecruiters.com/v1/companies/{company.token}/postings"
    jobs = []
    offset = 0
    limit = 100
    while True:
        resp = await client.get(url, params={"limit": limit, "offset": offset}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content", [])
        if not content:
            break
        for j in content:
            location = j.get("location", {})
            loc_str = ", ".join(filter(None, [location.get("city"), location.get("region"), location.get("country")]))
            jobs.append(
                normalize(
                    job_id=j["id"],
                    company=company.name,
                    title=j["name"],
                    location=loc_str,
                    url=j.get("applyUrl") or j.get("ref", ""),
                    posted_at=j.get("releasedDate"),
                )
            )
        offset += limit
        if offset >= data.get("totalFound", 0):
            break
    return jobs
