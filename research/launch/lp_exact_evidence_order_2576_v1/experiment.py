from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
OUT = Path(__file__).resolve().parent / "artifacts"
VIEWPORTS = [(1440,900),(1024,768),(768,1024),(390,844),(360,740),(320,568)]

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def swap_media(html: str) -> str:
    hero = re.search(r'<figure class="hero-media wrap".*?</figure>', html, re.S)
    failed = re.search(r'<figure aria-labelledby="realtime-label".*?</figure>', html, re.S)
    if not hero or not failed:
        raise RuntimeError("canonical figure boundaries not found")
    h, f = hero.group(0), failed.group(0)
    if html.count(h) != 1 or html.count(f) != 1:
        raise RuntimeError("non-unique figure boundary")
    return html.replace(h, f, 1).replace(f, h, 1)

def metrics(page):
    return page.evaluate("""() => {
      const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {top:r.top+scrollY,bottom:r.bottom+scrollY}};
      const text=t=>[...document.querySelectorAll('.media-state')].find(e=>e.textContent.includes(t));
      const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
      const media=[...document.querySelectorAll('video,iframe')].map(e=>({src:e.currentSrc||e.querySelector('source')?.src||'',loaded:e.readyState===4}));
      return {cta:rect(document.querySelector('.hero-aside .button')),verified:rect(text('VERIFIED RUN')),failed:rect(text('FAILED RUN')),height:document.documentElement.scrollHeight,dupIds:[...new Set(ids.filter((x,i)=>ids.indexOf(x)!==i))],scripts:document.scripts.length,skip:!!document.querySelector('a.skip[href="#main"]')&&!!document.querySelector('#main'),mainTabindex:document.querySelector('#main')?.getAttribute('tabindex'),reducedMotion:!![...document.styleSheets].length,media};
    }""")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    html=(SITE/"index.html").read_text()
    candidate=swap_media(html)
    (OUT/"baseline.html").write_text(html)
    (OUT/"candidate.html").write_text(candidate)
    result={"source":{"bytes":len(html.encode()),"sha256":hashlib.sha256(html.encode()).hexdigest()},"media":[],"viewports":[]}
    for rel in ("media/golden-desktop-live-02-2x-h264.mp4","media/map01-astra-live-01-2x-h264.mp4"):
        p=SITE/rel
        if not p.is_file(): raise RuntimeError("missing canonical asset: "+rel)
        result["media"].append({"path":rel,"bytes":p.stat().st_size,"sha256":sha256(p)})
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        for variant in ("baseline","candidate"):
            doc=(OUT/(variant+".html")).resolve().as_uri()
            for w,h in VIEWPORTS:
                page=browser.new_page(viewport={"width":w,"height":h})
                page.goto(doc,wait_until="load")
                m=metrics(page)
                for k in ("cta","verified","failed"):
                    if m[k]: m[k]["aboveFold"]=m[k]["top"]<h and m[k]["bottom"]>0
                result["viewports"].append({"variant":variant,"width":w,"height":h,**m})
                page.close()
        browser.close()
    (OUT/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__": main()
