#!/usr/bin/env python3
"""
check.py — Target Digital gatekeeper.

Runs a fixed set of mechanical pass/fail gates after every ticket. If ANY hard-stop
gate fails, this script exits non-zero and work stops until it's fixed — no deferring.

    Usage:  PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py check.py
            py check.py --strict     # treat warnings as failures too (periodic sweep)

Design rule (do not weaken): a gate may only HARD-stop if its mechanism is
denylist- or citation-PRECISE. Anything judgment-based (heuristics) stays a WARNING.
That keeps a red gate meaningful — it always means a real problem, never paranoia.

Zones (different rules apply to different files):
  A  published site      -> root-level *.html            (Target Digital's own marketing)
  B  client deliverables -> clients/** , blog/** , email-templates/**
  C  internal/source      -> everything else             (scripts, brand/, call-proxy/, config)

To extend a gate, edit the CONFIG block below — most gates are data-driven.
This file is the companion to check_site.py (the site-integrity boundary test, wrapped by G13).
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG  — edit here, not in the gate code.
# ─────────────────────────────────────────────────────────────────────────────

# G1 — provider secret patterns. These are unambiguous, so they HARD-stop.
SECRET_PATTERNS = [
    ("Anthropic key",   r"sk-ant-[A-Za-z0-9_-]{20,}"),
    ("OpenAI/live key", r"sk-(?:live_)?[A-Za-z0-9]{32,}"),
    ("AWS access key",  r"AKIA[0-9A-Z]{16}"),
    ("Google API key",  r"AIza[0-9A-Za-z_-]{35}"),
    ("Slack token",     r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    ("Private key PEM", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
# G1b — generic "secret = literal" assignment. Judgment-y (could be a placeholder),
# so it only WARNS. Placeholder-looking values are ignored.
SECRET_GENERIC = re.compile(
    r"""(?ix)\b(api[_-]?key|secret|token|passwd|password|private[_-]?key)\b\s*[:=]\s*['"]([^'"]{16,})['"]"""
)
SECRET_PLACEHOLDERS = ("your-", "xxx", "changeme", "example", "placeholder",
                       "replace", "<", "dummy", "test", "sample", "n8n_api_key")

# G5 — retired / forbidden proof. Exact strings we have banned. HARD.
# Claims registry: anything here is NOT VERIFIED and must never appear in content.
RETIRED_CLAIMS = ["500,000%", "500000%", "500,000 %", "[metric]", "XX%", "XXX leads",
                  # NOT VERIFIED (flagged 2026-07-12): fabricated numbers, killed everywhere.
                  "Brijesh", "Robotics For Sure"]

# G7 — regulated / unsubstantiated claim denylist (case-insensitive substrings). HARD.
REGULATED_CLAIMS = [
    "ndis approved", "ndis endorsed", "approved by the ndis", "official ndis",
    "government approved", "government endorsed", "endorsed by the government",
    "guaranteed funding", "guaranteed results", "guaranteed leads", "guaranteed roi",
    "we guarantee you", "guaranteed to double",
]

# G6 — fabrication-smell heuristics (WARN only).
FABRICATION_SMELLS = [
    r"\bstudies show\b", r"\bexperts agree\b", r"\bscientifically proven\b",
    r"\b#1\b", r"\bworld[- ]class\b", r"\b\d{2,}x more\b",
]

# G10 — half-finished content. Text markers (visible text) + placeholder URLs (attrs). HARD.
PLACEHOLDER_TEXT = ["lorem ipsum", "replace me", "your text here", "insert here",
                    "placeholder text", "todo:", "fixme:", "coming soon"]
PLACEHOLDER_URLS = ["example.com", "your-domain", "yourdomain",
                    "your-n8n-webhook.com", "your-webhook", "changeme"]

# G11 — the only merge tokens allowed in email templates. Unknown token = typo -> HARD.
TOKEN_ALLOWLIST = {"first_name", "addMo", "addYr", "unsubscribe_url"}

# G12 — booking-link canon + pricing coherence.
CANONICAL_CALENDLY = "calendly.com/ropkiplagat/intro-to-sales-target-digital"
RETIRED_CALENDLY = ["calendly.com/targetdigital/growth-audit"]
RETIRED_PRICES = []                                   # add superseded prices here -> HARD
CANONICAL_PRICES = {"$2,000", "$500", "$4,500", "$1,500", "$7,500", "$3,000"}
KNOWN_NON_PRICE = {"$10", "$80", "$150"}              # ROI / example figures, not pricing
PRICING_PAGES = ["index.html", "funnel.html", "outbound.html"]

# G8 — email marketing must identify the sender. Both must be present per template.
EMAIL_SENDER_MARKERS = ["target digital"]

# G14 — US spellings on an .com.au property (WARN). Scanned on VISIBLE TEXT only.
US_SPELLINGS = ["optimize", "organize", "customize", "maximize", "minimize", "analyze",
                "personalize", "prioritize", "specialize", "color", "favorite",
                "behavior", "catalog", "fulfill", "traveled", "canceled"]

# G3 — contact addresses that are legitimately public (won't be flagged as leaked PII).
SAFE_EMAILS = {"hello@targetdigital.com.au", "support@targetdigital.com.au",
               "rop@targetdigital.com.au", "unsubscribe@targetdigital.com.au",
               "ropkiplagat@gmail.com"}

# G9 — blog format contract thresholds.
BLOG_MIN_WORDS = 1000
META_LEN = (120, 155)
TITLE_LEN = (50, 60)


# ─────────────────────────────────────────────────────────────────────────────
# Findings
# ─────────────────────────────────────────────────────────────────────────────
HARD, WARN = "HARD", "WARN"
_findings = []  # (gate, level, path, line|None, msg)


def report(gate, level, path, line, msg):
    _findings.append((gate, level, path, line, msg))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def git_tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout
        return [p.strip() for p in out.splitlines() if p.strip()]
    except Exception:
        # Fallback: walk the tree (skips .git, node_modules).
        files = []
        for base, dirs, fs in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            for f in fs:
                files.append(os.path.relpath(os.path.join(base, f), ROOT).replace("\\", "/"))
        return files


def read(path):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, UnicodeError):
        return None


def strip_code(html):
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    return html


def visible_text(html):
    """Client-visible copy: body text (code stripped) + title/meta/alt (SEO-facing)."""
    body = re.sub(r"<[^>]+>", " ", strip_code(html))
    body = re.sub(r"&[a-z]+;", " ", body)
    extras = []
    for m in re.finditer(r'<title[^>]*>(.*?)</title>', html, re.I | re.S):
        extras.append(m.group(1))
    for m in re.finditer(r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]*content=["\']([^"\']*)["\']', html, re.I):
        extras.append(m.group(1))
    for m in re.finditer(r'\balt=["\']([^"\']*)["\']', html, re.I):
        extras.append(m.group(1))
    return body + " \n " + " ".join(extras)


def attr_urls(html):
    return [m.group(1) for m in
            re.finditer(r'(?:href|src|action)\s*=\s*["\']([^"\']*)["\']', html, re.I)]


def line_of(text, needle):
    low = text.lower()
    idx = low.find(needle.lower())
    if idx < 0:
        return None
    return text.count("\n", 0, idx) + 1


def load_yaml(path):
    """PyYAML if available, else a minimal parser for our flat schema:
    top-level `key:` -> list of `- k: v` maps with scalar (comma-list) values."""
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return {}
    try:
        import yaml
        with open(full, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass
    data, cur_list, cur_item = {}, None, None
    for raw in open(full, encoding="utf-8"):
        line = raw.rstrip("\n")
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if re.match(r"^\S.*:\s*(\[\s*\])?\s*$", line):        # top-level key:  (or key: [])
            key = line.split(":", 1)[0].strip()
            data[key], cur_list, cur_item = [], data.setdefault(key, []), None
            data[key] = cur_list = []
            continue
        m = re.match(r"^\s*-\s*(.*)$", line)                  # new list item
        if m and cur_list is not None:
            cur_item = {}
            cur_list.append(cur_item)
            rest = m.group(1).strip()
            if rest:
                k, v = _kv(rest)
                if k:
                    cur_item[k] = v
            continue
        if cur_item is not None and ":" in line:             # field within item
            k, v = _kv(s)
            if k:
                cur_item[k] = v
    return data


def _kv(s):
    if ": " in s:
        k, v = s.split(": ", 1)
    elif s.endswith(":"):
        k, v = s[:-1], ""
    elif ":" in s:
        k, v = s.split(":", 1)
    else:
        return None, None
    return k.strip(), v.strip().strip('"').strip("'")


# ─────────────────────────────────────────────────────────────────────────────
# Zone classification
# ─────────────────────────────────────────────────────────────────────────────
def classify(tracked):
    z = {"A": [], "email": [], "blog": [], "clients": [], "C": []}
    for p in tracked:
        if "/" not in p and p.endswith(".html"):
            z["A"].append(p)
        elif p.startswith("email-templates/"):
            z["email"].append(p)
        elif p.startswith("blog/"):
            z["blog"].append(p)
        elif p.startswith("clients/"):
            z["clients"].append(p)
        else:
            z["C"].append(p)
    return z


# ─────────────────────────────────────────────────────────────────────────────
# Gates
# ─────────────────────────────────────────────────────────────────────────────
def g1_secrets(tracked):
    for p in tracked:
        if p == "check.py":                     # don't flag our own pattern literals
            continue
        txt = read(p)
        if txt is None:
            continue
        for lineno, line in enumerate(txt.splitlines(), 1):
            for name, pat in SECRET_PATTERNS:
                if re.search(pat, line):
                    report("G1", HARD, p, lineno, f"hardcoded secret ({name})")
            m = SECRET_GENERIC.search(line)
            if m and not any(ph in m.group(2).lower() for ph in SECRET_PLACEHOLDERS):
                report("G1", WARN, p, lineno, f"possible secret in `{m.group(1)}=` assignment")


def g2_client_isolation(z, clients):
    for p in z["clients"]:
        parts = p.split("/")
        if len(parts) < 3:                      # clients/<slug>/<file>
            continue
        owner = parts[1]
        txt = read(p)
        if txt is None:
            continue
        low = txt.lower()
        for c in clients:
            if c["slug"] == owner:
                continue
            for ident in c["identifiers"]:
                if ident and ident.lower() in low:
                    report("G2", HARD, p, line_of(txt, ident),
                           f"references another client '{c['slug']}' via '{ident}'")


def g3_pii(z):
    email_re = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    phone_re = re.compile(r"(?:\+?61[\s-]?4|\b04)\d{2}[\s-]?\d{3}[\s-]?\d{3}")
    for p in z["A"] + z["email"] + z["blog"] + z["clients"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        vis = visible_text(txt) if p.endswith(".html") else txt
        for em in set(email_re.findall(vis)):
            if em.lower() not in SAFE_EMAILS:
                report("G3", WARN, p, line_of(txt, em), f"email address in copy: {em}")
        for ph in set(phone_re.findall(vis)):
            report("G3", WARN, p, line_of(txt, ph), f"AU mobile number in copy: {ph}")


def g4_evidence(z, clients):
    for c in clients:
        slug = c["slug"]
        ev = load_yaml(f"clients/{slug}/evidence.yml")
        approved, integrity_ok = set(), True
        for entry in ev.get("claims", []):
            src = (entry.get("source") or "").strip()
            if not src or src.lower() in ("tbd", "n/a", "na", "-"):
                integrity_ok = False
                report("G4", HARD, f"clients/{slug}/evidence.yml", None,
                       f"claim '{entry.get('value', entry.get('text', '?'))}' has a blank/placeholder source")
            val = (entry.get("value") or "").strip().lower()
            if val:
                approved.add(re.sub(r"\s+", "", val))
        files = [p for p in z["clients"]
                 if p.startswith(f"clients/{slug}/") and (p.endswith(".html") or p.endswith(".md"))]
        for p in files:
            txt = read(p)
            if txt is None:
                continue
            vis = visible_text(txt) if p.endswith(".html") else txt
            for m in re.finditer(r"\$[0-9][0-9,]*(?:\.\d+)?|\b\d+(?:\.\d+)?%|\b\d+x\b", vis):
                claim = re.sub(r"\s+", "", m.group(0).lower())
                if claim not in approved:
                    report("G4", HARD, p, line_of(txt, m.group(0)),
                           f"un-sourced claim '{m.group(0)}' (not in clients/{slug}/evidence.yml)")


def g5_retired_proof(z):
    for p in z["A"] + z["email"] + z["blog"] + z["clients"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        vis = visible_text(txt) if p.endswith(".html") else txt
        for bad in RETIRED_CLAIMS:
            if bad.lower() in vis.lower():
                report("G5", HARD, p, line_of(txt, bad), f"retired/forbidden proof: '{bad}'")


def g6_fabrication_smell(z):
    for p in z["email"] + z["blog"] + z["clients"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        vis = visible_text(txt) if p.endswith(".html") else txt
        for pat in FABRICATION_SMELLS:
            m = re.search(pat, vis, re.I)
            if m:
                report("G6", WARN, p, line_of(txt, m.group(0)),
                       f"fabrication smell: '{m.group(0)}' — verify it's sourced")


def g7_regulated(z):
    for p in z["A"] + z["email"] + z["blog"] + z["clients"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        vis = visible_text(txt) if p.endswith(".html") else txt
        low = vis.lower()
        for bad in REGULATED_CLAIMS:
            if bad in low:
                report("G7", HARD, p, line_of(txt, bad), f"regulated/unsubstantiated claim: '{bad}'")


def g8_email_compliance(z):
    for p in z["email"]:
        if not re.search(r"email\d+\.html$", p):     # the portable templates (skip .n8n / README)
            continue
        txt = read(p)
        if txt is None:
            continue
        low = txt.lower()
        if "unsubscribe" not in low:
            report("G8", HARD, p, None, "no unsubscribe mechanism (AU Spam Act)")
        if not any(m in low for m in EMAIL_SENDER_MARKERS):
            report("G8", HARD, p, None, "no sender identification (AU Spam Act)")


def g9_blog_format(z):
    for p in z["blog"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        fm = _front_matter(txt)
        if not fm or "target_keyword" not in fm:
            report("G9", HARD, p, None,
                   "missing front matter (need target_keyword, meta_description, slug)")
            continue
        kw = fm.get("target_keyword", "").strip().lower()
        title = fm.get("title", "").strip()
        meta = fm.get("meta_description", "").strip()
        slug = fm.get("slug", "").strip().lower()
        body = txt.split("---", 2)[-1] if txt.strip().startswith("---") else txt
        vis = visible_text(body) if p.endswith(".html") else body
        first_sentence = re.split(r"(?<=[.!?])\s", vis.strip(), 1)[0].lower() if vis.strip() else ""
        h2s = re.findall(r"(?:^#{2}\s+(.*)$)|(?:<h2[^>]*>(.*?)</h2>)", body, re.I | re.M)
        h2_text = " ".join(a or b for a, b in h2s).lower()

        if kw and kw not in title.lower():
            report("G9", HARD, p, None, f"keyword '{kw}' not in title")
        if kw and kw not in meta.lower():
            report("G9", HARD, p, None, f"keyword '{kw}' not in meta description")
        if kw and kw.replace(" ", "-") not in slug and kw not in slug:
            report("G9", HARD, p, None, f"keyword '{kw}' not in slug")
        if kw and kw not in first_sentence:
            report("G9", HARD, p, None, f"keyword '{kw}' not in first sentence")
        if kw and kw not in h2_text:
            report("G9", HARD, p, None, f"keyword '{kw}' not in any H2")
        if not (META_LEN[0] <= len(meta) <= META_LEN[1]):
            report("G9", HARD, p, None, f"meta description {len(meta)} chars (need {META_LEN[0]}-{META_LEN[1]})")
        if not (TITLE_LEN[0] <= len(title) <= TITLE_LEN[1]):
            report("G9", HARD, p, None, f"title {len(title)} chars (need {TITLE_LEN[0]}-{TITLE_LEN[1]})")
        words = len(re.findall(r"\b\w+\b", vis))
        if words < BLOG_MIN_WORDS:
            report("G9", HARD, p, None, f"{words} words (need >= {BLOG_MIN_WORDS})")
        if not re.search(r'href=["\'](?:/|\.|https?://(?:www\.)?targetdigital\.com\.au)', body, re.I) \
           and "](/" not in body and "](." not in body:
            report("G9", HARD, p, None, "no internal link")
        if ".gov.au" not in body:
            report("G9", HARD, p, None, "no .gov.au authority link")
        if CANONICAL_CALENDLY not in body and "calendly.com" not in body and "book" not in vis.lower():
            report("G9", HARD, p, None, "no CTA (Calendly/booking link)")
        if re.search(r"\b(19|20)\d{2}\b", title):
            report("G9", HARD, p, None, "year in title (must be evergreen)")


def _front_matter(txt):
    if not txt.strip().startswith("---"):
        return None
    end = txt.find("\n---", 3)
    if end < 0:
        return None
    fm = {}
    for line in txt[3:end].splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def g10_placeholder(z):
    for p in z["A"] + z["email"] + z["blog"] + z["clients"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        vis = visible_text(txt) if p.endswith(".html") else txt
        for marker in PLACEHOLDER_TEXT:
            if marker in vis.lower():
                report("G10", HARD, p, line_of(txt, marker), f"placeholder text in copy: '{marker}'")
        if p.endswith(".html"):
            for url in attr_urls(txt):
                for bad in PLACEHOLDER_URLS:
                    if bad in url.lower():
                        report("G10", HARD, p, line_of(txt, url), f"placeholder URL in link/src: '{url}'")
        # unresolved merge tokens in RENDERED site pages (not email templates)
        if p in z["A"]:
            m = re.search(r"\{\{[^}]+\}\}", vis)
            if m:
                report("G10", HARD, p, line_of(txt, m.group(0)),
                       f"unresolved merge token on live page: '{m.group(0)}'")


def g11_tokens(z):
    for p in z["email"]:
        if not p.endswith(".html") or ".n8n." in p:
            continue
        txt = read(p)
        if txt is None:
            continue
        for m in re.finditer(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", txt):
            if m.group(1) not in TOKEN_ALLOWLIST:
                report("G11", HARD, p, line_of(txt, m.group(0)),
                       f"unknown merge token '{{{{{m.group(1)}}}}}' (typo?)")


def g12_pricing_calendly(z):
    for p in z["A"]:
        txt = read(p)
        if txt is None:
            continue
        for link in re.findall(r"calendly\.com/[^\s\"'<>]+", txt):
            link = link.rstrip("/")
            if link in RETIRED_CALENDLY:
                report("G12", HARD, p, line_of(txt, link), f"retired Calendly link: {link}")
            elif not link.startswith(CANONICAL_CALENDLY):
                report("G12", HARD, p, line_of(txt, link), f"non-canonical Calendly link: {link}")
        for bad in RETIRED_PRICES:
            if bad in txt:
                report("G12", HARD, p, line_of(txt, bad), f"retired price still present: {bad}")
    for p in PRICING_PAGES:
        txt = read(p)
        if txt is None:
            continue
        for money in set(re.findall(r"\$[0-9][0-9,]+", txt)):
            if money not in CANONICAL_PRICES and money not in KNOWN_NON_PRICE:
                report("G12", WARN, p, line_of(txt, money),
                       f"unrecognized money figure '{money}' — pricing drift?")


def g13_site_integrity():
    script = os.path.join(ROOT, "check_site.py")
    if not os.path.exists(script):
        report("G13", WARN, "check_site.py", None, "check_site.py not found — site integrity unchecked")
        return
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, script], cwd=ROOT, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        msg = tail[-1] if tail else f"exit {r.returncode}"
        report("G13", HARD, "check_site.py", None, f"site integrity FAILED: {msg}")


def g14_au_english(z):
    word_re = {w: re.compile(r"\b" + re.escape(w) + r"\b", re.I) for w in US_SPELLINGS}
    for p in z["A"] + z["email"] + z["blog"] + z["clients"]:
        if not (p.endswith(".html") or p.endswith(".md")):
            continue
        txt = read(p)
        if txt is None:
            continue
        vis = visible_text(txt) if p.endswith(".html") else txt
        hits = [w for w, rx in word_re.items() if rx.search(vis)]
        if hits:
            report("G14", WARN, p, None, "US spelling(s): " + ", ".join(sorted(set(hits))))


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
def main():
    strict = "--strict" in sys.argv
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    tracked = git_tracked()
    z = classify(tracked)

    reg = load_yaml("clients/registry.yml")
    clients = []
    for c in reg.get("clients", []):
        idents = [c.get("slug", ""), c.get("domain", "")]
        idents += [a.strip() for a in (c.get("aliases") or "").split(",") if a.strip()]
        clients.append({"slug": c.get("slug", ""), "identifiers": [i for i in idents if i]})

    g1_secrets(tracked)
    g2_client_isolation(z, clients)
    g3_pii(z)
    g4_evidence(z, clients)
    g5_retired_proof(z)
    g6_fabrication_smell(z)
    g7_regulated(z)
    g8_email_compliance(z)
    g9_blog_format(z)
    g10_placeholder(z)
    g11_tokens(z)
    g12_pricing_calendly(z)
    g13_site_integrity()
    g14_au_english(z)

    hard = [f for f in _findings if f[1] == HARD]
    warn = [f for f in _findings if f[1] == WARN]

    def show(f):
        _, level, path, line, msg = f
        loc = f"{path}:{line}" if line else path
        tag = "✖ HARD" if level == HARD else "▲ warn"
        print(f"  {tag}  [{f[0]}] {loc}\n          {msg}")

    print("\n── Target Digital gatekeeper ─────────────────────────────")
    print(f"   {len(tracked)} tracked files · {len(clients)} client(s) registered\n")

    if hard:
        print(f"HARD-STOP FAILURES ({len(hard)}):")
        for f in hard:
            show(f)
        print()
    if warn:
        print(f"WARNINGS ({len(warn)}):")
        for f in warn:
            show(f)
        print()

    blocked = hard or (strict and warn)
    if not _findings:
        print("✔ all gates clear.\n")
    elif not blocked:
        print(f"✔ no hard-stops. {len(warn)} warning(s) for review — not blocking.\n")

    if blocked:
        print(f"✖ BLOCKED — {len(hard)} hard-stop(s)"
              + (f" + {len(warn)} warning(s) under --strict" if strict and warn else "")
              + ". Fix before shipping. No deferring.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
