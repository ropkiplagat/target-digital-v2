import sys
sys.stdout.reconfigure(encoding='utf-8')

FLOAT_CSS = """    <style>
      .hero-img-wrap{position:relative;max-width:520px;margin:2.5rem auto 0}
      .hero-img-wrap img{width:100%;border-radius:16px;border:1px solid rgba(255,255,255,0.1);box-shadow:0 24px 80px rgba(0,0,0,0.5)}
      .float-tag{position:absolute;background:rgba(6,9,26,0.88);border:1px solid rgba(255,255,255,0.18);color:#fff;padding:7px 16px;border-radius:100px;font-size:12px;font-weight:700;white-space:nowrap;backdrop-filter:blur(10px);animation:ftFloat 3s ease-in-out infinite;animation-delay:var(--delay,0s)}
      .float-tag.gold{border-color:rgba(240,192,64,0.45);color:var(--gold)}
      .float-tag.blue{border-color:rgba(37,99,235,0.45);color:#60a5fa}
      .float-tag.cyan{border-color:rgba(0,191,255,0.45);color:var(--cyan)}
      @keyframes ftFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
      @media(max-width:640px){.hero-img-wrap{display:none}}
    </style>"""

pages = {
    'funnel.html': {
        'start_marker': '    <!-- HERO IMAGE -->',
        'end_marker': '    </script>',
        'new_hero': FLOAT_CSS + """
    <div class="hero-img-wrap">
      <img src="funnel-hero.png" alt="AI Lead Funnel">
      <span class="float-tag gold" style="--delay:0s;top:10%;left:-5%">AI Qualified</span>
      <span class="float-tag" style="--delay:0.7s;top:10%;right:-5%">24/7</span>
      <span class="float-tag" style="--delay:1.2s;top:45%;right:-10%">Meeting Booked</span>
      <span class="float-tag gold" style="--delay:1.8s;bottom:20%;left:-8%">Zero Manual Work</span>
    </div>""",
        'prefix': '    <!-- HERO IMAGE -->\n',
    },
    'outbound.html': {
        'start_marker': '    <!-- OUTBOUND CHAIN ANIMATION -->',
        'end_marker': '    </script>',
        'new_hero': FLOAT_CSS + """
    <div class="hero-img-wrap">
      <img src="outbound-hero.png" alt="Automated Outbound Engine">
      <span class="float-tag" style="--delay:0s;top:10%;left:-5%">PhantomBuster</span>
      <span class="float-tag cyan" style="--delay:0.7s;top:10%;right:-5%">Apollo</span>
      <span class="float-tag" style="--delay:1.2s;top:45%;right:-10%">Instantly</span>
      <span class="float-tag cyan" style="--delay:0.4s;bottom:20%;right:-8%">Railway</span>
      <span class="float-tag gold" style="--delay:1.8s;bottom:20%;left:-8%">3-8 Calls/Week</span>
    </div>""",
        'prefix': '    <!-- OUTBOUND CHAIN ANIMATION -->\n',
    },
    'reputation.html': {
        'start_marker': '    <!-- STAR BUILDER ANIMATION -->',
        'end_marker': '    </script>',
        'new_hero': FLOAT_CSS + """
    <div class="hero-img-wrap">
      <img src="reputation-hero.png" alt="Reputation Builder">
      <span class="float-tag gold" style="--delay:0s;top:10%;left:-5%">4.9 Stars</span>
      <span class="float-tag" style="--delay:0.7s;top:10%;right:-5%">90 Days</span>
      <span class="float-tag gold" style="--delay:1.2s;top:45%;right:-10%">24/7 Monitor</span>
      <span class="float-tag" style="--delay:0.4s;bottom:20%;right:-8%">AI Response</span>
      <span class="float-tag cyan" style="--delay:1.8s;bottom:20%;left:-8%">3x Reviews</span>
    </div>""",
        'prefix': '    <!-- STAR BUILDER ANIMATION -->\n',
    },
    'creative.html': {
        'start_marker': '    <!-- AD GRID ANIMATION -->',
        'end_marker': '    </script>',
        'new_hero': FLOAT_CSS + """
    <div class="hero-img-wrap">
      <img src="creative-hero.png" alt="The Creative Goldmine">
      <span class="float-tag gold" style="--delay:0s;top:10%;left:-5%">100+ Variations</span>
      <span class="float-tag" style="--delay:0.7s;top:10%;right:-5%">CPL Down 47%</span>
      <span class="float-tag blue" style="--delay:1.2s;top:45%;right:-10%">Kling AI</span>
      <span class="float-tag" style="--delay:0.4s;bottom:20%;right:-8%">Zero Shoots</span>
      <span class="float-tag gold" style="--delay:1.8s;bottom:20%;left:-8%">Week 3 Winners</span>
    </div>""",
        'prefix': '    <!-- AD GRID ANIMATION -->\n',
    },
}

for filename, cfg in pages.items():
    with open(filename, encoding='utf-8') as f:
        html = f.read()

    start_idx = html.find(cfg['start_marker'])
    if start_idx == -1:
        print(f'ERROR: start marker not found in {filename}')
        continue

    # Find the end marker AFTER the start marker
    end_search_from = start_idx + len(cfg['start_marker'])
    end_idx = html.find(cfg['end_marker'], end_search_from)
    if end_idx == -1:
        print(f'ERROR: end marker not found in {filename}')
        continue

    # Include the end marker itself
    end_idx += len(cfg['end_marker'])

    old_block = html[start_idx:end_idx]
    new_block = cfg['prefix'] + cfg['new_hero']

    html_new = html[:start_idx] + new_block + html[end_idx:]

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_new)

    print(f'DONE: {filename} ({len(old_block)} chars -> {len(new_block)} chars)')

print('All pages updated.')
