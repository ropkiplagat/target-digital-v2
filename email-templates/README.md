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

## DEMO setup (current)
- **Delivery:** Gmail node in n8n.
- **How:** paste the contents of each file into the matching Gmail node's **Body (HTML)** field.
  No Google Drive step — these live in git, not Drive.
- **Trigger:** the calculator POSTs to the n8n webhook (`/webhook/lead-magnet-calculator`),
  which starts the sequence.

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
