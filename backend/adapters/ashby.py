import httpx

from .base import Company, normalize


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company.token}"
    resp = await client.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    jobs = []
    for j in data.get("jobs", []):
        jobs.append(
            normalize(
                job_id=j["id"],
                company=company.name,
                title=j["title"],
                location=j.get("location"),
                url=j.get("jobUrl", ""),
                posted_at=j.get("publishedAt"),
            )
        )
    return jobs
