from __future__ import annotations
import argparse,collections,hashlib,json,os,subprocess,time
from pathlib import Path
from Xlib import X,display
from rule import decide

STATES=['CURRENT_CLICK_UNIQUE','CURRENT_CLICK_MULTI','CURRENT_TYPE','CURRENT_SCROLL_MULTI','NO_ACTION','MISSING_TARGET','AMBIGUOUS_TARGET']
PUBLIC_KEYS={'session_id','observation_id','generation','allowed_operations','candidates','target_admissibility','payload_ref','receipt_ns'}
FORBIDDEN={'acceptable','hidden_mode','future_effect','post_state','oracle','oracle_facts','desired_action'}

def key(d): return tuple((k,d[k]) for k in sorted(d))
def normalized(p,d):
    z={'op':d['op']}
    if 'reason' in d:z['reason']=d['reason']
    if 'target' in d:
        ids=[c['id'] for c in p['candidates']]; z['target_slot']=ids.index(d['target']) if d['target'] in ids else 'UNBOUND'
    if 'payload_ref' in d:z['payload_arg']='PAYLOAD_PRESENT' if d['payload_ref'] is not None else 'NULL'
    return tuple((k,z[k]) for k in sorted(z))
def signature(p):
    return (tuple(sorted(p['allowed_operations'])),p['target_admissibility'],p['payload_ref'] is not None,tuple((c['role'],tuple(sorted(c['ops']))) for c in p['candidates']))
def wait(path,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if path.exists(): return
        time.sleep(.005)
    raise RuntimeError(f'timeout {path}')
def run_session(root,session,display_num,construction=False):
    sroot=root/(f'construction-session-{session:02d}' if construction else f'formal-session-{session:02d}'); sroot.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy();env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=str(sroot/'xauth'); Path(env['XAUTHORITY']).touch()
    xv=subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0','320x240x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    sock=Path(f'/tmp/.X11-unix/X{display_num}')
    try:
        wait(sock)
        fix=subprocess.Popen(['python',str(root/'fixture.py'),'--root',str(sroot),'--session',str(session)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            wait(sroot/'ready'); time.sleep(.08)
            old_display=os.environ.get('DISPLAY'); old_xauth=os.environ.get('XAUTHORITY')
            os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']
            d=display.Display(env['DISPLAY']); rw=d.screen().root
            neg=['STALE','UNSUPPORTED_OPERATION','PAYLOAD_MISSING'][session%3]
            modes=STATES+[neg]; rows=[]
            for seq,mode in enumerate(modes):
                (sroot/'command.json').write_text(json.dumps({'seq':seq,'mode':mode}))
                pp=sroot/'public'/f'{seq:02d}.json'; op=sroot/'oracle'/f'{seq:02d}.json'; wait(pp); wait(op)
                read_ns=time.perf_counter_ns(); p=json.loads(pp.read_text()); o=json.loads(op.read_text())
                # X11 witness: screenshot bytes from the actual private root after state application.
                img=rw.get_image(0,0,320,240,X.ZPixmap,0xffffffff); pix=bytes(img.data); xhash=hashlib.sha256(pix).hexdigest()
                prop=decide(p); member=key(prop) in {key(x) for x in o['acceptable']}
                rows.append({'session':session,'seq':seq,'mode':mode,'public':p,'oracle':o,'proposal':prop,'member':member,'read_ns':read_ns,'x11_sha256':xhash})
            d.close()
            if old_display is None: os.environ.pop('DISPLAY',None)
            else: os.environ['DISPLAY']=old_display
            if old_xauth is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=old_xauth
            (sroot/'done').write_text('1'); fix.wait(timeout=2)
            return rows,{'fixture_rc':fix.returncode,'xvfb_pid':xv.pid,'fixture_pid':fix.pid,'socket':str(sock)}
        finally:
            if fix.poll() is None: fix.kill();fix.wait()
    finally:
        if xv.poll() is None: xv.terminate()
        try:xv.wait(timeout=.3)
        except: xv.kill();xv.wait()
        for _ in range(100):
            if not sock.exists():break
            time.sleep(.005)

def main(out,construction=False):
    root=Path(__file__).resolve().parent; sessions=1 if construction else 12; base=19100 if construction else 19200
    allrows=[];cleanup=[]
    for s in range(sessions):
        rows,cl=run_session(root,s,base+s,construction);allrows+=rows;cleanup.append(cl)
    groups=collections.defaultdict(list);exact=pos=neg=poscov=negexact=falseexec=staleexec=missing=leak=ordererr=0; xuniq=set()
    for r in allrows:
        p,o,prop=r['public'],r['oracle'],r['proposal']; groups[signature(p)].append((p,o));xuniq.add(r['x11_sha256'])
        if set(p)!=PUBLIC_KEYS or set(p)&FORBIDDEN: leak+=1
        if not (o['applied_ns']<=p['receipt_ns']<=r['read_ns']):ordererr+=1
        if p['generation']!=o['generation']:ordererr+=1
        member=r['member']; exact+=member; isneg=all(x['op'] in ('NO_LOCAL_ACTION','YIELD') for x in o['acceptable'])
        if isneg:
            neg+=1;negexact+=member;falseexec+=prop['op'] in ('CLICK','TYPE_TEXT','SCROLL')
        else:pos+=1;poscov+=member
        if p['target_admissibility']=='STALE' and prop['op'] in ('CLICK','TYPE_TEXT','SCROLL'):staleexec+=1
        if any(x['op']=='TYPE_TEXT' for x in o['acceptable']) and p['payload_ref'] is None:missing+=1
    conflicts=0
    for items in groups.values():
        common=None
        for p,o in items:
            s={normalized(p,d) for d in o['acceptable']}; common=s if common is None else common&s
        conflicts+=not bool(common)
    errors=[]
    expected_rows=sessions*8
    if len(allrows)!=expected_rows:errors.append('rows')
    if exact!=expected_rows:errors.append('membership')
    if falseexec:errors.append('false_exec')
    if staleexec:errors.append('stale_exec')
    if missing:errors.append('missing_arg')
    if leak:errors.append('leak')
    if ordererr:errors.append('ordering')
    if conflicts:errors.append('conflicts')
    if len(xuniq)<4:errors.append('x11_state_witness')
    decision='CONSTRUCTION_PASS' if construction and not errors else ('PASS_PRIVATE_X11_OPERATION_TARGET_CONTRACT_SCOPED' if not construction and not errors else 'FAIL_INTEGRITY_OR_SEMANTICS')
    result={'task':'OPERATION-TARGET-PRIVATE-X11-REALSTATE-CENSUS-20260918-001','construction':construction,'formal_invocations':0 if construction else 1,'reruns':0,
      'decision':decision,'errors':errors,'rows':len(allrows),'exact_membership':exact,'positives':pos,'positive_coverage':poscov,'semantic_negatives':neg,'semantic_negative_exact':negexact,
      'false_executable_negatives':falseexec,'stale_executable':staleexec,'missing_arguments':missing,'public_oracle_leakage':leak,'ordering_errors':ordererr,'normalized_conflicts':conflicts,
      'unique_x11_frame_hashes':len(xuniq),'rows_detail':allrows,'cleanup':cleanup,'model_calls':0,'task_input_actions':0}
    if out:Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows_detail','cleanup')},sort_keys=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out');ap.add_argument('--construction',action='store_true');a=ap.parse_args();main(a.out,a.construction)
