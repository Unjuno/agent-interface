"""Finite real-XTEST comparison. App receipts, not the private scorer, drive input.

The fixture is deliberately app-aware; this is NOT Agent Interface runtime wiring,
semantic GUI grounding, Doom efficacy, or a deployment benchmark.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from Xlib import X, XK, display
from Xlib.ext import xtest
from fence import OutcomeFence
from fixture import MODES
from private_desktop import desktop

HERE = Path(__file__).resolve().parent
BASE = '120a1b8de6d515d75c2200ca3acc310a124fb373'
ARMS = ('TIMEOUT_RETRY', 'OUTCOME_FENCE')
RETRY_NS, WINDOW_NS, HOLD_S = 100_000_000, 500_000_000, .025


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def rows(path):
    if not path.exists():return []
    text=path.read_text()
    return [json.loads(x) for x in text[:text.rfind('\n')+1].splitlines()]


def sample_keys(conn):
    start=time.perf_counter_ns()
    bitmap=conn.query_keymap();mask=conn.screen().root.query_pointer().mask
    payload={'keys_down':[k for k in range(256) if bitmap[k//8] & (1 << (k%8))],
             'buttons_down':[b for b in (1,2,3) if mask & (X.Button1Mask << (b-1))],
             'sample_ns':time.perf_counter_ns()}
    return {'started_ns':start,'finished_ns':time.perf_counter_ns(),'payload':payload}


def empty(sample):
    return not sample['payload']['keys_down'] and not sample['payload']['buttons_down']


def owns_focus(conn, xid):
    focus=conn.get_input_focus().focus
    if not hasattr(focus,'id') or focus.id in (0,1):return False
    for _ in range(32):
        if focus.id==xid:return True
        if focus.id==conn.screen().root.id:return False
        focus=focus.query_tree().parent
    return False


def press(conn,code,xid,prepare=None):
    before=sample_keys(conn)
    if not empty(before) or not owns_focus(conn,xid):raise RuntimeError('fresh input guard refused')
    issued=time.perf_counter_ns()
    if prepare is not None:prepare(issued)  # validate BEFORE any key-down
    try:
        xtest.fake_input(conn,X.KeyPress,code);conn.sync()
        ack=time.perf_counter_ns();held=sample_keys(conn)
        if code not in held['payload']['keys_down']:raise RuntimeError('key-down not observed')
        time.sleep(HOLD_S)
    finally:
        up_start=time.perf_counter_ns()
        xtest.fake_input(conn,X.KeyRelease,code);conn.sync()
        up_end=time.perf_counter_ns()
    released=sample_keys(conn)
    if not empty(released):raise RuntimeError('physical release not verified')
    return dict(issued_ns=issued,ack_ns=ack,up_started_ns=up_start,up_finished_ns=up_end,
                before=before,held=held,released=released)


def run_case(root,case,env,conn,code):
    root.mkdir();public=root/'public'
    session='pending-'+root.parent.name+'-'+root.name
    title='AI-PENDING-'+root.name
    start_process=time.perf_counter_ns()
    log=(root/'fixture.log').open('w')
    proc=subprocess.Popen(['xterm','-T',title,'-geometry','100x14','-e',sys.executable,'-u',
        str(HERE/'fixture.py'),'--root',str(root),'--session',session,'--mode',case['mode']],
        env=env,stdout=log,stderr=log)
    record={'case':case,'session':session,'input':[],'feedback':[],'decisions':[],
            'private_scorer_read_during_control':False}
    try:
        deadline=time.monotonic()+4
        xid=None
        while time.monotonic()<deadline:
            if proc.poll() is not None:raise RuntimeError('fixture exited before ready')
            probe=subprocess.run(['wmctrl','-lp'],env=env,text=True,capture_output=True,timeout=1)
            hits=[line for line in probe.stdout.splitlines() if line.endswith(title)] if probe.returncode==0 else []
            if public.joinpath('ready').exists() and len(hits)==1:
                fields=hits[0].split();xid=int(fields[0],16)
                if int(fields[2])!=proc.pid:raise RuntimeError('window pid mismatch')
                break
            time.sleep(.01)
        if xid is None:raise RuntimeError('fixture window not ready')
        subprocess.run(['wmctrl','-ia',hex(xid)],env=env,check=True,timeout=2)
        while not owns_focus(conn,xid):
            if time.monotonic()>deadline:raise RuntimeError('private fixture never focused')
            time.sleep(.005)
        first=press(conn,code,xid);record['input'].append(first)
        fence=OutcomeFence(session,'append-token',first['issued_ns'])
        fence.released(True,first['released']['finished_ns'])
        seen=0;retry_checked=False
        end=first['ack_ns']+WINDOW_NS
        def receive_feedback():
            nonlocal seen
            # Public application receipts ONLY. No mode-specific policy branch or private read.
            feedback=rows(public/'feedback.jsonl')
            for row in feedback[seen:]:
                now=time.perf_counter_ns();decision=fence.observe(row,now)
                record['feedback'].append({'row':row,'read_ns':now,'disposition':decision})
            seen=len(feedback)
        while time.perf_counter_ns()<end:
            receive_feedback()
            now=time.perf_counter_ns()
            if not retry_checked and now>=first['ack_ns']+RETRY_NS:
                retry_checked=True
                allow=(fence.status!='COMMITTED') if case['arm']=='TIMEOUT_RETRY' else fence.may_retry()
                record['decisions'].append({'at_ns':now,'status':fence.status,
                    'fence_may_retry':fence.may_retry(),'retry_selected':allow,
                    'observed_release_empty':empty(record['input'][-1]['released'])})
                if allow:
                    # Fresh X11 focus/empty checks are mandatory even for the unsafe comparator.
                    prepare=fence.begin_retry if case['arm']=='OUTCOME_FENCE' else None
                    action=press(conn,code,xid,prepare);record['input'].append(action)
                    if case['arm']=='TIMEOUT_RETRY':
                        fence=OutcomeFence(session,'append-token',action['issued_ns']);fence.attempt=2
                    fence.released(True,action['released']['finished_ns'])
            time.sleep(.003)
        receive_feedback()
        record.update(controller_outcome=fence.finish_observation(),control_ended_ns=time.perf_counter_ns(),
                      active_attempt=fence.attempt,ignored_feedback=fence.ignored)
    finally:
        # End controller decisions before requesting cooperative fixture shutdown or scoring.
        record['control_closed_ns']=time.perf_counter_ns()
        public.mkdir(exist_ok=True);(public/'stop').touch()
        try:proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:proc.wait(timeout=1)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        record['fixture_returncode']=proc.returncode
        log.close()
        save(root/'controller.json',record)
    record['scorer_started_ns']=time.perf_counter_ns()
    ledger=rows(root/'private/commits.jsonl');received=rows(root/'private/received.jsonl')
    closed=rows(root/'private/closed.jsonl')
    effects=sorted(root.glob('private/effect-*.txt'))
    record.update(private_commits=ledger,private_received=received,private_closed=closed,
                  effect_count=len(effects),effect_tokens=[p.read_text() for p in effects])
    expected_inputs=(1 if case['mode']=='immediate' else 2) if case['arm']=='TIMEOUT_RETRY' else (2 if case['mode']=='reject_once' else 1)
    expected_effects=0 if case['mode']=='silent' else (1 if case['mode']=='reject_once' else expected_inputs)
    expected_status='UNKNOWN' if case['mode'] in ('lost_feedback','silent') else 'COMMITTED'
    record['checks']={
        'expected_input_count':len(record['input'])==expected_inputs,
        'expected_effect_count':len(effects)==expected_effects,
        'file_ledger_received_agree':len(effects)==len(ledger) and len(received)==len(record['input']),
        'exact_effect_tokens':all(p.read_text()==session for p in effects),
        'expected_controller_outcome':record['controller_outcome']==expected_status,
        'all_releases_empty':all(empty(x['released']) for x in record['input']),
        'private_scorer_after_control':record['scorer_started_ns']>record['control_closed_ns'],
        'fixture_closed_cleanly':proc.returncode==0 and len(closed)==1 and closed[0]['pending']==0,
        'candidate_no_duplicate':case['arm']!='OUTCOME_FENCE' or len(effects)<=1,
        'candidate_retry_requires_no_effect':case['arm']!='OUTCOME_FENCE' or all(not d['retry_selected'] or d['fence_may_retry'] for d in record['decisions']),
    }
    record['pass']=all(record['checks'].values())
    record['case_wall_ms']=(time.perf_counter_ns()-start_process)/1e6
    save(root/'result.json',record)
    return record


def run(out,smoke=False):
    plan=load(HERE/'plan.json')
    for name,sha in plan['sources'].items():
        if digest(HERE/name)!=sha:raise RuntimeError('frozen source mismatch: '+name)
    out.mkdir(parents=True,exist_ok=False)  # no resume of a consumed local output
    save(out/'plan.json',plan)
    cpu=next(x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name'))
    save(out/'environment.json',dict(base=BASE,python=platform.python_version(),kernel=platform.release(),
        cpu=cpu,affinity=sorted(os.sched_getaffinity(0)),cpu_clock='not pinned',
        xterm=subprocess.check_output(['xterm','-version'],text=True).strip(),
        clock=time.get_clock_info('perf_counter').implementation,
        clock_resolution_s=time.get_clock_info('perf_counter').resolution,
        input='XTEST on private Xvfb/Openbox; 25 ms Return',sample_delay_ms=3,
        fixture='app-aware synthetic append-only service in real xterm',
        controller_feedback='public application receipts only',model_calls=0,
        measurement_network_calls=0,production_executor_used=False))
    cases=plan['schedule'][:2] if smoke else plan['schedule']
    results=[]
    try:
        with desktop(out) as env:
            conn=display.Display(env['DISPLAY'])
            code=conn.keysym_to_keycode(XK.string_to_keysym('Return'))
            try:
                for index,case in enumerate(cases):
                    result=run_case(out/f'case-{index:02d}',case,env,conn,code)
                    results.append(result)
                    print(json.dumps({'case':index,**case,'effects':result['effect_count'],
                        'inputs':len(result['input']),'outcome':result['controller_outcome'],'pass':result['pass']}),flush=True)
                    if not result['pass']:raise RuntimeError('first failed case retained; no retry')
            finally:
                xtest.fake_input(conn,X.KeyRelease,code);conn.sync();conn.close()
    except BaseException as exc:
        save(out/'failure.json',{'exception':repr(exc),'completed':len(results)})
        raise
    summary={'schema':'pending-effect-native-calibration-v1','allocation':out.name,
        'scope':'development calibration, synthetic app receipts; no production or Doom integration',
        'completed':len(results),'pass':all(r['pass'] for r in results),
        'rows':[{'case':r['case'],'inputs':len(r['input']),'effects':r['effect_count'],
                 'outcome':r['controller_outcome'],'pass':r['pass']} for r in results]}
    save(out/'summary.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--smoke',action='store_true')
    a=p.parse_args();run(a.out, a.smoke)
