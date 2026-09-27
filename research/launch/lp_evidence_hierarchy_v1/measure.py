from playwright.sync_api import sync_playwright
from pathlib import Path
import json

variants = ['baseline', 'candidate_reorder', 'candidate_swapmedia']
viewports = [('desktop', 1440, 900), ('laptop', 1024, 768), ('mobile', 390, 844)]
out = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for variant in variants:
        filename = 'baseline.html' if variant == 'baseline' else variant + '.html'
        html = Path(filename).read_text()
        for name, width, height in viewports:
            page = browser.new_page(viewport={'width': width, 'height': height})
            page.set_content(html, wait_until='domcontentloaded')
            measured = page.evaluate('''() => {
              function rect(e) { if (!e) return null; const r=e.getBoundingClientRect(); return {top:r.top+scrollY,bottom:r.bottom+scrollY}; }
              function byText(sel,text) { return [...document.querySelectorAll(sel)].find(e=>e.textContent.includes(text)); }
              const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
              return {
                heroCTA: rect(document.querySelector('.hero-aside .button')),
                failed: rect(byText('.media-state','FAILED RUN')),
                verified: rect(byText('.media-state','VERIFIED RUN')),
                pageHeight: document.documentElement.scrollHeight,
                dupIds: [...new Set(ids.filter((x,i)=>ids.indexOf(x)!==i))],
                scripts: document.scripts.length,
                hasSkip: !!document.querySelector('a.skip[href="#main"]') && !!document.querySelector('#main')
              };
            }''')
            for key in ('heroCTA', 'failed', 'verified'):
                if measured[key]:
                    measured[key]['aboveFold'] = measured[key]['top'] < height and measured[key]['bottom'] > 0
            out.append({'variant': variant, 'viewport': {'name': name, 'width': width, 'height': height}, **measured})
            page.close()
    browser.close()

Path('metrics.json').write_text(json.dumps(out, indent=2) + '\n')
