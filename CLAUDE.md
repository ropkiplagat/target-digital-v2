# Target Digital v2 — CLAUDE.md

> Read this first, every session. If something here is wrong, fix it in the same commit as the code change — a doc that drifts is worse than no doc.

## What this is
Static marketing site for **Target Digital AI** — a GTM agency selling **two AI products** to direct customers (individual clients now, agencies later):

1. **AI Lead Gen Engine** (`funnel.html`) — Discover → AI qualify → book sales calls.
2. **AI Outbound Call Engine** (`outbound.html`) — Form submit → instant SMS → AI outbound voice call → AI qualifies → **HOT** live-transfer to sales / **WARM** appointment booking / **NO ANSWER** 3-day retry.

Both are pitched as working for any industry. Conversion is a Calendly booking — there is **no backend and no forms** on this site.

## Where it runs
- **Source:** `C:\Users\cc\targetdigital-v2` (git, branch `main`).
- **Hosting:** **GitHub Pages** — repo `github.com/ropkiplagat/target-digital-v2`, custom domain **targetdigital.com.au** (via `CNAME`). Pushing to `main` deploys. ⚠️ GitHub Pages serves from Linux/case-sensitive storage: asset filenames must match references exactly or they 404.
- **No build step.** Open the `.html` files directly; all CSS/JS is inline or via CDN (Three.js, GSAP, Lenis, Google Fonts).
- **Booking:** all CTAs point to `https://calendly.com/ropkiplagat/intro-to-sales-target-digital`.

## Pages (14 ship)
| File | Purpose |
|------|---------|
| `index.html` | Homepage — both products side by side, proof, 3-tier pricing |
| `funnel.html` | Lead Gen Engine product page |
| `outbound.html` | Outbound Call Engine product page |
| `lead-magnet-funnel.html` | Lead Gen lead magnet (AI Lead Leak Audit) |
| `lead-magnet-outbound.html` | Outbound lead magnet (Cold Outbound Playbook) |
| `lead-pipeline-calculator.html` | Lead-to-Call ROI calculator — email gate POSTs to the live n8n webhook (capture working) |
| `demos.html` | Hub linking the 4 live interactive demos |
| `leadgendemo.html` | Live demo — AI lead qualification (fully working) |
| `documentautomationdemo.html` | Live demo — document automation (lease generate → e-sign → sync) |
| `invoiceautomationdemo.html` | Live demo — supplier invoice → OCR extract → GST split → draft bill in Xero |
| `outboundcalldemo.html` | Live demo — AI outbound call flow; places **real Vapi calls** (proxy deployed) |
| `medical.html` | Sales asset for the live Aria voice-reception demo (unlisted — promoted via UTM, `utm_campaign=aria_article`) |
| `privacy-policy.html` / `terms.html` | Legal placeholders |

`brand/competitor-intelligence.md` and `competitor-hero-research.md` are strategy docs, not pages.
`call-proxy/` is a deployable Node service (NOT served by Pages) — it places real Vapi calls for the outbound demo; see `call-proxy/README.md`.

## Pricing (single source of truth — keep all pages consistent)
One-time **setup** + monthly retainer:
- **Starter** — $2,000 setup + $500/mo — one engine
- **Growth** — $4,500 setup + $1,500/mo — both engines
- **Scale** — $7,500 setup + $3,000/mo — both engines, max volume

## Analytics (GA4 — `G-DVJVMK97NH`)
Two layers, both auto-installed:
1. **Base gtag snippet** in `<head>` of every page — page views only.
2. **Event tracker** — one delegated click/submit listener injected before `</body>` by **`add_ga4_events.py`**. Never hand-write `onclick="gtag(...)"` on an element: `update_nav.py` rewrites the nav and would wipe it, and per-element handlers drift. Add a button, and it's tracked automatically.

| Event | Fires on | Key params |
|---|---|---|
| `generate_lead` | **The conversion** — any Calendly click, or the calculator email gate | `method` (`calendly` / `calculator_email_gate`), `cta_location` |
| `cta_click` | Any other internal CTA link | `link_url`, `cta_location` |
| `nav_click` | Header / mobile-menu links | `link_url` |
| `contact_click` | `tel:` and `mailto:` links | `method` (`phone` / `email`) |
| `demo_start` | A live demo form was submitted | `demo_name` |
| `calculator_submit` | The ROI calculator was run | — |
| `faq_click` | An FAQ question was clicked | `expanded` (`open` / `closed`) |

All events also carry `cta_text`, `cta_location`, `page_id`. **`cta_location`** is the nearest landmark (`nav`, `mobile_nav`, `footer`, or the enclosing `<section id>` — `hero`, `pricing`, `cta-final`…), which is the only way to tell the seven identical "Book a Call" CTAs apart.

**GA4 property = `properties/516327460`** ("Target Digital"). Two console-side steps were required:
- ✅ **Custom dimensions registered** — all six (`cta_text`, `cta_location`, `page_id`, `method`, `demo_name`, `expanded`) confirmed present via the Admin API on 2026-08-09.
- ❓ **Mark `generate_lead` as a Key Event** (Admin → Events) — *still unconfirmed.* This cannot be verified from here: the Data API only reports key-event status for events that have data, and `generate_lead` has never fired. Check it in the GA4 UI. Do **not** fire a test conversion to find out — that pollutes the conversion record permanently.

⚠️ **No custom event has EVER been recorded** (as of 2026-08-09). This is a traffic problem, not a tracking bug: the tracker is verified live on the deployed site, but the property has only ~3 page views in a rolling 4 days, so nothing has been clicked. Don't "fix" the tracker on this evidence — the first real diagnosis is that nobody is visiting.

`faq_click` deliberately fires on *every* click and reports state in a param, rather than only on opens. The accordion's `open` class is set by a script sharing a block with the Lenis/Three.js CDN init — if that CDN is blocked (ad blocker) or the WebGL hero throws, the accordion never binds. Gating the event on that class would kill FAQ tracking silently; this way an all-`closed` report is itself the signal that the accordion broke for real visitors.

## Search / indexing
- **`sitemap.xml` is hand-maintained** — there is no `jekyll-sitemap` plugin, so this file is the only thing Google reads. It lists **13 of the 14 pages**. `robots.txt` points at it.
- **`medical.html` is deliberately excluded** from the sitemap (unlisted demo, direct-link only via `utm_campaign=aria_article`). It is *also* deliberately **not** named in `robots.txt` — that file is public, so a `Disallow` line would advertise the page it's hiding, and wouldn't prevent indexing anyway.
- **Every page needs `rel="canonical"`.** The homepage's points at `/` (not `/index.html`) — it answers to both URLs, and without a canonical Google can split the domain's strongest page in two.
- `check_site.py` checks 6 + 7 enforce all of the above: a new page must be **either in the sitemap or explicitly in `SITEMAP_EXCLUDE`**, so adding a page forces a yes/no instead of silently dropping out of search. That's how the sitemap sat at 5 URLs while the site grew to 14.

## Critical rules (don't break these)
1. **Every CTA must resolve** — Calendly link or a real in-page anchor. No bare `<button>` that does nothing.
2. **Nav is uniform across all pages:** Home / Lead Gen Engine / Outbound Call Engine / Demos / ROI Calculator / Book a Call. Never link to removed pages (reputation/creative are gone). `update_nav.py` is the canonical source for this nav.
3. **Asset references must match on-disk casing exactly** (`Joanne.jfif`, `Brijesh.png` — not `.JFIF`/`.PNG`).
4. **Proof must be VERIFIED — real results only.** Joan R. = Lead Gen result (verified). **Wilson W. / Imani Car Sales, Brisbane = verified** (invoice processing 93% faster, live in 4 days). **Brijesh Singh / Robotics For Sure = NOT VERIFIED — fabricated numbers (3–8 calls/week etc.). Banned everywhere; enforced by `check.py` G5 (RETIRED_CLAIMS).** Outbound Call Engine proof is currently PENDING a verified client — do not attribute outbound-call results to Brijesh or anyone unverified.
5. **Pricing must be identical** across index / funnel / outbound.
6. Voice-stack tool names (Twilio + AI voice agent) are **placeholders** — confirm real vendors before claiming them publicly.

## Known fragile points
- **`update_nav.py`** regenerates nav across pages. Its CSS injection targets the **last** `</style>` only — re-running on a page with two `<style>` blocks used to double-inject (fixed). Prefer editing nav directly over re-running on already-updated pages (re-run duplicates the mobile menu).
- ~~**Skill mirroring**~~ — **resolved.** The ~24 duplicated AI-tool dirs (`.claude/`, `.codebuddy/`, `.qwen/`…) are gone and the ~3,168 deletions are committed; the working tree is clean. `.agents/skills/` is the single canonical copy. Don't re-add mirrors.
- Hero video `target-digital-hero.mp4` on the homepage is a placeholder (`pending Kling generation`).

## How to test it works (run before shipping)
```
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py check.py    # the gatekeeper — run after EVERY ticket
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py check_site.py   # site boundary test (also wrapped by check.py G13)
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py add_ga4_events.py --check   # GA4 tracker present + current on every page
cd tests && npm install && npm test        # GA4 events actually fire (jsdom, 65 assertions)
```
`tests/` is dev-only and never served; `node_modules/` is gitignored. Run `py add_ga4_events.py` (no flag) to install or refresh the tracker after adding a page — it's idempotent, so re-running replaces the block rather than stacking a second copy.
**`check.py` is the gatekeeper — run it after every ticket. Any hard-stop → work stops, no deferring.** It exits non-zero on any HARD gate and runs a fixed set (denylist/citation-precise gates hard-stop; judgment-based checks warn). Gates: G1 secrets · G2 client isolation · G4 evidence-backed claims (blank source = fail) · G5 retired proof · G7 regulated claims (NDIS/gov/guarantee) · G8 email Spam-Act (unsub+sender) · G9 blog format · G10 placeholders · G11 merge-token integrity · G12 Calendly canon + retired price · G13 wraps `check_site.py` · plus WARN gates G3 PII (allowlists: `SAFE_EMAILS`, `SAFE_PHONES` — deliberately-public contact details, so the demo line isn't a permanent warning), G6 fabrication smell, G12w pricing drift, G14 AU English (stem-matched, so `optimization`/`analyzes` are caught, not just the bare verb). Config lives in the CONFIG block at the top of `check.py`. `--strict` treats warnings as failures too. Client work is namespaced under `clients/<slug>/` with a per-client `evidence.yml` (see `clients/README.md`) — every metric/testimonial in client copy must trace to a sourced entry there.

`check_site.py` is the site boundary test. It fails on: broken internal links, dangling `#anchors`, missing/case-mismatched assets, dead CTA buttons, and duplicated nav/mobile-menu/CSS. Exit 0 = clear to ship.

## Recent major changes
0. **2026-08-07 — Search Console prep: sitemap rebuilt, canonical fixed, drift gated.** `sitemap.xml` was still the 5 URLs of the June restructure — 8 live pages (all 4 demos, the hub, calculator, both legal pages) were never offered to Google. Now 13 URLs; `medical.html` stays out on purpose. `index.html` had no `rel="canonical"` (the only page missing one). Added `check_site.py` checks 6 + 7 so neither can rot again. GSC verification itself is console-side — see the Search / indexing section.
1. **2026-08-06 — GA4 event tracking on every button.** Added `add_ga4_events.py` (delegated listener, injected site-wide, idempotent, page list auto-discovered) and `tests/test_ga4_events.js` (jsdom, 65 assertions driving the real CTAs). The test caught a real coupling bug: `faq_open` was gated on a CSS class set by a script that dies when the Lenis/Three.js CDN is blocked — now `faq_click` fires unconditionally and reports state in a param. Remaining manual step: mark `generate_lead` as a Key Event + register the custom dimensions in the GA4 UI.
2. **2026-06-19 — Linked the 3 live demos + built the call proxy.** Added `demos.html` hub; made nav uniform across all 12 pages (added Demos + ROI Calculator everywhere) and updated `update_nav.py` to match. Built `call-proxy/` (Node/Express) so `outboundcalldemo.html` can place real Vapi calls without exposing the key — deploy it + set `CALL_PROXY_URL` to go live; until then the demo stays in safe simulation.
3. **2026-06-16 — Restructured to the two-product GTM model.** Removed reputation/creative pages + their lead magnets; rewrote homepage (two engines, Joan/Brijesh proof, 3-tier setup+monthly pricing, all CTAs → Calendly); rewrote `outbound.html` from an email outbound engine into the AI Outbound Call Engine (form→SMS→AI call→qualify→hot transfer/warm booking/no-answer retry); aligned funnel pricing; nav reduced to Home / Lead Gen Engine / Outbound Call Engine + Book a Call. (commit `2b47aa8`)
4. **2026-06-16 — Centralized nav + mobile menu** across pages via `update_nav.py` (commit `5bdf769`); fixed a double-CSS-injection bug.
5. **2026-06-18 — Added `check_site.py` boundary test;** it caught 9 image case-mismatch bugs (`Joanne.JFIF`/`Brijesh.PNG` → lowercase) that would have 404'd on Linux hosting.
