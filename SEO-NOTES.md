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
