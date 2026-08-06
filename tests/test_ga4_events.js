// Runtime test: load each real page in jsdom, stub gtag, drive the real CTAs,
// assert the right GA4 events come out. Static syntax checks don't prove this.
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const REPO = path.join(__dirname, '..');
// Discovered, like add_ga4_events.py and check_site.py — a new page is covered
// by this test the moment it lands, without anyone remembering to list it.
const PAGES = fs.readdirSync(REPO).filter(f => f.endsWith('.html')).sort();

let pass = 0, fail = 0;
function ok(name, cond, detail) {
  if (cond) { pass++; console.log(`  PASS  ${name}`); }
  else { fail++; console.log(`  FAIL  ${name}${detail ? ' — ' + detail : ''}`); }
}

function load(page) {
  const html = fs.readFileSync(path.join(REPO, page), 'utf8');
  // jsdom doesn't fetch the CDN <script src> tags, so the page's own inline
  // block dies on `Lenis is not defined` / Three.js. That is deliberate here:
  // it reproduces the ad-blocker / CDN-outage visitor, and the tracker must
  // keep reporting anyway. VirtualConsole swallows those expected errors.
  const vc = new VirtualConsole();
  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    url: 'https://targetdigital.com.au/' + page,
    virtualConsole: vc,
  });
  const w = dom.window;
  const events = [];
  w.gtag = (kind, name, params) => { if (kind === 'event') events.push({ name, params }); };
  // page scripts may post to webhooks / the call proxy — never let a test hit the network
  w.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({}), text: () => Promise.resolve('') });
  return { w, d: w.document, events };
}

function click(el) { el.dispatchEvent(new el.ownerDocument.defaultView.MouseEvent('click', { bubbles: true, cancelable: true })); }
function submit(form) { form.dispatchEvent(new form.ownerDocument.defaultView.Event('submit', { bubbles: true, cancelable: true })); }
function last(events) { return events[events.length - 1]; }

console.log('\n1. Every page: tracker present and a Calendly click converts');
for (const page of PAGES) {
  const { d, events } = load(page);
  const cal = d.querySelector('a[href*="calendly.com"]');
  ok(`${page} has a Calendly CTA`, !!cal);
  if (!cal) continue;
  click(cal);
  const e = last(events);
  ok(`${page} → generate_lead`, e && e.name === 'generate_lead', e ? JSON.stringify(e) : 'no event fired');
  ok(`${page} page_id correct`, e && e.params.page_id === page.replace('.html', ''),
     e ? e.params.page_id : '');
}

console.log('\n2. index.html: cta_location distinguishes identical "Book a Call" labels');
{
  const { d, events } = load('index.html');
  const cals = [...d.querySelectorAll('a[href*="calendly.com"]')];
  cals.forEach(click);
  const places = events.filter(e => e.name === 'generate_lead').map(e => e.params.cta_location);
  ok('all Calendly clicks converted', events.filter(e => e.name === 'generate_lead').length === cals.length,
     `${events.length} events for ${cals.length} links`);
  ok('nav vs hero vs pricing vs final are distinct', new Set(places).size >= 4, places.join(','));
  console.log('        locations: ' + places.join(', '));
}

console.log('\n3. index.html: internal CTAs, nav links, FAQ');
{
  const { d, events } = load('index.html');

  const internal = d.querySelector('a.btn-outline[href="/funnel.html"]');
  click(internal);
  ok('internal CTA → cta_click', last(events).name === 'cta_click', JSON.stringify(last(events)));
  ok('cta_click carries link_url', last(events).params.link_url === '/funnel.html');

  const navLink = [...d.querySelectorAll('nav a')].find(a => !a.href.includes('calendly'));
  click(navLink);
  ok('nav link → nav_click', last(events).name === 'nav_click', JSON.stringify(last(events)));

  // The CDN scripts (Lenis/GSAP/Three) are NOT fetched by jsdom, so the page's
  // accordion handler never binds here — which is exactly the ad-blocker /
  // CDN-outage case a real visitor can hit. FAQ clicks must still be counted.
  const before = events.length;
  const faq = d.querySelector('button.faq-q');
  click(faq);
  ok('FAQ click tracked even with the accordion script dead',
     events.length === before + 1 && last(events).name === 'faq_click',
     JSON.stringify(last(events)));
  ok('faq_click reports the expanded state', last(events).params.expanded !== undefined,
     JSON.stringify(last(events).params));
  click(faq);
  ok('every FAQ click counted (not just opens)', events.length === before + 2,
     `${events.length - before} events`);

  const anchor = d.querySelector('a[href^="#"]');
  const n = events.length;
  if (anchor) click(anchor);
  ok('in-page #anchor → no event', events.length === n);
}

console.log('\n3b. index.html FAQ with a working accordion (the real-browser case)');
{
  // jsdom can't run the Three.js hero (no WebGL), and that abort takes the rest
  // of the inline block — including the accordion — with it. So pull the page's
  // OWN accordion source out of index.html and run just that. Real code, not a
  // re-typed imitation.
  const src = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
  const accordion = src.match(/\/\/ ── FAQ ACCORDION ──[\s\S]*?\n\}\);/);
  ok('found the accordion source in index.html', !!accordion);

  const { w, d, events } = load('index.html');
  w.eval(accordion[0]);

  const faq = d.querySelector('button.faq-q');
  click(faq);
  // Prove the accordion actually ran — otherwise 'expanded' would read 'closed'
  // forever and the assertions below would pass against a dead page.
  ok('accordion really toggles', faq.parentElement.classList.contains('open'),
     `classes: ${faq.parentElement.className}`);
  const open = last(events);
  ok('open click → faq_click expanded=open',
     open.name === 'faq_click' && open.params.expanded === 'open', JSON.stringify(open.params));
  click(faq);
  const close = last(events);
  ok('close click → faq_click expanded=closed',
     close.name === 'faq_click' && close.params.expanded === 'closed', JSON.stringify(close.params));
}

console.log('\n4. Contact links');
{
  const { d, events } = load('medical.html');
  click(d.querySelector('a[href^="tel:"]'));
  ok('tel: → contact_click/phone', last(events).name === 'contact_click' && last(events).params.method === 'phone',
     JSON.stringify(last(events)));
}
{
  const { d, events } = load('terms.html');
  click(d.querySelector('a[href^="mailto:"]'));
  ok('mailto: → contact_click/email', last(events).name === 'contact_click' && last(events).params.method === 'email',
     JSON.stringify(last(events)));
}

console.log('\n5. Demo forms');
const DEMOS = {
  'leadgendemo.html': ['leadForm', 'lead_qualification'],
  'outboundcalldemo.html': ['callForm', 'outbound_call'],
  'invoiceautomationdemo.html': ['invForm', 'invoice_automation'],
  'documentautomationdemo.html': ['docForm', 'document_automation'],
};
for (const [page, [formId, demoName]] of Object.entries(DEMOS)) {
  const { d, events } = load(page);
  submit(d.getElementById(formId));
  const e = events.find(x => x.name === 'demo_start');
  ok(`${page} submit → demo_start/${demoName}`, e && e.params.demo_name === demoName,
     e ? JSON.stringify(e) : 'no demo_start');
}

console.log('\n6. Calculator: run = engagement, email gate = conversion');
{
  const { d, events } = load('lead-pipeline-calculator.html');
  submit(d.getElementById('ltc-form'));
  ok('ltc-form → calculator_submit', events.some(e => e.name === 'calculator_submit'),
     JSON.stringify(events));
  submit(d.getElementById('ltc-unlock'));
  const g = events.find(e => e.name === 'generate_lead');
  ok('ltc-unlock → generate_lead/calculator_email_gate',
     g && g.params.method === 'calculator_email_gate', g ? JSON.stringify(g) : 'no generate_lead');
}

console.log('\n7. Non-destinations stay silent');
{
  const { d, events } = load('outboundcalldemo.html');
  const again = d.querySelector('a.btn-ghost[href="#"]');
  ok('"Run it again" link exists', !!again);
  if (again) { click(again); ok('href="#" reload link → no event', events.length === 0, JSON.stringify(events)); }
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
