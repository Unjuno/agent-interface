#!/usr/bin/env python3
import argparse, hashlib, json, os, signal, subprocess, tempfile, time, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import ImageGrab
from Xlib import X, XK, display as xdisplay
from Xlib.ext import xtest

W,H=1280,800
SVG_NS='{http://www.w3.org/2000/svg}'

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def color_bbox(im, color, roi=None):
    im=im.convert('RGB'); pts=[]
    if roi is None: x0,y0,x1,y1=100,170,1180,720
    else: x0,y0,x1,y1=roi
    for y in range(y0,y1,2):
        for x in range(x0,x1,2):
            r,g,b=im.getpixel((x,y))
            if color=='red': ok=r>=240 and g<=20 and b<=20
            else: ok=b>=240 and r<=20 and g<=20
            if ok: pts.append((x,y))
    if len(pts)<100: raise RuntimeError(f'{color}_target_missing:{len(pts)}')
    xs=sorted(p[0] for p in pts); ys=sorted(p[1] for p in pts)
    q=lambda a,p:a[int((len(a)-1)*p)]
    return [q(xs,.03),q(ys,.03),q(xs,.97)+1,q(ys,.97)+1]

def center(b): return [(b[0]+b[2]-1)//2,(b[1]+b[3]-1)//2]

def dark_count(im, box):
    im=im.convert('RGB'); l,t,r,b=box; n=0
    for y in range(max(0,t),min(im.height,b)):
        for x in range(max(0,l),min(im.width,r)):
            if max(im.getpixel((x,y))) <= 55: n += 1
    return n

def selection_score(im, bbox, expansion=20, minimum=20):
    l,t,r,b=bbox
    zones={
      'left':[l-expansion,t-expansion,l,b+expansion],
      'right':[r,t-expansion,r+expansion,b+expansion],
      'top':[l,t-expansion,r,t],
      'bottom':[l,b,r,b+expansion],
    }
    counts={k:dark_count(im,v) for k,v in zones.items()}
    return {'success':all(v>=minimum for v in counts.values()),'counts':counts,'minimum':minimum,'zones':zones}

def parse_positions(path):
    root=ET.parse(path).getroot(); out={}
    for el in root.findall(SVG_NS+'rect'):
        if el.attrib.get('id') in ('A','B'):
            out[el.attrib['id']]={'x':float(el.attrib.get('x','nan')),'y':float(el.attrib.get('y','nan')),'transform':el.attrib.get('transform')}
    return out

class Session:
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=False)
        self.tmp=Path(tempfile.mkdtemp(prefix='ink-race-'))
        self.procs=[]; self.display_num=self._pick_display(); self.name=f':{self.display_num}'
        self.auth=self.tmp/'Xauthority'; self.auth.touch()
        self.env=os.environ.copy(); self.env['DISPLAY']=self.name; self.env['XAUTHORITY']=str(self.auth)
        self._popen(['Xvfb',self.name,'-screen','0',f'{W}x{H}x24','-ac','-nolisten','tcp'])
        sock=Path(f'/tmp/.X11-unix/X{self.display_num}'); self._wait(lambda:sock.exists(),2,'xvfb')
        self._popen(['openbox','--config-file','/etc/xdg/openbox/rc.xml']); time.sleep(.2)
        os.environ['DISPLAY']=self.name; os.environ['XAUTHORITY']=str(self.auth)
        self.d=xdisplay.Display(self.name)
    def _pick_display(self):
        for n in range(210,250):
            if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists(): return n
        raise RuntimeError('no_display')
    def _popen(self,args):
        p=subprocess.Popen(args,env=self.env,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); self.procs.append(p); return p
    def _wait(self,fn,timeout,label):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if fn(): return
            time.sleep(.01)
        raise TimeoutError(label)
    def windows(self): return subprocess.run(['wmctrl','-l'],env=self.env,text=True,capture_output=True).stdout
    def wait_window(self,needle,timeout=10): self._wait(lambda:needle in self.windows(),timeout,'window')
    def focus(self,needle):
        lines=self.windows().splitlines(); hit=[l for l in lines if needle in l]
        if not hit: raise RuntimeError('window_not_found')
        subprocess.run(['wmctrl','-ia',hit[0].split()[0]],env=self.env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.08)
    def capture(self,path):
        im=ImageGrab.grab(); im.save(path); return im
    def click(self,x,y):
        xtest.fake_input(self.d,X.MotionNotify,x=int(x),y=int(y));self.d.sync()
        xtest.fake_input(self.d,X.ButtonPress,1);self.d.sync();xtest.fake_input(self.d,X.ButtonRelease,1);self.d.sync();time.sleep(.12)
    def key(self,name):
        kc=self.d.keysym_to_keycode(XK.string_to_keysym(name));
        xtest.fake_input(self.d,X.KeyPress,kc);self.d.sync();xtest.fake_input(self.d,X.KeyRelease,kc);self.d.sync();time.sleep(.04)
    def chord(self,mod,key):
        seq=[(mod,1),(key,1),(key,0),(mod,0)]
        for n,down in seq:
            kc=self.d.keysym_to_keycode(XK.string_to_keysym(n)); xtest.fake_input(self.d,X.KeyPress if down else X.KeyRelease,kc);self.d.sync()
        time.sleep(.2)
    def keymap_hex(self): return bytes(self.d.query_keymap()).hex()
    def close(self):
        try:self.d.close()
        except:pass
        for p in reversed(self.procs):
            try: os.killpg(p.pid,signal.SIGTERM)
            except:pass
        time.sleep(.05)
        for p in reversed(self.procs):
            try:
                if p.poll() is None: os.killpg(p.pid,signal.SIGKILL)
            except:pass

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--case-id',required=True); ap.add_argument('--trajectory',choices=['stable','switch'],required=True)
    a=ap.parse_args(); out=Path(a.out); s=Session(out); record={'case_id':a.case_id,'trajectory':a.trajectory,'schema':'inkscape-selection-race-case-v1'}
    try:
        svg=s.tmp/'two.svg'; svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="220" viewBox="0 0 400 220"><rect id="A" x="50" y="70" width="60" height="50" fill="#ff0000"/><rect id="B" x="220" y="70" width="60" height="50" fill="#0000ff"/></svg>')
        record['initial_svg_sha256']=sha256_file(svg)
        app=s._popen(['inkscape',str(svg)]); record['inkscape_pid']=app.pid; s.wait_window('two.svg');s.focus('two.svg');time.sleep(.8)
        p0=out/'initial.png'; im0=s.capture(p0); rb=color_bbox(im0,'red'); bb=color_bbox(im0,'blue'); record['initial_bbox']={'A':rb,'B':bb}
        s.key('F1'); s.click(*center(rb));
        pr=out/'revalidate.png'; imr=s.capture(pr);
        rroi=[max(0,rb[0]-30),max(0,rb[1]-30),min(W,rb[2]+30),min(H,rb[3]+30)]; broi=[max(0,bb[0]-30),max(0,bb[1]-30),min(W,bb[2]+30),min(H,bb[3]+30)]
        rb2=color_bbox(imr,'red',rroi); bb2=color_bbox(imr,'blue',broi); score=selection_score(imr,rb2)
        record['revalidation']={'A_bbox':rb2,'B_bbox':bb2,'selection_score_A':score,'image_sha256':sha256_file(pr)}
        c0=center(rb); c1=center(rb2); stable_target=(abs(c0[0]-c1[0])<=5 and abs(c0[1]-c1[1])<=5 and bb2==bb)
        record['revalidation']['stable_target']=stable_target
        if not stable_target or not score['success']: raise RuntimeError(f'revalidation_failed:{record["revalidation"]}')
        record['revalidated_ns']=time.monotonic_ns()
        if a.trajectory=='switch':
            s.click(*center(bb2)); record['mutation_ns']=time.monotonic_ns()
        else:
            time.sleep(.12); record['mutation_ns']=None
        record['effect_start_ns']=time.monotonic_ns()
        for _ in range(5): s.key('Right')
        record['effect_end_ns']=time.monotonic_ns(); record['keymap_after_effect_hex']=s.keymap_hex()
        s.chord('Control_L','s');time.sleep(.4); record['keymap_after_save_hex']=s.keymap_hex()
        saved=out/'saved.svg'; saved.write_bytes(svg.read_bytes()); record['saved_svg_sha256']=sha256_file(saved); record['positions']=parse_positions(saved)
        ax=record['positions']['A']['x']; bx=record['positions']['B']['x']
        if a.trajectory=='stable':
            verdict='CORRECT_A' if ax>50.5 and abs(bx-220)<.5 else 'OTHER'
        else:
            verdict='WRONG_B' if abs(ax-50)<.5 and bx>220.5 else ('REJECTED' if abs(ax-50)<.5 and abs(bx-220)<.5 else 'OTHER')
        record['verdict']=verdict; record['process_alive_before_cleanup']=app.poll() is None
        record['artifacts']={p.name:sha256_file(p) for p in out.iterdir() if p.is_file() and p.name!='result.json'}
        (out/'result.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
        print(json.dumps(record,sort_keys=True))
    except Exception as e:
        record['error']=repr(e); (out/'result.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n'); raise
    finally: s.close()
if __name__=='__main__':main()
