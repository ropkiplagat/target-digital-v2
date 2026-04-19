import sys, re
sys.stdout.reconfigure(encoding='utf-8')

pages = [
    ('funnel.html',     {'prices':['2,000','4,000'], 'extra': lambda h: 'hero-canvas' in h and 'hero-overlay' in h and 'ScrollTrigger' in h and 'funnel-hero.png' in h}),
    ('outbound.html',   {'prices':['4,000','6,000'], 'extra': lambda h: 'hero-canvas' in h and 'hero-overlay' in h and 'ScrollTrigger' in h and 'outbound-hero.png' in h}),
    ('reputation.html', {'prices':['1,500','3,000'], 'extra': lambda h: 'hero-canvas' in h and 'hero-overlay' in h and 'ScrollTrigger' in h and 'reputation-hero.png' in h}),
    ('creative.html',   {'prices':['1,500','3,000'], 'extra': lambda h: 'hero-canvas' in h and 'hero-overlay' in h and 'ScrollTrigger' in h and 'creative-hero.png' in h}),
]

all_pass = True
for filename, opts in pages:
    with open(filename, encoding='utf-8') as f:
        html = f.read()
    text = re.sub(r'<[^>]+>', ' ', html)
    words = len(text.split())
    results = []
    def check(label, passed, detail=''):
        results.append(('PASS' if passed else 'FAIL', label, detail))

    m = re.search(r'<title>([^<]+)</title>', html, re.I)
    title = m.group(1).strip() if m else ''
    check('Meta title <=60', len(title)<=60, f'{len(title)}: "{title}"')

    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I|re.S)
    desc = m.group(1).strip() if m else ''
    check('Meta desc <=155', len(desc)<=155, f'{len(desc)} chars')

    h1 = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.I|re.S)
    check('H1 present', bool(h1))
    check('Brand --navy', '--navy:#06091a' in html)
    check('Calendly link', 'calendly.com' in html)
    check('No bare # CTAs', len(re.findall(r'href=["\'](#)["\']', html))==0)
    bad = [r'>[Ss]ubmit<', r'>Click [Hh]ere<', r'>Learn [Mm]ore<']
    check('No bad CTA text', not any(re.search(p,html) for p in bad))
    check('IntersectionObserver', 'IntersectionObserver' in html)
    check('1500ms failsafe', '1500' in html)
    check('Joanne.JFIF', 'Joanne.JFIF' in html or 'joanne.jfif' in html.lower())
    check('Brijesh.PNG', 'Brijesh.PNG' in html or 'brijesh.png' in html.lower())
    check('Viewport meta', 'viewport' in html)
    check('Sticky CTA', 'sticky-cta' in html)
    check('Word count >600', words>600, f'{words}')
    check('Contact email', 'rop@targetdigital.com.au' in html)
    check('No Lorem ipsum', 'lorem ipsum' not in html.lower())
    check('Footer 2026', '2026' in html)
    for p in opts['prices']:
        check(f'Price {p}', p in html)
    check('Hero animation present', opts['extra'](html))
    check('Mobile hide @media', '@media(max-width:640px)' in html)

    passes = sum(1 for r in results if r[0]=='PASS')
    total = len(results)
    file_ok = passes==total
    if not file_ok: all_pass=False
    print(f'{"="*50}')
    print(f'PM: {filename}')
    print(f'{"="*50}')
    for s,l,d in results:
        print(f'[{s}] {l}' + (f' — {d}' if d else ''))
    print(f'SCORE: {passes}/{total} — {"ALL PASS" if file_ok else "FAIL"}\n')

print('='*50)
print(f'OVERALL: {"ALL 4 PASS ✓" if all_pass else "FAILURES — DO NOT PUSH"}')
print('='*50)
