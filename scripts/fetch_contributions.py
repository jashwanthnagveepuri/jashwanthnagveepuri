#!/usr/bin/env python3
"""Scrape the public GitHub contributions page (no token) and write
data/contributions.json with per-day entries plus aggregate stats.
"""
import json
import re
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "jashwanthnagveepuri"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path("data/contributions.json")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

COUNT_RE = re.compile(r"^(\d+) contribution")
MIN_DAYS = 300


def fetch_html() -> str:
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(URL, headers={"User-Agent": UA}, timeout=60)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"failed to fetch {URL}: {last_err}")


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # tooltips carry the real per-day counts: "N contributions on ..." /
    # "No contributions on ..." and reference the cell via for=<cell id>.
    counts = {}
    for tip in soup.select("tool-tip[for]"):
        text = tip.get_text(strip=True)
        m = COUNT_RE.match(text)
        counts[tip["for"]] = int(m.group(1)) if m else 0

    days = []
    for cell in soup.select("[data-date][data-level]"):
        d = cell["data-date"]
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            continue
        days.append({
            "date": d,
            "count": counts.get(cell.get("id"), 0),
            "level": int(cell["data-level"]),
        })
    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    best = max(days, key=lambda d: d["count"]) if days else {"date": None, "count": 0}

    monthly = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    # longest streak: max run of consecutive days with count > 0
    longest = run = 0
    prev = None
    for d in days:
        cur = date.fromisoformat(d["date"])
        if d["count"] > 0 and (prev is None or (cur - prev).days == 1 and run > 0):
            run += 1
        elif d["count"] > 0:
            run = 1
        else:
            run = 0
        longest = max(longest, run)
        prev = cur

    # current streak: run of count>0 days ending today or yesterday
    current = 0
    idx = len(days) - 1
    if idx >= 0 and days[idx]["count"] == 0:
        idx -= 1  # allow the streak to end yesterday
    while idx >= 0 and days[idx]["count"] > 0:
        current += 1
        idx -= 1

    return {
        "total_last_year": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": m, "count": c} for m, c in sorted(monthly.items())],
    }


def main() -> None:
    html = fetch_html()
    days = parse_days(html)
    if len(days) < MIN_DAYS:
        raise SystemExit(f"only parsed {len(days)} day cells (need >= {MIN_DAYS})")
    payload = {"days": days, "stats": compute_stats(days)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    s = payload["stats"]
    print(f"{OUT}: {len(days)} days, {s['total_last_year']} contributions, "
          f"current streak {s['current_streak']}, longest {s['longest_streak']}")


if __name__ == "__main__":
    main()
