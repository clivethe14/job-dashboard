import httpx

from .base import Company, normalize


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company.token}/jobs?content=false"
    resp = await client.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    jobs = []
    for j in data.get("jobs", []):
        location = (j.get("location") or {}).get("name")
        jobs.append(
            normalize(
                job_id=str(j["id"]),
                company=company.name,
                title=j["title"],
                location=location,
                url=j.get("absolute_url", ""),
                posted_at=j.get("updated_at"),
            )
        )
    return jobs
