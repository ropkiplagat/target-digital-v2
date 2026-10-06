#!/usr/bin/env python3
"""Advisory external-link check for built blog pages. Never fails a build.

Fetches every external https link in the given pages (default: blog/*.html and faq.html) and
reports the status. 200 and 3xx are fine. 403/429 usually mean the site blocks scripts:
verify those by hand. 404/410/5xx need a fix.

Run:  py blog_links.py [file ...]
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
SKIP = ("calendly.com", "fonts.googleapis.com", "fonts.gstatic.com", "googletagmanager.com", "targetdigital.com.au")


def status(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link check)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001 - report, never crash
        return f"ERR {type(e).__name__}"


files = sys.argv[1:] or sorted(str(p) for p in list((ROOT / "blog").glob("*.html")) + [ROOT / "faq.html"])
seen = {}
for f in files:
    txt = Path(f).read_text(encoding="utf-8")
    for url in sorted(set(re.findall(r'href=["\'](https?://[^"\']+)["\']', txt))):
        if any(s in url for s in SKIP):
            continue
        if url not in seen:
            seen[url] = status(url)
        s = seen[url]
        flag = "ok " if s in (200, 301, 302, 303, 307, 308) else ("chk" if s in (403, 429) else "FIX")
        print(f"[{flag}] {s}  {url}   ({Path(f).name})")
print(f"\n{sum(1 for s in seen.values() if s not in (200, 301, 302, 303, 307, 308, 403, 429))} link(s) need a fix; "
      f"{sum(1 for s in seen.values() if s in (403, 429))} to verify by hand.")
