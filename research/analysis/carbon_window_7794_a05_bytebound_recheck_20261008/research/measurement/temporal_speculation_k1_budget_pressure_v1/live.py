import json,subprocess,sys,time,statistics
from pathlib import Path
from contract import Case,current_only_select,temporal_select
HERE=Path(__file__).parent
GAP_NS=40_000_000

def run_one(realized,arm):
    p=subprocess.Popen([sys.executable,str(HERE/'fixture_child.py'),str(realized)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    ev=json.loads(p.stdout.readline()); assert ev['event']=='REALIZED'
    t_real=ev['t_realized_ns']
    if arm in ('wait','current'):
        # selected discriminator guarantees current-only miss, so both wait for gap end.
        deadline=t_real + 30_000_000
        while time.perf_counter_ns()<deadline: time.sleep(0.0002)
    cmd={'expected_state':realized,'authority':True,'fresh':True}
    p.stdin.write(json.dumps(cmd)+'\n');p.stdin.flush(); out=json.loads(p.stdout.readline()); rc=p.wait(timeout=2)
    assert out.get('effect') is True and not out.get('wrong') and rc==0
    return {'arm':arm,'latency_ns':out['t_effect_ns']-t_real,'wrong':False,'effect':True}

def construction():
    rows=[]
    c=Case(-1,(3,2,1),-1,'left')
    assert current_only_select(c)==(1,) and temporal_select(c)==(-1,)
    for arm in ('wait','current','temporal'): rows.append(run_one(-1,arm))
    return rows

def formal(cases):
    rows=[]
    # 24 predetermined monotone-left discriminators: temporal K1 selects -1; current-only fixed tie-break selects +1.
    c=Case(-1,(3,2,1),-1,'left')
    assert current_only_select(c)==(1,) and temporal_select(c)==(-1,)
    for i in range(24):
        realized=-1
        order=(('wait','current','temporal') if i%3==0 else ('current','temporal','wait') if i%3==1 else ('temporal','wait','current'))
        for arm in order:
            r=run_one(realized,arm);r['trial']=i;rows.append(r)
    return rows
