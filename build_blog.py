#!/usr/bin/env python3
"""Build the blog: blog-src/<slug>.html  ->  blog/<slug>.html, plus the /blog.html index.

A source file is a front-matter block (title, slug, target_keyword, meta_description,
date, og_image) followed by the article's inner HTML. The page chrome (GA4 snippet, CSS,
nav, footer, GA4 event tracker) is lifted from ai-lead-generation-brisbane.html at build
time, so a post is rebuilt with whatever the rest of the site currently uses.
Idempotent. Also adds the blog URLs to sitemap.xml.

Run:  py build_blog.py          (then py add_og_tags.py && py add_footer_links.py && py check.py)
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE = "https://targetdigital.com.au"
CHROME_SRC = ROOT / "ai-lead-generation-brisbane.html"
CAL = "https://calendly.com/ropkiplagat/intro-to-sales-target-digital"


def read(p):
    return Path(p).read_text(encoding="utf-8")


def grab(src, start, end, inclusive_end=True):
    i = src.index(start)
    j = src.index(end, i) + (len(end) if inclusive_end else 0)
    return src[i:j]


chrome = read(CHROME_SRC)
GA_HEAD = grab(chrome, "<!-- Google Analytics (GA4) -->", "gtag('config', 'G-DVJVMK97NH');\n</script>")
STYLE = grab(chrome, "<style>", "</style>")
NAV = grab(chrome, "<nav>", "</script>\n")          # nav + mobile nav + toggle script
FOOTER = grab(chrome, "<footer>", "</footer>")
EVENTS = grab(chrome, "<!-- ga4-events:start", "<!-- ga4-events:end -->")
EXTRA_CSS = """<style>
.legal ol{margin:0 0 16px 22px;padding:0}.legal ol li{padding-left:6px;margin-bottom:12px}.legal ol li::before{content:none}
.legal ul.posts{margin-top:8px}.legal ul.posts li::before{content:"→"}
.legal .btn.ghost{margin-left:0}
.legal table{width:100%;border-collapse:collapse;margin:8px 0 20px;font-size:15px}
.legal th,.legal td{text-align:left;padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.1);vertical-align:top}
.legal th{color:var(--white);font-family:'Syne',sans-serif;font-size:13px;text-transform:uppercase;letter-spacing:.04em}
@media (max-width:640px){.legal table{display:block;overflow-x:auto}}
</style>"""


def front_matter(txt):
    end = txt.index("\n---", 3)
    fm = {}
    for line in txt[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, txt[end + 4:].lstrip("\n")


def head(title, desc, canon, img, extra="", og=True):
    og = f"""<meta property="og:type" content="article">
<meta property="og:site_name" content="Target Digital">
<meta property="og:locale" content="en_AU">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{SITE}/{img}">
<meta property="og:image:width" content="1456">
<meta property="og:image:height" content="822">
<meta property="og:image:alt" content="Target Digital AI">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{SITE}/{img}">""" if og else ""  # root pages get theirs from add_og_tags.py
    return f"""<!DOCTYPE html>
<html lang="en-AU">
<head>
<meta charset="UTF-8">
{GA_HEAD}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
{og}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
{extra}
{STYLE}
{EXTRA_CSS}
</head>
<body>

"""


def jsonld(fm, canon):
    import json
    g = {"@context": "https://schema.org", "@type": "BlogPosting",
         "headline": fm["title"], "description": fm["meta_description"],
         "datePublished": fm["date"], "dateModified": fm["date"],
         "mainEntityOfPage": canon, "inLanguage": "en-AU",
         "author": {"@type": "Organization", "name": "Target Digital", "url": SITE + "/"},
         "publisher": {"@type": "Organization", "name": "Target Digital", "url": SITE + "/",
                       "logo": {"@type": "ImageObject", "url": SITE + "/target-digital-logo.png"}}}
    return '<script type="application/ld+json">\n' + json.dumps(g, indent=2) + "\n</script>"


def build_post(src_path):
    fm, body = front_matter(read(src_path))
    slug = fm["slug"]
    canon = f"{SITE}/blog/{slug}.html"
    fm_block = (f"---\ntitle: {fm['title']}\nslug: {slug}\ntarget_keyword: {fm['target_keyword']}\n"
                f"meta_description: {fm['meta_description']}\ndate: {fm['date']}\n---\n")
    page = (fm_block + head(fm["title"], fm["meta_description"], canon, fm.get("og_image", "funnel-hero.png"),
                            jsonld(fm, canon))
            + NAV + '\n<main class="legal">\n' + body.strip() + "\n</main>\n\n" + FOOTER + "\n\n" + EVENTS + "\n</body>\n</html>\n")
    out = ROOT / "blog" / f"{slug}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="")
    return fm


def build_index(posts):
    title = "Lead Follow-Up and AI Calling Guides | Target Digital"
    desc = "Practical guides on responding to leads fast, AI outbound calling and Australian rules, from the team at Target Digital in Brisbane."
    canon = SITE + "/blog.html"
    items = "\n".join(
        f'  <li><a href="/blog/{p["slug"]}.html"><strong>{p["title"]}</strong></a><br>{p["meta_description"]}</li>'
        for p in sorted(posts, key=lambda p: p["date"], reverse=True))
    body = f"""<h1>Guides on <span class="accent">lead follow-up</span> and AI calling</h1>
<p class="updated">From Target Digital, Brisbane. Every figure is traced to its source.</p>
<ul class="posts">
{items}
</ul>
<p><a class="btn" href="{CAL}" target="_blank" rel="noopener">Book a Call</a></p>"""
    page = (head(title, desc, canon, "funnel-hero.png", og=False)
            + NAV + '\n<main class="legal">\n' + body + "\n</main>\n\n" + FOOTER + "\n\n" + EVENTS + "\n</body>\n</html>\n")
    (ROOT / "blog.html").write_text(page, encoding="utf-8", newline="")


def build_faq():
    """faq.html from blog-src/_faq.json: [{"section","q","a"}], answers are inner HTML."""
    import json
    items = json.loads((ROOT / "blog-src" / "_faq.json").read_text(encoding="utf-8"))
    title = "Lead Follow-Up and AI Calling FAQ | Target Digital"
    desc = "Answers on speed to lead, AI receptionist and lead generation costs, how AI lead qualification works, and Australian calling rules, from Target Digital."
    canon = SITE + "/faq.html"
    plain = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": i["q"], "acceptedAnswer": {"@type": "Answer", "text": plain(i["a"])}} for i in items]}
    body, last = ['<h1>Lead follow-up and AI calling: <span class="accent">your questions</span></h1>',
                  '<p class="updated">Short answers, each linked to the guide that backs it up. General information, not legal advice.</p>'], None
    for i in items:
        if i["section"] != last:
            body.append(f"<h2>{i['section']}</h2>"); last = i["section"]
        body.append(f"<h3>{i['q']}</h3>\n<p>{i['a']}</p>")
    body.append(f'<p style="margin-top:28px"><a class="btn" href="{CAL}" target="_blank" rel="noopener">Book a Call</a></p>')
    ld = '<script type="application/ld+json">\n' + json.dumps(schema, indent=2, ensure_ascii=False) + "\n</script>"
    page = (head(title, desc, canon, "funnel-hero.png", ld, og=False)
            + NAV + '\n<main class="legal">\n' + "\n".join(body) + "\n</main>\n\n" + FOOTER + "\n\n" + EVENTS + "\n</body>\n</html>\n")
    (ROOT / "faq.html").write_text(page, encoding="utf-8", newline="")


def add_sitemap(urls):
    sm = ROOT / "sitemap.xml"
    t = sm.read_text(encoding="utf-8")
    for u in urls:
        if u not in t:
            t = t.replace("</urlset>", f"  <url><loc>{u}</loc></url>\n</urlset>")
    sm.write_text(t, encoding="utf-8", newline="")


posts = [build_post(p) for p in sorted((ROOT / "blog-src").glob("*.html"))]
build_index(posts)
if (ROOT / "blog-src" / "_faq.json").exists():
    build_faq()
add_sitemap([SITE + "/blog.html", SITE + "/faq.html"] + [f"{SITE}/blog/{p['slug']}.html" for p in posts])
print(f"built {len(posts)} post(s) + blog.html + faq.html; sitemap updated")
