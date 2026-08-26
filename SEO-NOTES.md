# SEO notes — targetdigital.com.au

Static HTML site. Not WordPress. No SEO plugin, no plugin score.
Read this before rebuilding, regenerating, or bulk-editing any `<head>`.

**14 HTML pages ship. 13 are in `sitemap.xml`** — `medical.html` is deliberately
excluded (unlisted, direct-link only via `utm_campaign=aria_article`). "All pages"
below means all 14; "sitemap pages" means the 13.

## SEO — current state (verified 26 Aug 2026)

Present and correct. Preserve on any rebuild:

- Self-referencing canonical on all **14** pages (index's points at `/`, not `/index.html`)
- GA4 gtag G-DVJVMK97NH on all **14** pages
- robots.txt and sitemap.xml — correct, do not regenerate
- medical.html deliberately excluded from sitemap.xml
- `check_site.py` checks 6 + 7 gate both: a new page must be in the sitemap or
  explicitly in `SITEMAP_EXCLUDE`, and must carry a canonical

## SEO — target state (NOT YET LIVE as of 26 Aug 2026)

These do not exist yet. If you are rebuilding, CREATE them — do not assume
they are present and skip them:

- Open Graph + twitter:card on all 14 pages (currently 0/14)
- JSON-LD @graph (Organization / Service / FAQPage) on funnel.html and
  outbound.html (currently bare Organization on 6 pages — index, funnel,
  outbound, both lead magnets, calculator — and absent on the other 8)
- `<meta name="robots" content="noindex,follow">` on medical.html
  (currently NO robots meta on any page — medical.html is indexable, opposite
  to intent. Sitemap exclusion is not de-indexing.)
- preconnect to fonts.gstatic.com with crossorigin
  (fonts.googleapis.com is already preconnected — that is the stylesheet
  host, not the font host, so the round-trip saving is not being had)

## Known drift

- `funnel.html` JSON-LD `description` still says **"The AI Funnel Machine"** —
  a retired product name. Current name is **AI Lead Gen Engine**. Fix when the
  @graph rewrite happens.

Update this file when each ships. Move the line up, change the date.

## Pre-flight answers (settled from disk, 27 Aug 2026)

**G1 — rollback path: YES.** `C:\Users\cc\targetdigital-v2` is a git repo,
remote `github.com/ropkiplagat/target-digital-v2`, push to `main` deploys.
Rollback = `git revert <sha> && git push`. Two gates run before shipping:
`check.py` (content) and `check_site.py` (boundary).

**G2 — the 14 HTML files are HAND-MAINTAINED SOURCE. Edit them in place.**
Four independent confirmations:
- no `_site/`, no `_layouts/`, no `_includes/` — nothing generates
- no Liquid tags (`{{` / `{%`) in any page
- no YAML front matter — every page opens `<!DOCTYPE html>`, so Jekyll copies
  it through byte-for-byte
- `_config.yml` is `exclude:`-only — a publish filter, not a build config

Jekyll *is* present (GitHub Pages runs it by default) but does nothing to these
files. That is exactly why `sitemap.xml` is hand-maintained.

⚠️ **Do not use a rendered-text grep to test this.** Searching source for
`STOP LOSING 70%` returns only `brand/competitor-intelligence.md` and MISSES
`funnel.html`, which renders that headline at line 346 — inline markup splits
the string (`STOP <span class="red">LOSING 70%</span> OF YOUR...`). A grep that
matches the rendered page but not the source will tell you the HTML is
generated when it isn't.

## Batch-1 hazard: do NOT add `defer` to the three.js / Lenis tags

`index.html`, `funnel.html`, `outbound.html` load three.js + Lenis via
`<script src>` in `<head>`, then call them from an **inline** block further down
(`index.html:611` `new Lenis(...)`, `:618` `new THREE.WebGLRenderer(...)` — 21
references in total; funnel/outbound have 2 each). Inline scripts are never
deferred, so `defer` makes the inline block run *before* the library loads →
`ReferenceError` → hero WebGL and smooth scroll die.

Worse, that same block binds the FAQ accordion (see the `faq_click` note in
CLAUDE.md), so the breakage is not visually obvious — the page looks static
rather than broken. "Re-render and confirm it works" will not catch it.
Move the `<script src>` tags to just before `</body>`, or wrap the inline init
in `DOMContentLoaded`. Check the console explicitly.

## Batch-1 hazard: there is no valid `og:image` asset yet

Largest images on disk are `funnel-hero.png` / `outbound-hero.png` /
`creative-hero.png` / `reputation-hero.png` at **1456×822**. Usable (1.77 vs
OG's ideal 1.91 — minor letterboxing). **`target-digital-logo.png` is 182×88 and
is NOT a usable fallback** — it is under Facebook's 200px minimum and will be
rejected, producing the grey box. Either omit `og:image` from Batch 1 or point
pages at a `*-hero.png`. Purpose-built 1200×630 art is a separate task.

**Sequencing:** all 14 pages already have a `meta description`. If a batch
rewrites those, `og:description` must be rewritten in the same pass or it
desyncs silently.
