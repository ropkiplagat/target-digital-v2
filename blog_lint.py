#!/usr/bin/env python3
"""Advisory prose lint for blog-src/*.html. Flags AI-writing tells, never fails a build.

Rules adapted from stop-slop (MIT, github.com/hardikpandya/stop-slop): filler adverbs,
throat-clearing, "not X, it's Y" contrasts, vague declaratives, false agency, em dashes.
Deliberately NOT run as a gate: legal and quoted text legitimately contains "immediately",
"expressly" and similar, and the house rules in check.py are the real contract.

Run:  py blog_lint.py [file ...]      (default: every blog-src/*.html)
Exit code is always 0. Read the output, then judge each hit in context.
Skips: quoted text between double quotes, table cells, headings, and <a> link text.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
FILLER = r"\b(really|just|literally|genuinely|honestly|simply|actually|truly|fundamentally|inherently|inevitably|interestingly|importantly|crucially|seriously|plainly)\b"
THROAT = (r"(here's (the|what|why|this|that)|let me be clear|the truth is|it turns out|make no mistake|"
          r"in today's|it's worth noting|at the end of the day|when it comes to|the reality is|let that sink in|"
          r"in this (section|guide|post)|as we'll see)")
CONTRAST = r"\b(it'?s not|isn'?t|not because|not just|not only|stops being)\b[^.]{0,60}\b(it'?s|but|starts being|instead)\b"
VAGUE = r"\bthe (implications|stakes|consequences|reasons) are\b"
AGENCY = r"\b(the (data|market|culture|decision|conversation|complaint) (tells|rewards|shifts|emerges|moves|becomes))\b"
LY_OK = {"only", "early", "family", "daily", "weekly", "monthly", "apply", "supply", "reply", "july", "likely",
         "friendly", "assembly", "rely", "multiply", "imply", "hourly", "yearly", "quarterly", "italy", "holy"}


def prose(t):
    t = t.split("</head>")[-1]
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>", "", t, flags=re.S)
    m = re.search(r"<main.*?</main>", t, re.S)
    t = m.group(0) if m else t
    t = re.sub(r"<(h[1-6]|table|a)\b.*?</\1>", " ", t, flags=re.S)       # headings, tables, link text
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r'"[^"]{8,}"', " ", t)                                     # quoted text
    return re.sub(r"\s+", " ", t)


def lint(path):
    txt = prose(Path(path).read_text(encoding="utf-8"))
    words = max(len(txt.split()), 1)
    hits = []
    for name, pat in (("filler", FILLER), ("throat-clearing", THROAT), ("contrast", CONTRAST),
                      ("vague", VAGUE), ("false-agency", AGENCY)):
        for m in re.finditer(pat, txt, re.I):
            a, b = max(m.start() - 45, 0), min(m.end() + 45, len(txt))
            hits.append((name, txt[a:b]))
    ly = [m.group(0) for m in re.finditer(r"\b\w{5,}ly\b", txt) if m.group(0).lower() not in LY_OK]
    if "—" in txt:
        hits.append(("em-dash", "em dash in prose"))
    print(f"\n{Path(path).name}: {words} words, {len(ly)} -ly adverbs ({100*len(ly)/words:.1f} per 100), {len(hits)} flags")
    for name, ctx in hits:
        print(f"  [{name}] ...{ctx}...")
    if ly:
        print("  -ly:", ", ".join(sorted(set(w.lower() for w in ly))))


files = sys.argv[1:] or sorted(str(p) for p in (ROOT / "blog-src").glob("*.html"))
for f in files:
    lint(f)
