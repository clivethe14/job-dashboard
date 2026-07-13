from .adapters.base import Company

POLL_INTERVAL_MINUTES = 60

# Every entry below was live-tested against its real API and confirmed to return
# job data. Companies with no clean public JSON API (Google, Meta, Microsoft,
# Apple, and several others) are intentionally excluded — see README for details
# and options if you want to add them later via browser-based scraping.
COMPANIES = [
    # --- Greenhouse ---
    # content=True pulls the heavier payload so we can recover location from the
    # `offices` array (Stripe uses "N/A" in location.name for country-level roles).
    Company(name="Stripe", ats="greenhouse", token="stripe", extra={"content": True}),
    Company(name="Airbnb", ats="greenhouse", token="airbnb"),
    Company(name="Robinhood", ats="greenhouse", token="robinhood"),
    Company(name="Reddit", ats="greenhouse", token="reddit"),
    Company(name="Figma", ats="greenhouse", token="figma"),
    Company(name="Coinbase", ats="greenhouse", token="coinbase"),
    Company(name="Pinterest", ats="greenhouse", token="pinterest"),
    Company(name="DoorDash", ats="greenhouse", token="doordashusa"),
    Company(name="Databricks", ats="greenhouse", token="databricks"),
    Company(name="Roblox", ats="greenhouse", token="roblox"),
    Company(name="Twilio", ats="greenhouse", token="twilio"),
    Company(name="Cloudflare", ats="greenhouse", token="cloudflare"),
    Company(name="Asana", ats="greenhouse", token="asana"),
    Company(name="MongoDB", ats="greenhouse", token="mongodb"),
    Company(name="Elastic", ats="greenhouse", token="elastic"),
    Company(name="Datadog", ats="greenhouse", token="datadog"),
    Company(name="Lyft", ats="greenhouse", token="lyft"),

    Company(name="Jane Street", ats="greenhouse", token="janestreet"),

    # --- Lever ---
    Company(name="Palantir", ats="lever", token="palantir"),
    Company(name="Spotify", ats="lever", token="spotify"),

    # --- Ashby ---
    Company(name="Notion", ats="ashby", token="notion"),
    Company(name="Snowflake", ats="ashby", token="snowflake"),

    # --- SmartRecruiters ---
    Company(name="Block", ats="smartrecruiters", token="BlockRecruit"),
    Company(name="ServiceNow", ats="smartrecruiters", token="servicenow"),

    # --- Eightfold ---
    Company(name="Netflix", ats="eightfold", extra={"domain": "netflix.com", "subdomain": "netflix"}),

    # --- Workday (POST-based CXS API) ---
    Company(name="Zoom", ats="workday", extra={"tenant": "zoom", "site": "Zoom", "host": "wd5"}),
    Company(name="Nvidia", ats="workday", extra={"tenant": "nvidia", "site": "NVIDIAExternalCareerSite", "host": "wd5"}),
    Company(name="Salesforce", ats="workday", extra={"tenant": "salesforce", "site": "External_Career_Site", "host": "wd12"}),
    Company(name="Adobe", ats="workday", extra={"tenant": "adobe", "site": "external_experienced", "host": "wd5"}),
    Company(name="Cisco", ats="workday", extra={"tenant": "cisco", "site": "Cisco_Careers", "host": "wd5"}),
    Company(name="Capital One", ats="workday", extra={"tenant": "capitalone", "site": "Capital_One", "host": "wd12"}),
    Company(name="VMware (Broadcom)", ats="workday", extra={"tenant": "broadcom", "site": "External_Career", "host": "wd1"}),
    Company(name="Workday", ats="workday", extra={"tenant": "workday", "site": "Workday", "host": "wd5"}),

    # --- Custom (unofficial but confirmed-working endpoints) ---
    Company(name="Amazon", ats="custom", extra={"fn": "amazon", "base_query": "software engineer"}),
    Company(name="Uber", ats="custom", extra={"fn": "uber"}),  # unofficial endpoint, may break without notice
    Company(name="Microsoft", ats="custom", extra={"fn": "microsoft"}),
    Company(name="Apple", ats="custom", extra={"fn": "apple"}),
    Company(name="Google", ats="custom", extra={"fn": "google"}),  # brittle positional HTML parse

    # --- Community feed: SimplifyJobs New-Grad-Positions (GitHub) ---
    # Listings keep their real company names; the feed is already curated to
    # early-career roles, so keywords=[""] matches every title and only the
    # EXCLUDE list applies (drops the rare senior/intern stragglers).
    Company(name="New-Grad Feed (GitHub)", ats="github_newgrad", keywords=[""]),
]
