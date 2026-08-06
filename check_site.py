#!/usr/bin/env python3
"""
Boundary test for the Target Digital static site.
Run BEFORE declaring anything shipped:  py check_site.py

Checks the failure modes that have actually bitten this repo:
  1. Internal links point to .html files that exist
  2. In-page anchors (#id) have a matching element id on the page
  3. Local assets (img/video/source src) exist on disk — case-sensitive,
     because hosting is Linux and "Joanne.JFIF" != "Joanne.jfif" there
  4. No dead CTA <button>s (Book a Call / Claim / Audit / Get Started with
     no onclick and not wrapped in a link)
  5. No duplicated nav / mobile menu / nav CSS (the update_nav.py gotcha)

Exit code 0 = all clear, 1 = problems found.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PAGES = sorted(ROOT.glob("*.html"))
CTA_WORDS = re.compile(r"(book a call|book free|claim|growth audit|get started)", re.I)

problems = []  # (file, message)
warnings = []  # (file, message)


def page_ids(html):
    return set(re.findall(r'\bid="([^"]+)"', html))


for page in PAGES:
    html = page.read_text(encoding="utf-8", errors="replace")
    ids = page_ids(html)

    # 1. internal .html links resolve to a real file
    for href in re.findall(r'href="([^"#?]+\.html)(?:[?#][^"]*)?"', html):
        if href.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        target = href.lstrip("/")
        if not (ROOT / target).exists():
            problems.append((page.name, f"link -> missing page: {href}"))

    # href="/" means index.html
    for href in re.findall(r'href="(/)"', html):
        if not (ROOT / "index.html").exists():
            problems.append((page.name, "link -> '/' but index.html missing"))

    # 2. in-page anchors have a matching id
    for anchor in re.findall(r'href="#([^"]+)"', html):
        if anchor and anchor not in ids:
            problems.append((page.name, f"anchor -> #{anchor} has no matching id"))

    # 3. local assets exist — case-SENSITIVE (Windows .exists() lies; hosting is Linux)
    for src in re.findall(r'(?:src|href)="([^":]+\.(?:png|jpe?g|jfif|webp|gif|svg|mp4|webm|ico))"', html, re.I):
        if src.startswith(("http", "//", "data:", "#")):
            continue
        rel = Path(src.lstrip("/"))
        parent = (ROOT / rel).parent
        if not parent.exists():
            problems.append((page.name, f"asset -> missing dir for: {src}"))
            continue
        names = {p.name for p in parent.iterdir()}
        if rel.name in names:
            continue  # exact, case-correct match
        lower = {n.lower(): n for n in names}
        if rel.name.lower() in lower:
            problems.append((page.name, f"asset CASE MISMATCH: '{src}' but disk has '{lower[rel.name.lower()]}' (404s on Linux hosting)"))
        else:
            problems.append((page.name, f"asset -> missing file: {src}"))

    # 4. dead CTA buttons (cta text, no onclick, not an <a>)
    for btn in re.findall(r"<button\b[^>]*>(.*?)</button>", html, re.S | re.I):
        text = re.sub(r"<[^>]+>", "", btn)
        if CTA_WORDS.search(text):
            # find the full opening tag for this button to inspect attrs
            pass
    for m in re.finditer(r"<button\b([^>]*)>(.*?)</button>", html, re.S | re.I):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner)
        if CTA_WORDS.search(text) and "onclick" not in attrs.lower():
            problems.append((page.name, f'dead CTA button (no onclick/link): "{text.strip()[:40]}"'))

    # 5. duplication (the nav-injection gotcha)
    for label, pat, limit in [
        ("<nav> tags", r"<nav\b", 1),
        ('id="mobileNav"', r'id="mobileNav"', 1),
        ("toggleMobileNav() defs", r"function toggleMobileNav", 1),
        ("nav CSS blocks", r"/\* Nav links \*/", 1),
    ]:
        n = len(re.findall(pat, html))
        if n > limit:
            problems.append((page.name, f"duplicated {label}: found {n} (expected {limit})"))


# 6. sitemap coverage — this is what silently rotted: the sitemap sat at the
#    5 pages of the June restructure while the site grew to 14, so 8 live pages
#    were never offered to Google. A page must be either IN the sitemap or
#    explicitly listed here, so adding a page forces a yes/no rather than
#    letting it drop out unnoticed.
SITEMAP_EXCLUDE = {
    # Unlisted Smiles Clinic demo — direct-link only, promoted via
    # utm_campaign=aria_article, deliberately kept out of nav AND search.
    "medical.html",
}
BASE = "https://targetdigital.com.au/"
sitemap = ROOT / "sitemap.xml"

if not sitemap.exists():
    problems.append(("sitemap.xml", "missing — robots.txt points at it"))
else:
    sm = sitemap.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    listed = set()
    for loc in locs:
        if not loc.startswith(BASE):
            problems.append(("sitemap.xml", f"URL not on the canonical domain: {loc}"))
            continue
        name = loc[len(BASE):] or "index.html"
        if name in listed:
            problems.append(("sitemap.xml", f"duplicate URL: {loc}"))
        listed.add(name)
        if not (ROOT / name).exists():
            problems.append(("sitemap.xml", f"URL has no page on disk: {loc}"))

    for page in PAGES:
        if page.name not in listed and page.name not in SITEMAP_EXCLUDE:
            problems.append(("sitemap.xml", f"{page.name} ships but is not in the sitemap "
                                            "(add it, or add it to SITEMAP_EXCLUDE on purpose)"))
    for name in SITEMAP_EXCLUDE:
        if name in listed:
            problems.append(("sitemap.xml", f"{name} is meant to be unlisted but IS in the sitemap"))

    # robots.txt is public: naming an unlisted page there would advertise it.
    robots = ROOT / "robots.txt"
    if robots.exists():
        txt = robots.read_text(encoding="utf-8")
        if "sitemap.xml" not in txt.lower():
            problems.append(("robots.txt", "does not point at sitemap.xml"))
        for name in SITEMAP_EXCLUDE:
            if name in txt:
                problems.append(("robots.txt", f"names the unlisted page {name} — robots.txt is "
                                               "public, so this advertises what it's hiding"))

# 7. every page needs a canonical (index.html answers to both / and /index.html)
for page in PAGES:
    html = page.read_text(encoding="utf-8", errors="replace")
    if 'rel="canonical"' not in html:
        problems.append((page.name, "no rel=canonical link"))


print(f"Boundary test — {len(PAGES)} pages checked\n")
if warnings:
    print(f"⚠  {len(warnings)} warning(s):")
    for f, msg in warnings:
        print(f"   {f}: {msg}")
    print()
if problems:
    print(f"✗  {len(problems)} problem(s):")
    for f, msg in problems:
        print(f"   {f}: {msg}")
    print("\nFAIL — fix the above before shipping.")
    sys.exit(1)
else:
    print("✓  No broken links, dead CTAs, missing assets, or duplicated nav. Clear to ship.")
    sys.exit(0)
