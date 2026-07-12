import httpx

from .base import Company, normalize


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{company.token}?mode=json"
    resp = await client.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    jobs = []
    for j in data:
        categories = j.get("categories", {})
        location = categories.get("location")
        jobs.append(
            normalize(
                job_id=j["id"],
                company=company.name,
                title=j["text"],
                location=location,
                url=j.get("hostedUrl", ""),
                posted_at=str(j.get("createdAt", "")),
            )
        )
    return jobs
