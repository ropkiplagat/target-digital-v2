import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

files = [
    ('lead-magnet-funnel.html',      {'prices': ['1,500','2,000','4,000'], 'accent': 'gold/blue', 'keyword': 'funnel|lead|audit'}),
    ('lead-magnet-outbound.html',    {'prices': ['4,000','6,000'], 'accent': 'cyan', 'keyword': 'outbound|playbook'}),
    ('lead-magnet-reputation.html',  {'prices': ['1,500','3,000'], 'accent': 'amber', 'keyword': 'review|reputation|star'}),
    ('lead-magnet-creative.html',    {'prices': ['1,500','3,000'], 'accent': 'purple', 'keyword': 'creative|fatigue|andromeda'}),
]

all_pass = True

for filename, opts in files:
    with open(filename, encoding='utf-8') as f:
        html = f.read()
    text = re.sub(r'<[^>]+>', ' ', html)
    words = len(text.split())
    results = []

    def check(label, passed, detail=''):
        results.append(('PASS' if passed else 'FAIL', label, detail))

    m = re.search(r'<title>([^<]+)</title>', html, re.I)
    title = m.group(1).strip() if m else ''
    check('Meta title <=60 chars', len(title) <= 60, f'{len(title)}: "{title}"')

    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I|re.S)
    desc = m.group(1).strip() if m else ''
    check('Meta desc <=155 chars', len(desc) <= 155, f'{len(desc)} chars')

    h1 = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.I|re.S)
    h1_text = re.sub(r'<[^>]+>','',h1[0]).strip() if h1 else ''
    check('H1 present', bool(h1), h1_text[:60] if h1_text else 'MISSING')

    check('Brand --navy', '--navy:#06091a' in html)
    check('Calendly link', 'calendly.com' in html)

    hash_links = re.findall(r'href=["\'](#)["\']', html)
    check('No bare # CTAs', len(hash_links)==0, f'{len(hash_links)} found')

    bad_patterns = [r'>[Ss]ubmit<', r'>Click [Hh]ere<', r'>Learn [Mm]ore<', r'>Read [Mm]ore<']
    found_bad = [p for p in bad_patterns if re.search(p, html)]
    check('No bad CTA text', len(found_bad)==0, str(found_bad))

    check('IntersectionObserver', 'IntersectionObserver' in html)
    check('1500ms failsafe', '1500' in html)
    check('Joanne.JFIF', 'Joanne.JFIF' in html or 'joanne.jfif' in html.lower())
    check('Brijesh.PNG', 'Brijesh.PNG' in html or 'brijesh.png' in html.lower())
    check('Viewport meta', 'viewport' in html)
    check('Sticky CTA', 'sticky' in html.lower() and ('sticky-cta' in html))
    check('Word count >600', words > 600, f'{words} words')
    check('Contact email', 'rop@targetdigital.com.au' in html)
    check('No Lorem ipsum', 'lorem ipsum' not in html.lower())
    check('Footer 2026', '2026' in html)
    check('No fabricated names', not any(f in html.lower() for f in ['john smith','jane doe','john doe']))

    passes = sum(1 for r in results if r[0]=='PASS')
    total = len(results)
    file_pass = passes == total
    if not file_pass:
        all_pass = False

    print('='*55)
    print(f'PM CHECK: {filename}')
    print('='*55)
    for status, label, detail in results:
        mark = '[PASS]' if status=='PASS' else '[FAIL]'
        print(f'{mark} {label}' + (f' — {detail}' if detail else ''))
    print(f'SCORE: {passes}/{total} — {"ALL PASS" if file_pass else "FAILURES FOUND"}')
    print()

print('='*55)
print(f'OVERALL: {"ALL 4 FILES PASS" if all_pass else "FAILURES — DO NOT PUSH"}')
print('='*55)
