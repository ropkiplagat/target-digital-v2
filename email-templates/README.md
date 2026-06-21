# Email templates — Lead-to-Call calculator nurture

5-email sequence sent to leads who opt in on `lead-pipeline-calculator.html`.
These files are the **source of truth** (versioned in git) — not Google Drive.

| File | Subject line | Purpose |
|------|--------------|---------|
| `email1.html` | Here's your Lead-to-Call ROI report | Deliver the result, set up the sequence |
| `email2.html` | Why 5 minutes changes everything | Speed-to-lead principle |
| `email3.html` | The #1 mistake killing your pipeline | Agitate: leads go cold |
| `email4.html` | How Brijesh booked 3–8 calls a week — no ads, no BDR | Proof (Outbound Call Engine) |
| `email5.html` | Want us to build this for you? | Final CTA → growth audit + pricing |

## Merge tokens
Replace these in n8n before sending (a Set / Edit-Fields node, or the Gmail node's expression field):

| Token | Source |
|-------|--------|
| `{{first_name}}` | lead's first name (optional; if you only collect email, drop it or default to "there") |
| `{{addMo}}` | additional revenue / month from the calculator payload (`addMo`) |
| `{{addYr}}` | additional revenue / year from the calculator payload (`addYr`) |
| `{{unsubscribe_url}}` | unsubscribe link — **must be functional** (AU Spam Act 2003) |

> Note: the calculator currently captures **email + consent only**, not first name.
> Until first name is collected, either remove `{{first_name}}` greetings or default them to "there".

## Two versions of each template
- `emailN.html` — **clean source of truth.** Uses readable tokens (`{{first_name}}` etc.).
  Edit copy here.
- `emailN.n8n.html` — **paste-ready for n8n.** Tokens pre-swapped to live n8n expressions
  so personalization works with no extra nodes. Regenerate these whenever you edit the
  clean source. Bakes in: real webhook node name, `$`-formatted numbers, a mailto unsubscribe.

Token → expression mapping used in the `.n8n.html` files (webhook node assumed to be
named `Webhook - Calculator Capture` — rename if yours differs):

| Token | n8n expression |
|-------|----------------|
| `{{first_name}}` | `{{ $('Webhook - Calculator Capture').item.json.body.first_name }}` |
| `{{addMo}}` | `{{ '$' + Math.round($('Webhook - Calculator Capture').item.json.body.addMo).toLocaleString('en-US') }}` |
| `{{addYr}}` | `{{ '$' + Math.round($('Webhook - Calculator Capture').item.json.body.addYr).toLocaleString('en-US') }}` |
| `{{unsubscribe_url}}` | `mailto:unsubscribe@targetdigital.com.au?subject=Unsubscribe` (demo) — swap for a hosted one-click page at volume |

## DEMO setup (current)
- **Delivery:** Gmail node in n8n.
- **How:** paste the contents of each **`.n8n.html`** file into the matching Gmail node's
  **Body (HTML)** field. No Google Drive step — these live in git, not Drive.
- **Trigger:** the calculator POSTs to the n8n webhook (`/webhook/lead-magnet-calculator`),
  which starts the sequence.
- **Gmail node config:** Resource = **Message**, Operation = **Send** (NOT Draft);
  To = `{{ $('Webhook - Calculator Capture').item.json.body.email }}`.
- **Test:** see "How to test personalization" — use n8n's live expression preview, then
  one real send with the Wait nodes temporarily shortened.

## PRODUCTION (when there are paying clients — to build later)
Replace the Gmail node with a real email-sending API. Gmail is fine to prove the flow but
will not scale or stay deliverable for client volume.

- **ESP:** Resend / Postmark / Amazon SES / Brevo (via n8n HTTP Request node).
- **Per-client authenticated sending domain** (SPF / DKIM / DMARC) so mail comes from the
  client's own domain and lands in the inbox.
- **Built-in:** open/click/bounce tracking, one-click unsubscribe, suppression lists.
- **Multi-tenant:** parameterize sender domain + branding per client; deploy this template
  set per client from git.

## Brand facts baked in (keep consistent with the site)
- Proof: **Brijesh Singh — Robotics For Sure, Brisbane** (Outbound result); Joan R. — Imani
  Mental Health (Lead Gen result). Don't invent metrics beyond what the site states.
- Pricing: Starter $2,000+$500/mo · Growth $4,500+$1,500/mo · Scale $7,500+$3,000/mo.
- CTA: `https://calendly.com/targetdigital/growth-audit`.
- Colours: cyan `#00BFFF`, ink `#0b0f14`.
