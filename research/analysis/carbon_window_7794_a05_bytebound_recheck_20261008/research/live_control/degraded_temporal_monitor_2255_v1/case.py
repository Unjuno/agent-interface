#!/usr/bin/env python3
import argparse, hashlib, json, os, pathlib, select, shutil, subprocess, sys, time

SCENARIOS = {
 'AB_WITHIN': [('A',1,0.0),('B',1,0.030)],
 'AB_LATE': [('A',1,0.0),('B',1,0.120)],
 'A_ONLY': [('A',1,0.0)],
 'CANCEL_COMPLETE': [('A',1,0.0),('CANCEL',1,0.020),('B',1,0.020)],
 'CANCEL_DROP_DECLARED': [('A',1,0.0),('CANCEL',1,0.020),('B',1,0.020)],
 'CANCEL_DROP_UNDECLARED': [('A',1,0.0),('CANCEL',1,0.020),('B',1,0.020)],
 'REORDER_DECLARED': [('A',1,0.0),('B',1,0.030)],
 'CROSS_CLOCK_DECLARED': [('A',1,0.0),('B',1,0.030)],
}

def read_json_line(stream, timeout=3.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        r,_,_=select.select([stream],[],[],min(0.05,end-time.monotonic()))
        if r:
            line=stream.readline()
            if not line: raise RuntimeError('eof')
            return json.loads(line)
    raise TimeoutError('json line timeout')

def send(p,obj):
    p.stdin.write(json.dumps(obj,separators=(',',':'))+'\n'); p.stdin.flush()

def wait_display(display_num, auth, timeout=3.0):
    sock=pathlib.Path(f'/tmp/.X11-unix/X{display_num}')
    end=time.monotonic()+timeout
    env={**os.environ,'DISPLAY':f':{display_num}','XAUTHORITY':str(auth)}
    while time.monotonic()<end:
        if sock.exists():
            r=subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if r.returncode==0: return
        time.sleep(0.02)
    raise RuntimeError('Xvfb not ready')

def oracle(events):
    pending=None
    for ev in events:
        if ev['phase']=='A': pending=(ev['epoch'],ev['server_ms'])
        elif ev['phase']=='CANCEL' and pending and pending[0]==ev['epoch']: pending=None
        elif ev['phase']=='B' and pending and pending[0]==ev['epoch']:
            dt=(ev['server_ms']-pending[1]) & 0xffffffff
            return {'status':'SATISFIED' if dt<=80 else 'NOT_SATISFIED','delta_ms':dt,'reason':None if dt<=80 else 'late'}
    return {'status':'NOT_SATISFIED','reason':'no_matching_B'}

def transform(scenario, raw):
    events=[dict(e) for e in raw]
    packet={'events':events,'coverage_complete':True,'order_complete':True,'clock_coherent':True,'scope':'title-contract-v1'}
    if scenario in {'CANCEL_DROP_DECLARED','CANCEL_DROP_UNDECLARED'}:
        packet['events']=[e for e in events if e['phase']!='CANCEL']
        if scenario=='CANCEL_DROP_DECLARED': packet['coverage_complete']=False
    elif scenario=='REORDER_DECLARED':
        packet['events']=list(reversed(events)); packet['order_complete']=False
    elif scenario=='CROSS_CLOCK_DECLARED':
        for e in packet['events']:
            if e['phase']=='B': e['clock_domain']='foreign-clock'
        packet['clock_coherent']=False
    return packet

def run_policy(study, packet, mode):
    p=subprocess.run([sys.executable,'-S','-B',str(study/'policy.py'),mode],input=json.dumps(packet),text=True,capture_output=True,timeout=3)
    if p.returncode!=0: raise RuntimeError(f'policy {mode} rc={p.returncode} stderr={p.stderr}')
    return {'mode':mode,'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode,'decision':json.loads(p.stdout)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--scenario',choices=SCENARIOS); ap.add_argument('--rep',type=int); ap.add_argument('--out',type=pathlib.Path); ap.add_argument('--display',type=int)
    a=ap.parse_args(); study=pathlib.Path(__file__).resolve().parent
    a.out.mkdir(parents=False,exist_ok=False)
    auth=a.out/'Xauthority'; auth.touch()
    cookie=subprocess.check_output(['mcookie'],text=True).strip()
    subprocess.run(['xauth','-f',str(auth),'add',f':{a.display}','.',cookie],check=True,capture_output=True,text=True)
    xvout=(a.out/'xvfb.stdout').open('w'); xverr=(a.out/'xvfb.stderr').open('w')
    xv=subprocess.Popen(['Xvfb',f':{a.display}','-screen','0','320x200x24','-nolisten','tcp','-auth',str(auth)],stdout=xvout,stderr=xverr,text=True)
    app=obs=None
    record={'scenario':a.scenario,'rep':a.rep,'display':a.display,'pids':{'xvfb':xv.pid},'commands':[],'app_responses':[],'raw_events':[]}
    try:
        wait_display(a.display,auth)
        env={**os.environ,'DISPLAY':f':{a.display}','XAUTHORITY':str(auth),'PYTHONDONTWRITEBYTECODE':'1'}
        app=subprocess.Popen([sys.executable,'-S','-B',str(study/'app.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(a.out/'app.stderr').open('w'),text=True,bufsize=1,env=env)
        record['pids']['app']=app.pid
        ready=read_json_line(app.stdout); record['app_responses'].append(ready); xid=ready['xid']
        expected=len(SCENARIOS[a.scenario])
        obs=subprocess.Popen([sys.executable,'-B',str(study/'observer.py'),f':{a.display}',str(xid),str(expected)],stdout=subprocess.PIPE,stderr=(a.out/'observer.stderr').open('w'),text=True,bufsize=1,env=env)
        record['pids']['observer']=obs.pid
        oready=read_json_line(obs.stdout); record['observer_ready']=oready
        # Establish event subscription before first mutation.
        time.sleep(0.03)
        for idx,(phase,epoch,delay) in enumerate(SCENARIOS[a.scenario]):
            if delay: time.sleep(delay)
            cmd={'op':'set','phase':phase,'epoch':epoch,'tag':idx}
            record['commands'].append({'cmd':cmd,'send_ns':time.monotonic_ns()}); send(app,cmd)
            ack=read_json_line(app.stdout); record['app_responses'].append(ack)
            ev=read_json_line(obs.stdout); record['raw_events'].append(ev)
        done=read_json_line(obs.stdout); record['observer_done']=done
        obs_rc=obs.wait(timeout=2); record['observer_exit']=obs_rc
        send(app,{'op':'snapshot'}); snap=read_json_line(app.stdout); record['app_responses'].append(snap); record['snapshot']=snap
        send(app,{'op':'close'}); closing=read_json_line(app.stdout); record['app_responses'].append(closing)
        app_rc=app.wait(timeout=2); record['app_exit']=app_rc
        packet=transform(a.scenario,record['raw_events']); record['delivery_packet']=packet
        record['oracle']=oracle(record['raw_events'])
        record['policies']=[run_policy(study,packet,'NAIVE_COMPILED'),run_policy(study,packet,'FAIL_CLOSED')]
        record['case_end_ns']=time.monotonic_ns()
        (a.out/'CASE.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    finally:
        if obs and obs.poll() is None: obs.terminate(); obs.wait(timeout=1)
        if app and app.poll() is None: app.terminate(); app.wait(timeout=1)
        if xv.poll() is None: xv.terminate(); xv.wait(timeout=2)
        record['xvfb_exit']=xv.returncode
        xvout.close(); xverr.close()
        if (a.out/'CASE.json').exists():
            d=json.loads((a.out/'CASE.json').read_text()); d['xvfb_exit']=xv.returncode; (a.out/'CASE.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
