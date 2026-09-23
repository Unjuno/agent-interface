#!/opt/pyvenv/bin/python3
import argparse,json,os,pathlib,signal,socket,subprocess,time,statistics
from Xlib import X,XK,display
from Xlib.ext import xtest

P=pathlib.Path(__file__).parent
PYTHON='/opt/pyvenv/bin/python3'
AUTH=P/'empty.Xauthority'
os.environ['XAUTHORITY']=str(AUTH)

def wait_file(path,timeout=4):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists(): return json.loads(path.read_text())
        time.sleep(0.002)
    raise TimeoutError(path)

def wait_x(display_name,timeout=4):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try: return display.Display(display_name)
        except Exception: time.sleep(0.02)
    raise TimeoutError('display')

def viewable_top(d):
    root=d.screen().root; end=time.monotonic()+4
    while time.monotonic()<end:
        for w in root.query_tree().children:
            try:
                if w.get_attributes().map_state==X.IsViewable:
                    cls=w.get_wm_class(); name=w.get_wm_name()
                    if cls and any('xterm' in str(z).lower() for z in cls): return w
                    if name and 'xterm' in str(name).lower(): return w
            except Exception: pass
        time.sleep(0.02)
    raise RuntimeError('no xterm top')

def key_down(d,kc):
    km=d.query_keymap()
    # python-xlib returns 32-byte str/bytes-like
    if isinstance(km,str): km=km.encode('latin1')
    return bool(km[kc//8] & (1<<(kc%8)))

def schedule(target_ns):
    while True:
        now=time.perf_counter_ns(); rem=target_ns-now
        if rem<=0: return
        if rem>2_000_000: time.sleep((rem-2_000_000)/1e9)
        else:
            while time.perf_counter_ns()<target_ns: pass
            return

def run_case(case_id,transport,display_no):
    c=P/'cases'/case_id; c.mkdir(parents=True,exist_ok=False)
    ready=c/'ready.json'; inp=c/'input.json'; eff=c/'effect.json'; sockp=c/'effect.sock'
    xs=subprocess.Popen(['Xvfb',f':{display_no}','-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    d=None; xp=None; us=None
    try:
        dn=f':{display_no}'; d=wait_x(dn)
        env=os.environ.copy(); env['DISPLAY']=dn; env['XAUTHORITY']=str(AUTH)
        if transport=='dgram':
            us=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM); us.bind(str(sockp)); us.settimeout(0.05)
        sid='s-'+case_id; rid='r-'+case_id
        cmd=['xterm','-geometry','80x24+0+0','-e',PYTHON,str(P/'helper.py'),'--ready',str(ready),'--input',str(inp),'--transport',transport,'--session',sid,'--request',rid,'--delay-ms','13']
        if transport=='file': cmd += ['--effect-file',str(eff)]
        else: cmd += ['--sock',str(sockp)]
        xp=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        wait_file(ready); w=viewable_top(d)
        w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync()
        focus=d.get_input_focus().focus
        focus_match=(getattr(focus,'id',None)==w.id)
        kc=d.keysym_to_keycode(XK.string_to_keysym('x'))
        t0=time.perf_counter_ns(); press_target=t0+38_000_000; frontier=t0+40_000_000
        schedule(press_target); press_ns=time.perf_counter_ns()
        xtest.fake_input(d,X.KeyPress,kc); d.sync()
        time.sleep(0.008)
        xtest.fake_input(d,X.KeyRelease,kc); d.sync(); release_ns=time.perf_counter_ns(); act_ns=release_ns
        if transport=='file':
            end=time.monotonic()+0.05; rec=None
            while time.monotonic()<end:
                if eff.exists(): rec=json.loads(eff.read_text()); break
                time.sleep(0.0001)
            if rec is None: raise TimeoutError('effect-file')
            seen_ns=time.perf_counter_ns()
        else:
            payload=us.recv(65535); seen_ns=time.perf_counter_ns(); rec=json.loads(payload.decode())
        input_row=wait_file(inp)
        rc=xp.wait(timeout=3)
        terminal_down=key_down(d,kc)
        valid=(rec.get('session_id')==sid and rec.get('request_id')==rid and rec.get('role')=='TASK_SEMANTIC_EFFECT' and rec.get('accepted_key')=='x' and rec.get('result')=='TOKEN_ACCEPTED' and rec.get('input_authority') is False and rec.get('semantic_authority') is False)
        row={
          'case_id':case_id,'transport':transport,'focus_match':focus_match,'press_offset_ms':(press_ns-t0)/1e6,'press_before_frontier':press_ns<frontier,
          'release_offset_ms':(release_ns-t0)/1e6,'input_byte_hex':input_row['byte_hex'],'input_recv_offset_ms':(input_row['recv_ns']-t0)/1e6,
          'effect_offset_ms':(rec['effect_ns']-t0)/1e6,'seen_offset_ms':(seen_ns-t0)/1e6,'transport_seen_ms':(seen_ns-rec['effect_ns'])/1e6,
          'drain_ms':(seen_ns-act_ns)/1e6,'receipt_valid':valid,'terminal_key_down':terminal_down,'xterm_rc':rc
        }
        (c/'row.json').write_text(json.dumps(row,indent=2,sort_keys=True)); return row
    finally:
        if us:
            us.close()
            try: sockp.unlink()
            except FileNotFoundError: pass
        if xp and xp.poll() is None:
            xp.terminate()
            try: xp.wait(timeout=1)
            except: xp.kill()
        if d:
            try: d.close()
            except: pass
        xs.terminate()
        try: xs.wait(timeout=1)
        except: xs.kill()

def pct(vals,p):
    s=sorted(vals); k=(len(s)-1)*p; a=int(k); b=min(a+1,len(s)-1); f=k-a; return s[a]*(1-f)+s[b]*f

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pairs',type=int,required=True); ap.add_argument('--start-display',type=int,default=130); ap.add_argument('--out',required=True); a=ap.parse_args()
    rows=[]
    for i in range(a.pairs):
        order=['file','dgram'] if i%2==0 else ['dgram','file']
        for j,tr in enumerate(order): rows.append(run_case(f'p{i:03d}-{tr}',tr,a.start_display+i*2+j))
    by={tr:[r for r in rows if r['transport']==tr] for tr in ['file','dgram']}
    summary={'pairs':a.pairs,'rows':rows,'stats':{}}
    for tr,rr in by.items():
        summary['stats'][tr]={
          'n':len(rr),'drain_median_ms':statistics.median(r['drain_ms'] for r in rr),'drain_p95_ms':pct([r['drain_ms'] for r in rr],0.95),'drain_max_ms':max(r['drain_ms'] for r in rr),
          'transport_median_ms':statistics.median(r['transport_seen_ms'] for r in rr),'transport_p95_ms':pct([r['transport_seen_ms'] for r in rr],0.95),'transport_max_ms':max(r['transport_seen_ms'] for r in rr),
          'integrity':sum(1 for r in rr if r['focus_match'] and r['press_before_frontier'] and r['input_byte_hex']=='78' and r['receipt_valid'] and not r['terminal_key_down'] and r['xterm_rc']==0)
        }
    diffs=[]
    for i in range(a.pairs):
        f=next(r for r in rows if r['case_id']==f'p{i:03d}-file'); u=next(r for r in rows if r['case_id']==f'p{i:03d}-dgram'); diffs.append(f['drain_ms']-u['drain_ms'])
    summary['matched_file_minus_dgram_median_ms']=statistics.median(diffs)
    pathlib.Path(a.out).write_text(json.dumps(summary,indent=2,sort_keys=True))
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
if __name__=='__main__': main()
