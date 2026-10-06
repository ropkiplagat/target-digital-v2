#!/usr/bin/env python3
"""Footer link block to every sitemap page, on every shipping page. Idempotent.
Reads the page list from sitemap.xml so a new page links itself on re-run.
Run: py add_footer_links.py"""
import re
from pathlib import Path
ROOT = Path(__file__).parent
LABELS = {"": "Home", "funnel.html": "AI Lead Gen Engine", "outbound.html": "AI Outbound Call Engine", "ai-lead-generation-brisbane.html": "Brisbane",
          "demos.html": "Demos", "lead-pipeline-calculator.html": "ROI Calculator",
          "lead-magnet-funnel.html": "Lead Leak Audit", "lead-magnet-outbound.html": "Cold Outbound Playbook",
          "leadgendemo.html": "Lead Qualification Demo", "outboundcalldemo.html": "AI Call Demo",
          "blog.html": "Blog", "faq.html": "FAQ", "blog/speed-to-lead-australia.html": "Speed to Lead Guide", "blog/ai-outbound-calling-compliance-australia.html": "AI Calling Compliance", "blog/do-not-call-register-calling-leads.html": "Do Not Call Register", "blog/facebook-lead-form-consent-to-call.html": "Facebook Lead Form Consent", "blog/follow-up-facebook-lead-ads-fast.html": "Follow Up Facebook Leads", "blog/ai-caller-disclosure-australia.html": "AI Caller Disclosure", "blog/ai-live-transfer-explained.html": "AI Live Transfer", "blog/spam-act-ai-sms-follow-up.html": "Spam Act and AI Texts", "blog/gohighlevel-alternative-australia.html": "GoHighLevel Alternative", "blog/dental-enquiry-follow-up-ai.html": "Dental Enquiry Follow-Up", "blog/ai-lead-follow-up-for-tradies.html": "AI Follow-Up for Tradies", "blog/does-ai-lead-generation-work.html": "Does AI Lead Generation Work",
          "blog/ai-receptionist-cost-australia.html": "AI Receptionist Cost", "blog/lead-generation-pricing-australia.html": "Lead Generation Pricing",
          "privacy-policy.html": "Privacy Policy", "terms.html": "Terms"}
S, E = "<!-- footer-links:start -->", "<!-- footer-links:end -->"
locs = re.findall(r"<loc>https://targetdigital.com.au/([^<]*)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
links = "".join(f'<a href="/{p}" style="color:#7986b0;text-decoration:none;margin:0 .6rem;white-space:nowrap">{LABELS.get(p, p)}</a>' for p in locs)
block = f'{S}<div style="text-align:center;line-height:2;margin:1rem 0;font-size:.85rem">{links}</div>{E}\n'
for page in sorted(ROOT.glob("*.html")):
    if page.name in ("404.html", "medical.html", "invoiceautomationdemo.html", "documentautomationdemo.html"):
        continue
    t = page.read_text(encoding="utf-8")
    t = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", "", t, flags=re.S)
    t = t.replace("</footer>", block + "</footer>", 1)
    page.write_text(t, encoding="utf-8", newline="")
    print("ok", page.name)
