"""Real Chromium/X11 staged-addressing comparison; no model or task-state reads."""
import argparse, base64, gzip, hashlib, importlib.metadata, io, json, os
import platform, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import ImageGrab
from playwright.sync_api import sync_playwright
from Xlib import X, display
from Xlib.ext import xtest
from fixture import CASES, html
from resolver import ARMS, regions, resolve

HERE=Path(__file__).resolve().parent

def digest(data): return hashlib.sha256(data).hexdigest()
def write(path,obj):
    with path.open('x',encoding='utf-8') as f:
        json.dump(obj,f,sort_keys=True);f.flush();os.fsync(f.fileno())
def append(path,obj):
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(obj,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

def native(cdp):
    started=time.perf_counter_ns();raw=cdp.send('Accessibility.getFullAXTree');items=[]
    for n in raw['nodes']:
        if n.get('ignored') or n.get('role',{}).get('value')!='button': continue
        model=cdp.send('DOM.getBoxModel',{'backendNodeId':n['backendDOMNodeId']})['model']
        b=model['border'];x,y=min(b[::2]),min(b[1::2])
        items.append({'name':n.get('name',{}).get('value',''),
            'box':[x,y,max(b[::2])-x,max(b[1::2])-y],
            'backend_node':n['backendDOMNodeId']})
    return items,raw,time.perf_counter_ns()-started

def run(out,layout):
    out.mkdir(parents=True,exist_ok=False)
    plan=json.loads((HERE/'plan.json').read_text())
    for n,h in plan['sources'].items():
        if digest((HERE/n).read_bytes())!=h: raise ValueError('source mismatch '+n)
    write(out/'plan.json',plan)
    env={'python':sys.version,'platform':platform.platform(),'cpuinfo':Path('/proc/cpuinfo').read_text(),
         'affinity':sorted(os.sched_getaffinity(0)), 'versions':{},'layout':layout}
    for name in ('numpy','Pillow','opencv-python','playwright','python-xlib'):
        try:env['versions'][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:env['versions'][name]='unavailable'
    xvfb=wm=None;d=None
    # Isolated local display; no TCP listener. Never changes the user's desktop.
    auth=out/'empty.Xauthority';auth.write_bytes(b'');os.environ['XAUTHORITY']=str(auth)
    chosen=None
    for i in range(110,150):
        if not Path(f'/tmp/.X11-unix/X{i}').exists():chosen=f':{i}';break
    if chosen is None:raise RuntimeError('no free isolated display')
    os.environ['DISPLAY']=chosen
    pngs={};records=[];window=None
    try:
        xvfb=subprocess.Popen(['Xvfb',chosen,'-screen','0','800x600x24','-ac','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.3);wm=subprocess.Popen(['openbox'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        d=display.Display(chosen)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=False,
                args=['--no-sandbox','--disable-gpu','--force-device-scale-factor=1','--window-position=0,0','--window-size=800,600'])
            env['browser']=browser.version;page=browser.new_page(no_viewport=True)
            def receive(msg):
                if msg.text.startswith('__SCORER__'):
                    row=json.loads(msg.text[len('__SCORER__'):]);row['received_ns']=time.perf_counter_ns()
                    append(out/'scorer.jsonl',row)
            page.on('console',receive)
            cdp=page.context.new_cdp_session(page);w=cdp.send('Browser.getWindowForTarget')
            cdp.send('Browser.setWindowBounds',{'windowId':w['windowId'],'bounds':{'windowState':'fullscreen'}})
            page.wait_for_timeout(150)
            geometry=page.evaluate('({w:innerWidth,h:innerHeight,dpr:devicePixelRatio,ow:outerWidth,oh:outerHeight})')
            if geometry!={'w':800,'h':600,'dpr':1,'ow':800,'oh':600}:raise ValueError('unbound viewport')
            env['geometry']=geometry;write(out/'environment.json',env)
            for ci,case in enumerate(CASES):
                order=list(ARMS);shift=(ci+layout)%len(order);order=order[shift:]+order[:shift]
                for arm in order:
                    token=f'L{layout}-{case}-{arm}';observations=[]
                    for phase in range(3):
                        if phase==2:time.sleep(plan['simulated_wait_ms']/1000)
                        # Setup channel only; resolver is never given layout, case, phase or scorer.
                        page.set_content(html(case,layout,phase,token))
                        page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                        before=d.get_input_focus().focus.id;start=time.perf_counter_ns()
                        im=ImageGrab.grab(xdisplay=chosen).convert('RGB');captured=time.perf_counter_ns()
                        rgb=np.asarray(im);boxes=regions(rgb);classified=time.perf_counter_ns()
                        ax,raw,ax_ns=native(cdp);after=d.get_input_focus().focus.id
                        if before!=after:raise ValueError('focus changed during observation')
                        f=io.BytesIO();im.save(f,format='PNG');png=f.getvalue();h=digest(png)
                        if h not in pngs:
                            (out/(h+'.png')).write_bytes(png);pngs[h]=base64.b64encode(png).decode()
                        observations.append({'image_sha256':h,'pixel_sha256':digest(im.tobytes()),
                            'capture_ns':captured,'capture_duration_ns':captured-start,
                            'classification_ns':classified-captured,'regions':boxes,
                            'native':ax,'native_raw':raw,'native_duration_ns':ax_ns,
                            'focus':before,'native_finished_ns':time.perf_counter_ns()})
                    start=time.perf_counter_ns()
                    decision=resolve(arm,observations[0]['regions'],observations[1]['regions'],
                        observations[2]['regions'],observations[2]['native'],plan['grid_size'])
                    resolve_ns=time.perf_counter_ns()-start
                    press=None;release=None;point=decision['point']
                    if point is not None:
                        age=time.perf_counter_ns()-observations[2]['capture_ns']
                        if age>plan['max_current_age_ms']*1e6 or d.get_input_focus().focus.id!=before:
                            raise ValueError('input binding stale')
                        if d.screen().root.query_pointer().mask & X.Button1Mask:raise ValueError('pre-held input')
                        try:
                            xtest.fake_input(d,X.MotionNotify,x=round(point[0]),y=round(point[1]));d.sync()
                            press=time.perf_counter_ns();xtest.fake_input(d,X.ButtonPress,1);d.sync()
                        finally:
                            xtest.fake_input(d,X.ButtonRelease,1);d.sync();release=time.perf_counter_ns()
                    empty=not bool(d.screen().root.query_pointer().mask & X.Button1Mask)
                    if not empty:raise ValueError('release verification failed')
                    page.wait_for_timeout(60)
                    record={'token':token,'case':case,'layout':layout,'arm':arm,'observations':observations,
                        'decision':decision,'resolve_ns':resolve_ns,'press_ns':press,'release_ns':release,'empty':empty}
                    records.append(record);append(out/'records.jsonl',record)
                print(json.dumps({'case_completed':case,'layout':layout,'arms':len(order)}),flush=True)
            browser.close()
    finally:
        if d is not None:d.close()
        if wm is not None:wm.terminate();wm.wait(timeout=5)
        if xvfb is not None:xvfb.terminate();xvfb.wait(timeout=5)
    # Independent effects are read only after the browser/controller has terminated.
    receipts=[json.loads(s) for s in (out/'scorer.jsonl').read_text().splitlines()] if (out/'scorer.jsonl').exists() else []
    payload={'environment':env,'plan':plan,'records':records,'receipts':receipts,'pngs':pngs}
    packed=gzip.compress(json.dumps(payload,sort_keys=True,separators=(',',':')).encode(),mtime=0)
    (out/'evidence.json.gz').write_bytes(packed)
    write(out/'manifest.json',{'sha256':digest(packed),'bytes':len(packed),'records':len(records),'unique_pngs':len(pngs)})
    return payload

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--layout',type=int,choices=(0,1),required=True)
    args=ap.parse_args();run(args.out.resolve(),args.layout)
