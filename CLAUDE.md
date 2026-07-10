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

## Pages (12 ship)
| File | Purpose |
|------|---------|
| `index.html` | Homepage — both products side by side, proof, 3-tier pricing |
| `funnel.html` | Lead Gen Engine product page |
| `outbound.html` | Outbound Call Engine product page |
| `lead-magnet-funnel.html` | Lead Gen lead magnet (AI Lead Leak Audit) |
| `lead-magnet-outbound.html` | Outbound lead magnet (Cold Outbound Playbook) |
| `lead-pipeline-calculator.html` | Lead-to-Call ROI calculator (webhook not yet wired) |
| `demos.html` | Hub linking the 3 live interactive demos |
| `leadgendemo.html` | Live demo — AI lead qualification (fully working) |
| `documentautomationdemo.html` | Live demo — document automation pipeline (fully working) |
| `outboundcalldemo.html` | Demo — AI outbound call flow; **simulation** until `CALL_PROXY_URL` set |
| `privacy-policy.html` / `terms.html` | Legal placeholders |

`brand/competitor-intelligence.md` and `competitor-hero-research.md` are strategy docs, not pages.
`call-proxy/` is a deployable Node service (NOT served by Pages) — it places real Vapi calls for the outbound demo; see `call-proxy/README.md`.

## Pricing (single source of truth — keep all pages consistent)
One-time **setup** + monthly retainer:
- **Starter** — $2,000 setup + $500/mo — one engine
- **Growth** — $4,500 setup + $1,500/mo — both engines
- **Scale** — $7,500 setup + $3,000/mo — both engines, max volume

## Critical rules (don't break these)
1. **Every CTA must resolve** — Calendly link or a real in-page anchor. No bare `<button>` that does nothing.
2. **Nav is uniform across all pages:** Home / Lead Gen Engine / Outbound Call Engine / Demos / ROI Calculator / Book a Call. Never link to removed pages (reputation/creative are gone). `update_nav.py` is the canonical source for this nav.
3. **Asset references must match on-disk casing exactly** (`Joanne.jfif`, `Brijesh.png` — not `.JFIF`/`.PNG`).
4. **Proof must match the brand doc:** Joan R. = Lead Gen result; Brijesh Singh = Outbound result.
5. **Pricing must be identical** across index / funnel / outbound.
6. Voice-stack tool names (Twilio + AI voice agent) are **placeholders** — confirm real vendors before claiming them publicly.

## Known fragile points
- **`update_nav.py`** regenerates nav across pages. Its CSS injection targets the **last** `</style>` only — re-running on a page with two `<style>` blocks used to double-inject (fixed). Prefer editing nav directly over re-running on already-updated pages (re-run duplicates the mobile menu).
- **Skill mirroring:** the repo has the skills library duplicated into ~24 AI-tool dirs (`.claude/`, `.codebuddy/`, `.qwen/`…). There were ~3,168 uncommitted deletions of these mirrors — intentional cleanup, still pending a decision. Canonical copy lives in `.agents/skills/`.
- Hero video `target-digital-hero.mp4` on the homepage is a placeholder (`pending Kling generation`).

## How to test it works (run before shipping)
```
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py check.py    # the gatekeeper — run after EVERY ticket
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py check_site.py   # site boundary test (also wrapped by check.py G13)
```
**`check.py` is the gatekeeper — run it after every ticket. Any hard-stop → work stops, no deferring.** It exits non-zero on any HARD gate and runs a fixed set (denylist/citation-precise gates hard-stop; judgment-based checks warn). Gates: G1 secrets · G2 client isolation · G4 evidence-backed claims (blank source = fail) · G5 retired proof · G7 regulated claims (NDIS/gov/guarantee) · G8 email Spam-Act (unsub+sender) · G9 blog format · G10 placeholders · G11 merge-token integrity · G12 Calendly canon + retired price · G13 wraps `check_site.py` · plus WARN gates G3 PII, G6 fabrication smell, G12w pricing drift, G14 AU English. Config lives in the CONFIG block at the top of `check.py`. `--strict` treats warnings as failures too. Client work is namespaced under `clients/<slug>/` with a per-client `evidence.yml` (see `clients/README.md`) — every metric/testimonial in client copy must trace to a sourced entry there.

`check_site.py` is the site boundary test. It fails on: broken internal links, dangling `#anchors`, missing/case-mismatched assets, dead CTA buttons, and duplicated nav/mobile-menu/CSS. Exit 0 = clear to ship.

## Recent major changes
0. **2026-06-19 — Linked the 3 live demos + built the call proxy.** Added `demos.html` hub; made nav uniform across all 12 pages (added Demos + ROI Calculator everywhere) and updated `update_nav.py` to match. Built `call-proxy/` (Node/Express) so `outboundcalldemo.html` can place real Vapi calls without exposing the key — deploy it + set `CALL_PROXY_URL` to go live; until then the demo stays in safe simulation.
1. **2026-06-16 — Restructured to the two-product GTM model.** Removed reputation/creative pages + their lead magnets; rewrote homepage (two engines, Joan/Brijesh proof, 3-tier setup+monthly pricing, all CTAs → Calendly); rewrote `outbound.html` from an email outbound engine into the AI Outbound Call Engine (form→SMS→AI call→qualify→hot transfer/warm booking/no-answer retry); aligned funnel pricing; nav reduced to Home / Lead Gen Engine / Outbound Call Engine + Book a Call. (commit `2b47aa8`)
2. **2026-06-16 — Centralized nav + mobile menu** across pages via `update_nav.py` (commit `5bdf769`); fixed a double-CSS-injection bug.
3. **2026-06-18 — Added `check_site.py` boundary test;** it caught 9 image case-mismatch bugs (`Joanne.JFIF`/`Brijesh.PNG` → lowercase) that would have 404'd on Linux hosting.
