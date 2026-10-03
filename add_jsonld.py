#!/usr/bin/env python3
"""Install JSON-LD (@graph) on index / funnel / outbound. Idempotent.

Organization + WebSite on the homepage; Service + FAQPage on the three pages
that carry an FAQ. FAQ text is read from the page's own .faq-q/.faq-a markup
and the description from the page's own <meta description>, so schema can never
drift from what visitors read. Run:  py add_jsonld.py   (--check = verify only)
"""
import html as H, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://targetdigital.com.au"
SERVICES = {
    "funnel.html": ("AI Lead Gen Engine", "/funnel.html"),
    "outbound.html": ("AI Outbound Call Engine", "/outbound.html"),
}
PAGES = ["index.html", "funnel.html", "outbound.html"]
BLOCK = re.compile(r'<script type="application/ld\+json">.*?</script>\n?', re.S)
ORG = {
    "@type": "Organization", "@id": SITE + "/#org", "name": "Target Digital", "url": SITE + "/",
    "logo": SITE + "/target-digital-logo.png", "email": "rop@targetdigital.com.au",
    "areaServed": {"@type": "Country", "name": "Australia"},
    "address": {"@type": "PostalAddress", "addressLocality": "Brisbane",
                "addressRegion": "QLD", "addressCountry": "AU"},
}


def strip(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def faq(src):
    out = []
    for q, a in re.findall(r'<button class="faq-q">(.*?)<span class="faq-icon">.*?</span></button>\s*'
                           r'<div class="faq-a"><p>(.*?)</p></div>', src, re.S):
        out.append({"@type": "Question", "name": strip(q),
                    "acceptedAnswer": {"@type": "Answer", "text": strip(a)}})
    return out


def build(name, src):
    desc = H.unescape(re.search(r'<meta name="description" content="([^"]*)"', src).group(1))
    graph = []
    if name == "index.html":
        graph += [dict(ORG, description=desc),
                  {"@type": "WebSite", "@id": SITE + "/#site", "url": SITE + "/",
                   "name": "Target Digital", "publisher": {"@id": SITE + "/#org"},
                   "inLanguage": "en-AU"}]
    else:
        svc, path = SERVICES[name]
        graph += [ORG, {"@type": "Service", "name": svc, "serviceType": svc, "url": SITE + path,
                        "description": desc, "provider": {"@id": SITE + "/#org"},
                        "areaServed": {"@type": "Country", "name": "Australia"}}]
    qs = faq(src)
    if qs:
        graph.append({"@type": "FAQPage", "mainEntity": qs})
    body = json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False)
    return '<script type="application/ld+json">\n' + body + "\n</script>\n"


bad = 0
for name in PAGES:
    p = ROOT / name
    src = p.read_text(encoding="utf-8")
    want = build(name, src)
    old = BLOCK.findall(src)
    if "--check" in sys.argv:
        if old != [want]:
            print("STALE:", name); bad += 1
        continue
    new = BLOCK.sub("", src)
    new = new.replace("<style>", want + "<style>", 1)
    p.write_text(new, encoding="utf-8", newline="")
    print("ok", name)
sys.exit(1 if bad else 0)
