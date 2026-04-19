import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('creative.html', encoding='utf-8') as f:
    html = f.read()
text = re.sub(r'<[^>]+>', ' ', html)
words = len(text.split())

results = []
def check(label, passed, detail=''):
    status = 'PASS' if passed else 'FAIL'
    results.append((status, label, detail))

# 1. Meta title <= 60 chars
m = re.search(r'<title>([^<]+)</title>', html, re.I)
title = m.group(1).strip() if m else ''
check('Meta title <= 60 chars', len(title) <= 60, f'{len(title)} chars: "{title}"')

# 2. Meta description <= 155 chars
m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I | re.S)
desc = m.group(1).strip() if m else ''
check('Meta desc <= 155 chars', len(desc) <= 155, f'{len(desc)} chars')

# 3. H1 present
h1 = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.I | re.S)
check('H1 present', len(h1) > 0, h1[0][:60] if h1 else 'MISSING')

# 4. Brand color --navy
check('Brand color --navy', '--navy:#06091a' in html or '--navy: #06091a' in html)

# 5. Calendly link
check('Calendly link present', 'calendly.com' in html)

# 6. No hash-only CTAs
hash_links = re.findall(r'href=["\'](#)["\']', html)
check('No bare # CTAs', len(hash_links) == 0, f'{len(hash_links)} found')

# 7. No bad CTA text
bad = ['click here', 'learn more', 'submit', 'read more']
found_bad = [b for b in bad if b in html.lower()]
check('No bad CTA text', len(found_bad) == 0, str(found_bad))

# 8. IntersectionObserver present
check('IntersectionObserver present', 'IntersectionObserver' in html)

# 9. 1500ms failsafe
check('1500ms failsafe', '1500' in html)

# 10. Joanne.JFIF present
check('Joanne.JFIF present', 'Joanne.JFIF' in html or 'joanne.jfif' in html.lower())

# 11. Brijesh.PNG present
check('Brijesh.PNG present', 'Brijesh.PNG' in html or 'brijesh.png' in html.lower())

# 12. Viewport meta
check('Viewport meta', 'viewport' in html)

# 13. Sticky CTA
check('Sticky CTA present', 'sticky' in html.lower() and 'cta' in html.lower())

# 14. Word count > 600
check('Word count > 600', words > 600, f'{words} words')

# 15. Contact email
check('Contact email present', 'rop@targetdigital.com.au' in html)

# 16. No Lorem ipsum
check('No Lorem ipsum', 'lorem ipsum' not in html.lower())

# 17. Price $1,500 present
check('Price $1,500 present', '1,500' in html or '1500' in html)

# 18. Price $3,000 present
check('Price $3,000 present', '3,000' in html or '3000' in html)

# 19. /month present
check('/month present', '/month' in html)

# 20. Footer year 2026
check('Footer 2026', '2026' in html)

# 21. No fabricated names (check for common fake names)
fake = ['john smith', 'jane doe', 'john doe']
found_fake = [f for f in fake if f in html.lower()]
check('No fabricated names', len(found_fake) == 0, str(found_fake))

# 22. Purple accent color
check('Purple accent --purple', '--purple' in html or '#a855f7' in html)

# 23. Facebook Andromeda mentioned
check('Andromeda angle present', 'andromeda' in html.lower())

print('=' * 55)
print('AGENT 3 — PM CHECKLIST: creative.html')
print('=' * 55)
passes = sum(1 for r in results if r[0] == 'PASS')
for status, label, detail in results:
    mark = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'{mark} {label}' + (f' — {detail}' if detail else ''))
print('=' * 55)
print(f'SCORE: {passes}/{len(results)}')
if passes == len(results):
    print('STATUS: ALL PASS — APPROVED FOR PREVIEW')
else:
    fails = [r for r in results if r[0] == 'FAIL']
    print(f'STATUS: {len(fails)} FAILURE(S) — FIX BEFORE PREVIEW')
