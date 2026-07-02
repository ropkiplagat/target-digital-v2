#!/usr/bin/env python3
"""
Auto-update navigation for Target Digital site.
Run: python update_nav.py
"""

import os
import re
from pathlib import Path

# === CONFIG ===
REPO_ROOT = Path(__file__).parent
HTML_FILES = [
    "index.html", "funnel.html", "outbound.html",
    "lead-magnet-funnel.html", "lead-magnet-outbound.html",
    "lead-pipeline-calculator.html", "demos.html",
    "leadgendemo.html", "documentautomationdemo.html", "outboundcalldemo.html",
    "privacy-policy.html", "terms.html",
]

CALENDLY = "https://calendly.com/ropkiplagat/intro-to-sales-target-digital"

NEW_NAV = '''<nav>
  <div class="nav-logo">🎯 Target<span>Digital</span></div>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/funnel.html">Lead Gen Engine</a>
    <a href="/outbound.html">Outbound Call Engine</a>
    <a href="/demos.html">Demos</a>
    <a href="/lead-pipeline-calculator.html">ROI Calculator</a>
  </div>
  <a href="https://calendly.com/ropkiplagat/intro-to-sales-target-digital" target="_blank" rel="noopener" class="nav-cta" style="text-decoration:none">Book a Call</a>
  <div class="hamburger" onclick="toggleMobileNav()">
    <span></span><span></span><span></span>
  </div>
</nav>
<div class="mobile-nav" id="mobileNav">
  <a href="/">Home</a>
  <a href="/funnel.html">Lead Gen Engine</a>
  <a href="/outbound.html">Outbound Call Engine</a>
  <a href="/demos.html">Demos</a>
  <a href="/lead-pipeline-calculator.html">ROI Calculator</a>
  <a href="https://calendly.com/ropkiplagat/intro-to-sales-target-digital" target="_blank" rel="noopener" class="mobile-cta">Book a Call</a>
</div>

<script>
function toggleMobileNav() {
  const nav = document.getElementById('mobileNav');
  nav.classList.toggle('open');
}
</script>'''

NEW_CSS = '''
/* Nav links */
.nav-links {
  display: flex;
  gap: 2rem;
  align-items: center;
}
.nav-links a {
  color: var(--muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.2s;
}
.nav-links a:hover {
  color: #fff;
}
.hamburger {
  display: none;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 4px;
}
.hamburger span {
  display: block;
  width: 25px;
  height: 3px;
  background: #fff;
  border-radius: 2px;
}
.mobile-nav {
  display: none;
  position: fixed;
  top: 70px;
  left: 0;
  right: 0;
  background: var(--navy);
  padding: 2rem;
  flex-direction: column;
  gap: 1.5rem;
  border-bottom: 1px solid rgba(37,99,235,0.15);
  z-index: 99;
}
.mobile-nav.open {
  display: flex;
}
.mobile-nav a {
  color: var(--text);
  text-decoration: none;
  font-size: 1.1rem;
}
.mobile-cta {
  background: var(--blue);
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  color: #fff !important;
  font-weight: 600;
}
@media (max-width: 768px) {
  .nav-links { display: none; }
  .hamburger { display: flex; }
}'''

def update_file(filepath):
    """Update a single HTML file with new nav and CSS."""
    if not filepath.exists():
        print(f"⚠️ Skipping: {filepath.name} (not found)")
        return False

    content = filepath.read_text(encoding='utf-8')

    # Find and replace nav
    nav_pattern = r'<nav[^>]*>.*?</nav>'
    if re.search(nav_pattern, content, re.DOTALL):
        content = re.sub(nav_pattern, NEW_NAV, content, flags=re.DOTALL)
    else:
        # Insert after <body>
        content = content.replace('<body>', f'<body>\n{NEW_NAV}')

    # Add CSS before the LAST </style> only (files may have multiple <style> blocks)
    if '</style>' in content and '.nav-links' not in content:
        head, sep, tail = content.rpartition('</style>')
        content = f'{head}{NEW_CSS}\n{sep}{tail}'

    filepath.write_text(content, encoding='utf-8')
    print(f"✅ Updated: {filepath.name}")
    return True

# === MAIN ===
if __name__ == "__main__":
    print(f"📍 Repo root: {REPO_ROOT}")
    updated = 0
    for filename in HTML_FILES:
        filepath = REPO_ROOT / filename
        if update_file(filepath):
            updated += 1

    print(f"\n🎉 Done! {updated} files updated.")
    print("📦 Run: git add . && git commit -m 'Update navigation' && git push")
