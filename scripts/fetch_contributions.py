"""Scrape the public contribution calendar into data/contributions.json.

GitHub serves the calendar as an HTML fragment at /users/<name>/contributions,
the same one the profile page renders. No token needed.

    python scripts/fetch_contributions.py
"""

import json
import re
import sys
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "AbhishekGajera"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

COUNT_RE = re.compile(r"^(\d[\d,]*|No) contributions?")


def fetch() -> str:
    resp = requests.get(
        f"https://github.com/users/{USERNAME}/contributions",
        headers={"User-Agent": f"{USERNAME}-profile-readme"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tips = {tip.get("for"): tip.get_text(strip=True) for tip in soup.select("tool-tip[for]")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        match = COUNT_RE.match(tips.get(cell.get("id"), ""))
        count = 0 if not match or match.group(1) == "No" else int(match.group(1).replace(",", ""))
        days.append({"date": cell["data-date"], "level": int(cell.get("data-level", 0)), "count": count})
    days.sort(key=lambda d: d["date"])
    if len(days) < 300:
        # The markup changed; fail loudly so the workflow run goes red.
        sys.exit(f"parsed only {len(days)} days; GitHub's calendar markup may have changed")
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # Today may not have activity yet; the streak is still alive if yesterday did.
    current = 0
    tail = days[:-1] if days and not days[-1]["count"] else days
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return current, longest


def main() -> None:
    days = parse(fetch())
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly: OrderedDict[str, int] = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    data = {
        "username": USERNAME,
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"]),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {data['total']} contributions, {len(days)} days")


if __name__ == "__main__":
    main()
