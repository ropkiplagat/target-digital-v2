import sys, re
sys.stdout.reconfigure(encoding='utf-8')

HERO_CSS = """<style>
.hero-bg{position:absolute;inset:0;z-index:1;overflow:hidden;pointer-events:none}
.hero-bg img{width:100%;height:100%;object-fit:cover;object-position:center;opacity:0.45}
#hero::after{content:'';position:absolute;bottom:0;left:0;width:100%;height:200px;background:linear-gradient(to bottom,transparent,#010D1F);z-index:2;pointer-events:none}
.float-tag{position:absolute;z-index:4;background:rgba(6,9,26,0.88);border:1px solid rgba(255,255,255,0.18);color:#fff;padding:7px 16px;border-radius:100px;font-size:12px;font-weight:700;white-space:nowrap;backdrop-filter:blur(10px);animation:ftFloat 3s ease-in-out infinite;animation-delay:var(--delay,0s)}
.float-tag.gold{border-color:rgba(240,192,64,0.45);color:var(--gold)}
.float-tag.blue{border-color:rgba(37,99,235,0.45);color:#60a5fa}
.float-tag.cyan{border-color:rgba(0,191,255,0.45);color:var(--cyan)}
@keyframes ftFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@media(max-width:640px){.hero-bg img{opacity:0.25}}
</style>"""

pages = {
    'funnel.html': {
        'img_src': 'funnel-hero.png',
        'img_alt': 'AI Lead Funnel',
        'tags': [
            '<span class="float-tag gold" style="--delay:0s;top:15%;left:3%">AI Qualified</span>',
            '<span class="float-tag" style="--delay:0.7s;top:15%;right:3%">24/7</span>',
            '<span class="float-tag" style="--delay:1.2s;top:45%;right:3%">Meeting Booked</span>',
            '<span class="float-tag gold" style="--delay:1.8s;bottom:25%;left:3%">Zero Manual Work</span>',
        ],
    },
    'outbound.html': {
        'img_src': 'outbound-hero.png',
        'img_alt': 'Automated Outbound Engine',
        'tags': [
            '<span class="float-tag" style="--delay:0s;top:15%;left:3%">PhantomBuster</span>',
            '<span class="float-tag cyan" style="--delay:0.7s;top:15%;right:3%">Apollo</span>',
            '<span class="float-tag" style="--delay:1.2s;top:45%;right:3%">Instantly</span>',
            '<span class="float-tag cyan" style="--delay:0.4s;bottom:25%;right:3%">Railway</span>',
            '<span class="float-tag gold" style="--delay:1.8s;bottom:25%;left:3%">3-8 Calls/Week</span>',
        ],
    },
    'reputation.html': {
        'img_src': 'reputation-hero.png',
        'img_alt': 'Reputation Builder',
        'tags': [
            '<span class="float-tag gold" style="--delay:0s;top:15%;left:3%">4.9 Stars</span>',
            '<span class="float-tag" style="--delay:0.7s;top:15%;right:3%">90 Days</span>',
            '<span class="float-tag gold" style="--delay:1.2s;top:45%;right:3%">24/7 Monitor</span>',
            '<span class="float-tag" style="--delay:0.4s;bottom:25%;right:3%">AI Response</span>',
            '<span class="float-tag cyan" style="--delay:1.8s;bottom:25%;left:3%">3x Reviews</span>',
        ],
    },
    'creative.html': {
        'img_src': 'creative-hero.png',
        'img_alt': 'The Creative Goldmine',
        'tags': [
            '<span class="float-tag gold" style="--delay:0s;top:15%;left:3%">100+ Variations</span>',
            '<span class="float-tag" style="--delay:0.7s;top:15%;right:3%">CPL Down 47%</span>',
            '<span class="float-tag blue" style="--delay:1.2s;top:45%;right:3%">Kling AI</span>',
            '<span class="float-tag" style="--delay:0.4s;bottom:25%;right:8%">Zero Shoots</span>',
            '<span class="float-tag gold" style="--delay:1.8s;bottom:25%;left:8%">Week 3 Winners</span>',
        ],
    },
}

for filename, cfg in pages.items():
    with open(filename, encoding='utf-8') as f:
        html = f.read()

    # 1. Remove old hero-img-wrap block (comment + style + div)
    html = re.sub(
        r'\n\n    <!--[^>]+-->\n    <style>.*?</style>\n    <div class="hero-img-wrap">.*?</div>',
        '',
        html,
        flags=re.DOTALL
    )

    # 2. Update inner container div: add position:relative;z-index:3
    html = html.replace(
        '  <div style="max-width:860px;margin:0 auto">\n',
        '  <div style="max-width:860px;margin:0 auto;position:relative;z-index:3">\n',
        1
    )

    # 3. Inject hero-bg + float tags right after <section id="hero">
    tags_html = '\n  '.join(cfg['tags'])
    bg_block = (
        f'  <div class="hero-bg">'
        f'<img src="{cfg["img_src"]}" alt="{cfg["img_alt"]}"></div>\n'
        f'  {tags_html}\n'
    )
    html = html.replace('<section id="hero">\n', f'<section id="hero">\n{bg_block}', 1)

    # 4. Inject new CSS block before </head>
    if '.hero-bg{' not in html:
        html = html.replace('</head>', HERO_CSS + '\n</head>', 1)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'DONE: {filename}')

print('All 4 pages upgraded.')
