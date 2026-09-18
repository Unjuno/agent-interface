from __future__ import annotations
import argparse,hashlib,json,os,random,socket,statistics,subprocess,sys,tempfile,time
from pathlib import Path
from Xlib import X,display,error

TASK='DECISION-POLICY-CACHE-XTERM-TRANSFER-20260918-001'
FORMAL_SEED=134920260918001;FORMAL_PAIRS=24
CONSTRUCTION_SEED=134920260918901;CONSTRUCTION_PAIRS=3
GAP_NS=40_000_000;ACTION_NS=5_000_000
ACTION_OFFSETS=tuple(range(ACTION_NS,GAP_NS,ACTION_NS));HARD_OFFSETS=(22_500_000,27_500_000,32_500_000)
VALID='VALID_CONTINUATION';HARD='HARD_INVALIDATION';ROI=(0,0,180,20)

def pct(vals,p):
    if not vals:return None
    xs=sorted(vals);return xs[max(0,min(len(xs)-1,int((len(xs)-1)*p)))]

def sleep_until_ns(target):
    while True:
        rem=target-time.perf_counter_ns()
        if rem<=0:return
        if rem>2_000_000:time.sleep((rem-500_000)/1e9)
        elif rem>100_000:time.sleep(rem/2e9)

def wait_path(p,timeout=4):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if Path(p).exists():return
        time.sleep(.005)
    raise RuntimeError(f'timeout waiting {p}')

def start_xvfb(case_root):
    auth=Path(case_root)/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600)
    env=os.environ.copy();env['XAUTHORITY']=str(auth)
    p=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x480x24','-nolisten','tcp','-pn','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    line=p.stdout.readline().strip()
    if not line:raise RuntimeError('Xvfb displayfd failed')
    env['DISPLAY']=':'+line
    return p,env

def descendants(root):
    out=[];q=list(root.query_tree().children)
    for _ in range(4):
        nq=[]
        for w in q:
            out.append(w)
            try:nq.extend(w.query_tree().children)
            except Exception:pass
        q=nq
    return out

def find_xterm(D,title,timeout=4):
    end=time.monotonic()+timeout;root=D.screen().root
    while time.monotonic()<end:
        for w in descendants(root):
            try:
                if w.get_wm_name()==title and w.get_attributes().map_state==X.IsViewable:return w
            except Exception:pass
        time.sleep(.01)
    raise RuntimeError('xterm target window not found')

def connect_unix(path,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        try:s.connect(str(path));return s
        except OSError:s.close();time.sleep(.005)
    raise RuntimeError('fixture socket connect timeout')

def request(sock,obj):
    sock.sendall((json.dumps(obj,sort_keys=True)+'\n').encode());buf=b''
    while b'\n' not in buf:
        chunk=sock.recv(65536)
        if not chunk:raise RuntimeError('fixture socket EOF')
        buf+=chunk
    raw,_=buf.split(b'\n',1);r=json.loads(raw)
    if not r.get('ok'):raise RuntimeError(r.get('error','fixture error'))
    return r

def capture_roi(win):
    x,y,w,h=ROI;b=time.perf_counter_ns();img=win.get_image(x,y,w,h,X.ZPixmap,0xffffffff);e=time.perf_counter_ns()
    data=bytes(img.data)
    if len(data)!=w*h*4:raise RuntimeError(f'ROI bytes {len(data)}')
    return b,e,data

def stable_digest(win,timeout_ns=150_000_000):
    end=time.perf_counter_ns()+timeout_ns;last=None
    while time.perf_counter_ns()<end:
        _,_,data=capture_roi(win);d=hashlib.sha256(data).hexdigest()
        if d==last:return d
        last=d;time.sleep(.002)
    raise RuntimeError('ROI did not stabilize')

def calibrate(sock,win):
    fp={}
    for state in (VALID,HARD):
        request(sock,{'cmd':'set_state','state':state,'case_id':'calibration'})
        fp[stable_digest(win)]=state
    if len(fp)!=2:raise RuntimeError('VALID/HARD fingerprints alias')
    request(sock,{'cmd':'set_state','state':VALID,'case_id':'calibration-end'});stable_digest(win)
    return fp

def schedules(n,seed):
    rng=random.Random(seed);vals=[HARD_OFFSETS[i%len(HARD_OFFSETS)] for i in range(n)];rng.shuffle(vals)
    return [{'pair_id':i,'hard_offset_ns':vals[i]} for i in range(n)]

def read_log(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]

def run_case(root,arm,sched,case_id):
    cr=Path(root)/case_id;cr.mkdir(parents=True,exist_ok=False)
    xvfb=xterm=D=sock=None;cleanup={'xterm_exit':False,'xvfb_exit':False,'socket_residual':None};exceptions=[]
    guards=[];commands=[];window_meta={};fp={}
    log=cr/'fixture.jsonl';ready=cr/'ready.json';sockpath=cr/'fixture.sock'
    try:
        xvfb,env=start_xvfb(cr);title='AI1349-'+case_id
        xterm=subprocess.Popen(['xterm','-fn','fixed','-b','0','-geometry','40x10+20+20','-title',title,'-e',sys.executable,str(Path(__file__).with_name('fixture.py')),'--socket',str(sockpath),'--ready',str(ready),'--log',str(log)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        wait_path(ready);D=display.Display(env['DISPLAY']);win=find_xterm(D,title)
        geo=win.get_geometry();window_meta={'xid':win.id,'width':geo.width,'height':geo.height,'roi':list(ROI),'mapped':True}
        if geo.width<ROI[2] or geo.height<ROI[3]:raise RuntimeError('XTerm smaller than ROI')
        sock=connect_unix(sockpath);fp=calibrate(sock,win)
        start=request(sock,{'cmd':'start_case','case_id':case_id,'hard_offset_ns':sched['hard_offset_ns'],'gap_ns':GAP_NS});start_ns=start['start_ns']
        terminal_guard_end=None
        if arm=='CACHED_POLICY_XTERM_GUARD':
            for idx,off in enumerate(ACTION_OFFSETS):
                target=start_ns+off;sleep_until_ns(target);action_begin=time.perf_counter_ns()
                gb,ge,data=capture_roi(win);digest=hashlib.sha256(data).hexdigest();observed=fp.get(digest,'UNKNOWN')
                g={'slot_offset_ns':off,'scheduled_ns':target,'action_begin_ns':action_begin,'guard_begin_ns':gb,'guard_end_ns':ge,'guard_duration_ns':ge-gb,'action_start_lag_ns':action_begin-target,'digest':digest,'observed_state':observed,'guard_bytes':len(data)}
                guards.append(g)
                if observed in (HARD,'UNKNOWN'):
                    terminal_guard_end=ge;g['disposition']='INVALIDATE';break
                g['disposition']='APPLY_PROGRESS';cmd_id=f'{case_id}-c{idx:02d}';send_ns=time.perf_counter_ns()
                request(sock,{'cmd':'apply_progress','case_id':case_id,'command_id':cmd_id});commands.append({'command_id':cmd_id,'send_ns':send_ns})
        sleep_until_ns(start_ns+GAP_NS);planner_return=time.perf_counter_ns();end=request(sock,{'cmd':'end_case','case_id':case_id})
        request(sock,{'cmd':'exit'});sock.close();sock=None;xterm.wait(timeout=3);cleanup['xterm_exit']=True
        if D is not None:D.close();D=None
        events=read_log(log)
        hard=next(e for e in events if e.get('event')=='scheduled_state' and e.get('case_id')==case_id)
        applies=[e for e in events if e.get('event')=='apply_result' and e.get('case_id')==case_id]
        byid={e['command_id']:e for e in applies};cmdrows=[]
        for c in commands:
            e=byid.get(c['command_id'])
            if e is None:raise RuntimeError('missing fixture command result')
            cmdrows.append({**c,**e})
        accepted=[c for c in cmdrows if c['accepted']]
        gap_accept=[c for c in accepted if c['effect_ns']<=start_ns+GAP_NS]
        hard_accepted=[c for c in accepted if c['state_at_recv']==HARD]
        post_terminal=[c for c in cmdrows if terminal_guard_end is not None and c['send_ns']>terminal_guard_end]
        nonoverlap=0;overlaps=0
        for g in guards:
            ov=not (g['guard_end_ns']<hard['begin_ns'] or g['guard_begin_ns']>hard['applied_ns']);g['transition_overlap']=ov
            if ov:overlaps+=1
            else:
                expected=VALID if g['guard_end_ns']<hard['begin_ns'] else HARD;g['oracle_state']=expected
                if g['observed_state']!=expected:nonoverlap+=1
        stop_ns=None if terminal_guard_end is None else terminal_guard_end-hard['applied_ns']
        accepted_valid=sum(1 for e in applies if e['accepted'] and e['state_at_recv']==VALID)
        delta=end['progress']
        return {'case_id':case_id,'pair_id':sched['pair_id'],'arm':arm,'hard_offset_ns':sched['hard_offset_ns'],'start_ns':start_ns,'gap_end_ns':start_ns+GAP_NS,'window':window_meta,'fingerprints':fp,'hard_transition':hard,'guards':guards,'commands':cmdrows,'planner_return_ns':planner_return,'end':end,'fixture_log':events,'verified_progress_during_gap':len(gap_accept),'accepted_effects':len(accepted),'hard_accepted_effects':len(hard_accepted),'post_terminal_commands':len(post_terminal),'nonoverlap_mismatch':nonoverlap,'transition_overlap_captures':overlaps,'hard_invalidation_to_stop_ns':stop_ns,'fixture_progress_delta':delta,'accepted_valid_effects':accepted_valid,'semantic_decisions_during_gap':0,'authority_actions':0,'task_input_actions':0,'xtest_actions':0,'exceptions':exceptions,'cleanup':cleanup}
    except Exception as e:
        exceptions.append({'type':type(e).__name__,'message':str(e)})
        return {'case_id':case_id,'pair_id':sched['pair_id'],'arm':arm,'hard_offset_ns':sched['hard_offset_ns'],'window':window_meta,'fingerprints':fp,'guards':guards,'commands':commands,'exceptions':exceptions,'cleanup':cleanup}
    finally:
        if sock is not None:
            try:request(sock,{'cmd':'exit'})
            except Exception:pass
            try:sock.close()
            except Exception:pass
        if D is not None:
            try:D.close()
            except Exception:pass
        if xterm is not None and xterm.poll() is None:
            try:xterm.terminate();xterm.wait(timeout=1)
            except Exception:
                try:xterm.kill();xterm.wait(timeout=1)
                except Exception:pass
        if xterm is not None:cleanup['xterm_exit']=xterm.poll() is not None
        if xvfb is not None:
            try:xvfb.terminate();xvfb.wait(timeout=2);cleanup['xvfb_exit']=True
            except Exception:
                try:xvfb.kill();xvfb.wait(timeout=1);cleanup['xvfb_exit']=True
                except Exception:pass
        cleanup['socket_residual']=sockpath.exists()

def summarize(cases):
    out={}
    for arm in ('WAIT_FOR_PLANNER','CACHED_POLICY_XTERM_GUARD'):
        cs=[c for c in cases if c.get('arm')==arm];guards=[g for c in cs for g in c.get('guards',[])]
        progress=[c.get('verified_progress_during_gap',0) for c in cs];stops=[c['hard_invalidation_to_stop_ns'] for c in cs if c.get('hard_invalidation_to_stop_ns') is not None]
        durations=[g['guard_duration_ns'] for g in guards];lags=[g['action_start_lag_ns'] for g in guards]
        out[arm]={'cases':len(cs),'progress':progress,'progress_median':statistics.median(progress) if progress else None,'progress_min':min(progress) if progress else None,'progress_max':max(progress) if progress else None,'accepted_effects':sum(c.get('accepted_effects',0) for c in cs),'hard_accepted_effects':sum(c.get('hard_accepted_effects',0) for c in cs),'post_terminal_commands':sum(c.get('post_terminal_commands',0) for c in cs),'nonoverlap_mismatch':sum(c.get('nonoverlap_mismatch',0) for c in cs),'guard_p95_ns':pct(durations,.95),'guard_p99_ns':pct(durations,.99),'guard_max_ns':max(durations) if durations else None,'action_start_lag_p95_ns':pct(lags,.95),'action_start_lag_max_ns':max(lags) if lags else None,'stop_p95_ns':pct(stops,.95),'stop_max_ns':max(stops) if stops else None,'cases_completed':sum(not c.get('exceptions') and c.get('cleanup',{}).get('xterm_exit') and c.get('cleanup',{}).get('xvfb_exit') and c.get('cleanup',{}).get('socket_residual') is False for c in cs),'progress_effect_exact':sum(c.get('fixture_progress_delta')==c.get('accepted_valid_effects') for c in cs)}
    pairs=[]
    for pid in sorted(set(c['pair_id'] for c in cases)):
        w=next(c for c in cases if c['pair_id']==pid and c['arm']=='WAIT_FOR_PLANNER');k=next(c for c in cases if c['pair_id']==pid and c['arm']=='CACHED_POLICY_XTERM_GUARD')
        pairs.append({'pair_id':pid,'hard_offset_ns':k['hard_offset_ns'],'wait_progress':w.get('verified_progress_during_gap',0),'cached_progress':k.get('verified_progress_during_gap',0),'delta':k.get('verified_progress_during_gap',0)-w.get('verified_progress_during_gap',0)})
    out['matched']={'pairs':pairs,'all_cached_gt_wait':all(p['delta']>0 for p in pairs),'delta_median':statistics.median([p['delta'] for p in pairs]) if pairs else None}
    return out

def decide(summary,pairs,cases):
    w=summary['WAIT_FOR_PLANNER'];c=summary['CACHED_POLICY_XTERM_GUARD'];m=summary['matched']
    if any(x.get('exceptions') for x in cases) or w['cases_completed']!=pairs or c['cases_completed']!=pairs:return 'FAIL_INTEGRITY'
    if c['nonoverlap_mismatch'] or c['hard_accepted_effects'] or c['post_terminal_commands']:return 'FAIL_CACHE_STALENESS_XTERM'
    if w['accepted_effects']!=0 or any(x!=0 for x in w['progress']):return 'FAIL_INTEGRITY'
    if c['progress_effect_exact']!=pairs or w['progress_effect_exact']!=pairs:return 'FAIL_INTEGRITY'
    useful=(c['progress_median'] is not None and c['progress_median']>=4 and m['all_cached_gt_wait'])
    safe=(c['stop_p95_ns'] is not None and c['stop_p95_ns']<=10_000_000 and c['stop_max_ns']<=15_000_000)
    cost=(c['guard_p95_ns'] is not None and c['guard_p95_ns']<1_500_000 and c['guard_p99_ns']<3_000_000 and c['action_start_lag_p95_ns']<=3_000_000 and c['action_start_lag_max_ns']<=12_000_000)
    if not safe or not cost:return 'HOLD_XTERM_EVIDENCE_TOO_SLOW'
    if not useful:return 'HOLD_NO_USEFUL_REUSE_WINDOW'
    return 'PASS_DECISION_POLICY_CACHE_XTERM_TRANSFER_SCOPED'

def run(pair_count,seed,formal_invocations,root):
    cases=[];ss=schedules(pair_count,seed)
    for s in ss:
        order=('WAIT_FOR_PLANNER','CACHED_POLICY_XTERM_GUARD') if s['pair_id']%2==0 else ('CACHED_POLICY_XTERM_GUARD','WAIT_FOR_PLANNER')
        for pos,arm in enumerate(order):cases.append(run_case(root,arm,s,f"p{s['pair_id']:03d}-{pos}-{arm}"))
    summary=summarize(cases);decision=decide(summary,pair_count,cases)
    return {'task':TASK,'seed':seed,'pairs':pair_count,'formal_invocations':formal_invocations,'reruns':0,'replacements':0,'tuning':0,'planner_gap_ns':GAP_NS,'action_cadence_ns':ACTION_NS,'hard_offsets_ns':list(HARD_OFFSETS),'cases':cases,'summary':summary,'decision':decision,'authority_actions':0,'task_input_actions':0,'xtest_actions':0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--formal',action='store_true');ap.add_argument('--out',required=True);ap.add_argument('--root',required=True)
    a=ap.parse_args();out=Path(a.out)
    if out.exists():raise SystemExit('result exists')
    pairs,seed=(FORMAL_PAIRS,FORMAL_SEED) if a.formal else (CONSTRUCTION_PAIRS,CONSTRUCTION_SEED)
    root=Path(a.root);root.mkdir(parents=True,exist_ok=False)
    t0=time.perf_counter_ns();r=run(pairs,seed,1 if a.formal else 0,root);r['wall_ns']=time.perf_counter_ns()-t0
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':r['decision'],'formal':a.formal,'pairs':pairs,'summary':r['summary']},sort_keys=True))

if __name__=='__main__':main()
