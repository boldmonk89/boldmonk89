#!/usr/bin/env python3
"""fetch_contributions.py — scrape a real contribution calendar, NO auth.

GitHub serves the calendar as a plain HTML fragment at
    https://github.com/users/<user>/contributions
so we can read it with just requests + BeautifulSoup: no token, no API rate
limit, nothing to 404. Writes data/contributions.json for render_heatmap_svg.py.

    GH_PROFILE_USER=boldmonk89 python scripts/fetch_contributions.py
"""
import os
import re
import json
import sys
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_PROFILE_USER", "boldmonk89")
OUT = os.path.join("data", "contributions.json")
URL = f"https://github.com/users/{USER}/contributions"
UA = "Mozilla/5.0 (profile-art contribution scraper)"


def scrape():
    r = requests.get(URL, headers={"User-Agent": UA,
                     "X-Requested-With": "XMLHttpRequest"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # id -> exact count, from the <tool-tip> elements (modern markup)
    counts = {}
    for tip in soup.find_all("tool-tip"):
        fid = tip.get("for")
        if not fid:
            continue
        txt = tip.get_text(" ", strip=True)
        m = re.search(r"([\d,]+)\s+contribution", txt)
        counts[fid] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for td in soup.select("td[data-date]"):
        d = td.get("data-date")
        level = int(td.get("data-level", 0))
        cid = td.get("id")
        # exact count if we have it, else fall back to the visual level
        if cid in counts:
            c = counts[cid]
        elif td.has_attr("data-count"):
            c = int(td["data-count"])
        else:
            c = level
        days.append({"date": d, "count": c, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def streaks(days):
    total = sum(d["count"] for d in days)
    today = date.today().isoformat()
    # longest run of consecutive active days
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    # current streak: walk backwards from the last non-future day
    current = 0
    for d in reversed([x for x in days if x["date"] <= today]):
        if d["count"] > 0:
            current += 1
        else:
            break
    return total, current, longest


def main():
    days = scrape()
    if not days:
        print(f"WARNING: no contribution cells found for '{USER}' "
              f"(private profile or bad username?)", file=sys.stderr)
    total, current, longest = streaks(days)
    payload = {
        "user": USER,
        "generated": datetime.utcnow().isoformat() + "Z",
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "days": days,
    }
    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"{OUT}: {len(days)} days, {total} contributions, "
          f"current {current}d, longest {longest}d")


if __name__ == "__main__":
    main()
