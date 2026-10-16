#!/usr/bin/env python3
import argparse, hashlib, json, os, shutil, signal, subprocess, tempfile, time
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image
from Xlib import X, XK, display
from Xlib.ext import xtest

SCREEN_W, SCREEN_H = 1100, 800
HANDLE_DARK_MAX = 60
HANDLE_MIN = 100
DWELL_S = 0.020
SETTLE_S = 0.35

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200">
 <rect id="A" x="50" y="70" width="60" height="40" fill="#ff0000"/>
 <rect id="B" x="190" y="70" width="60" height="40" fill="#0000ff"/>
</svg>\n'''

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()

def snap(D, path):
    root=D.screen().root; g=root.get_geometry()
    raw=root.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff).data
    im=Image.frombytes('RGB',(g.width,g.height),raw,'raw','BGRX')
    im.save(path)
    return im

def color_bbox(im, kind):
    pix=im.load(); xs=[]; ys=[]
    # Restrict to document canvas; excludes UI palette colors.
    for y in range(145, min(im.height,700)):
        for x in range(50, min(im.width,720)):
            r,g,b=pix[x,y]
            ok=(r>=245 and g<=20 and b<=20) if kind=='red' else (b>=245 and r<=20 and g<=20)
            if ok: xs.append(x); ys.append(y)
    if not xs: raise RuntimeError(f'{kind}_not_found')
    return [min(xs), min(ys), max(xs)+1, max(ys)+1]

def click(D,x,y):
    D.screen().root.warp_pointer(int(x),int(y)); D.sync(); time.sleep(.03)
    xtest.fake_input(D,X.ButtonPress,1); D.sync(); time.sleep(.03)
    xtest.fake_input(D,X.ButtonRelease,1); D.sync(); time.sleep(SETTLE_S)

def move_pointer(D,x,y):
    D.screen().root.warp_pointer(int(x),int(y)); D.sync(); time.sleep(SETTLE_S)

def key(D,name,ctrl=False,shift=False):
    kc=D.keysym_to_keycode(XK.string_to_keysym(name))
    ctrlkc=D.keysym_to_keycode(XK.string_to_keysym('Control_L'))
    shiftkc=D.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
    if ctrl: xtest.fake_input(D,X.KeyPress,ctrlkc)
    if shift: xtest.fake_input(D,X.KeyPress,shiftkc)
    xtest.fake_input(D,X.KeyPress,kc); D.sync(); time.sleep(DWELL_S)
    xtest.fake_input(D,X.KeyRelease,kc)
    if shift: xtest.fake_input(D,X.KeyRelease,shiftkc)
    if ctrl: xtest.fake_input(D,X.KeyRelease,ctrlkc)
    D.sync(); time.sleep(.15)

def handle_counts(im, box):
    x0,y0,x1,y1=box
    strips={
      'top':(max(0,x0-22),max(0,y0-22),min(im.width,x1+22),y0),
      'bottom':(max(0,x0-22),y1,min(im.width,x1+22),min(im.height,y1+25)),
      'left':(max(0,x0-27),max(0,y0-17),x0,min(im.height,y1+17)),
      'right':(x1,max(0,y0-17),min(im.width,x1+29),min(im.height,y1+17)),
    }
    out={}
    for n,b in strips.items():
        c=0
        crop=im.crop(b)
        for r,g,bb in crop.getdata():
            if r < HANDLE_DARK_MAX and g < HANDLE_DARK_MAX and bb < HANDLE_DARK_MAX: c+=1
        out[n]=c
    return out

def selection_a(counts): return all(v>=HANDLE_MIN for v in counts.values())

def physical_state(D):
    km=D.query_keymap()
    pressed=[]
    for kc in range(256):
        if km[kc//8] & (1 << (kc%8)): pressed.append(kc)
    mask=D.screen().root.query_pointer().mask
    buttons=[b for b,bit in [(1,X.Button1Mask),(2,X.Button2Mask),(3,X.Button3Mask),(4,X.Button4Mask),(5,X.Button5Mask)] if mask & bit]
    return {'pressed_keycodes':pressed,'buttons':buttons}

def parse_svg(path):
    root=ET.parse(path).getroot(); out={}
    for e in root.iter():
        eid=e.attrib.get('id')
        if eid in ('A','B'):
            out[eid]={k:float(e.attrib[k]) for k in ('x','y','width','height')}
            out[eid]['fill']=e.attrib.get('fill') or e.attrib.get('style','')
    return out

def run(args):
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    svg=out/'case.svg'; svg.write_text(SVG)
    profile=out/'profile'; profile.mkdir()
    display_no=args.display
    os.environ['XAUTHORITY']='/dev/null'
    env=os.environ.copy(); env['DISPLAY']=f':{display_no}'; env['XAUTHORITY']='/dev/null'; env['INKSCAPE_PROFILE_DIR']=str(profile)
    procs=[]; events=[]
    def ev(name,**kw): events.append({'event':name,'t_ns':time.monotonic_ns(),**kw})
    try:
        xv=subprocess.Popen(['Xvfb',f':{display_no}','-screen','0',f'{SCREEN_W}x{SCREEN_H}x24','-nolisten','tcp'],stdout=open(out/'xvfb.out','wb'),stderr=subprocess.STDOUT,env=env); procs.append(xv); time.sleep(.25)
        ob=subprocess.Popen(['openbox'],stdout=open(out/'openbox.out','wb'),stderr=subprocess.STDOUT,env=env); procs.append(ob); time.sleep(.35)
        ink=subprocess.Popen(['inkscape',str(svg)],stdout=open(out/'inkscape.out','wb'),stderr=subprocess.STDOUT,env=env); procs.append(ink); ev('inkscape_start',pid=ink.pid)
        D=None; im=None
        for i in range(60):
            try:
                if D is None: D=display.Display(f':{display_no}')
                im=snap(D,out/'initial.png')
                rb=color_bbox(im,'red'); bb=color_bbox(im,'blue')
                break
            except Exception:
                time.sleep(.1)
        else: raise RuntimeError('render_timeout')
        # Let Openbox/Inkscape finish final window/layout placement, then bind geometry.
        time.sleep(1.0)
        im=snap(D,out/'initial.png'); rb=color_bbox(im,'red'); bb=color_bbox(im,'blue')
        ev('render_ready',red_bbox=rb,blue_bbox=bb)
        subprocess.run(['wmctrl','-a','case.svg - Inkscape'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(.2)
        before=parse_svg(svg)
        ax=(rb[0]+rb[2])//2; ay=(rb[1]+rb[3])//2; bx=(bb[0]+bb[2])//2; by=(bb[1]+bb[3])//2
        # Give the document focus, then use ordinary selector/Tab traversal.
        click(D,600,600); ev('focus_canvas')
        key(D,'F1'); key(D,'Tab'); ev('select_a_tab')
        im=snap(D,out/'a_validated.png'); init_counts=handle_counts(im,rb); init_ok=selection_a(init_counts); ev('initial_check',counts=init_counts,ok=init_ok)
        if not init_ok: raise RuntimeError('initial_a_selection_not_visible')
        focus0=getattr(D.get_input_focus().focus,'id',None)
        if args.scenario=='switch_to_B': key(D,'Tab'); ev('trajectory_switch_b')
        elif args.scenario=='A_B_A': key(D,'Tab'); key(D,'Tab',shift=True); ev('trajectory_b_a')
        elif args.scenario=='unrelated_pointer': move_pointer(D,50,600); ev('trajectory_pointer_move')
        elif args.scenario=='stable': ev('trajectory_stable')
        else: raise ValueError(args.scenario)
        final_im=snap(D,out/'final_check.png'); final_counts=handle_counts(final_im,rb); final_ok=selection_a(final_counts); ev('final_check',counts=final_counts,ok=final_ok)
        focus1=getattr(D.get_input_focus().focus,'id',None)
        prephys=physical_state(D); ev('pre_effect_physical',**prephys)
        effect_started=False
        if final_ok:
            effect_started=True; ev('effect_admit'); key(D,'Right'); ev('effect_release')
        else: ev('effect_refuse')
        postphys=physical_state(D); ev('post_effect_physical',**postphys)
        if effect_started:
            key(D,'s',ctrl=True); ev('save')
            time.sleep(.25)
        after=parse_svg(svg)
        finalphys=physical_state(D); ev('final_physical',**finalphys)
        ink.terminate()
        try: ink.wait(timeout=3)
        except subprocess.TimeoutExpired: ink.kill(); ink.wait()
        ev('inkscape_exit',returncode=ink.returncode)
        result={
          'schema':'selection-final-check-case-v1','scenario':args.scenario,'construction':args.construction,
          'red_bbox':rb,'blue_bbox':bb,'initial_counts':init_counts,'initial_check':init_ok,
          'final_counts':final_counts,'final_check':final_ok,'effect_started':effect_started,
          'focus_same':focus0==focus1,'focus0':focus0,'focus1':focus1,
          'pre_physical':prephys,'post_physical':postphys,'final_physical':finalphys,
          'before':before,'after':after,
          'delta_x':{k:after[k]['x']-before[k]['x'] for k in ('A','B')},
          'image_sha256':{p.name:sha256_file(p) for p in [out/'initial.png',out/'a_validated.png',out/'final_check.png']},
          'events':events,
        }
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True))
        return result
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=2)
                except: p.kill()

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--scenario',required=True,choices=['stable','switch_to_B','A_B_A','unrelated_pointer']); ap.add_argument('--out',required=True); ap.add_argument('--display',type=int,required=True); ap.add_argument('--construction',action='store_true')
    a=ap.parse_args(); r=run(a); print(json.dumps({k:r[k] for k in ['scenario','initial_counts','final_counts','final_check','effect_started','delta_x','focus_same','post_physical','final_physical']},sort_keys=True))
