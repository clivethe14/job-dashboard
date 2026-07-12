import httpx

from .base import Company, normalize


async def fetch(client: httpx.AsyncClient, company: Company) -> list[dict]:
    """Eightfold AI ATS. company.extra must include: domain (e.g. 'netflix.com')."""
    domain = company.extra["domain"]
    subdomain = company.extra.get("subdomain", domain.split(".")[0])
    url = f"https://{subdomain}.eightfold.ai/api/apply/v2/jobs"
    jobs = []
    start = 0
    num = 50
    while True:
        resp = await client.get(url, params={"domain": domain, "start": start, "num": num}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        positions = data.get("positions", [])
        if not positions:
            break
        for p in positions:
            jobs.append(
                normalize(
                    job_id=str(p.get("id")),
                    company=company.name,
                    title=p.get("name", ""),
                    location=p.get("location"),
                    url=p.get("canonicalPositionUrl", ""),
                    posted_at=str(p.get("t_create", "")),
                )
            )
        start += num
        if start >= data.get("count", 0):
            break
    return jobs
