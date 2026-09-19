from __future__ import annotations
import argparse, json, os, select, subprocess, time
from pathlib import Path
import tkinter as tk
from Xlib import X, Xatom, display
from monitor import Monitor, SATISFIED, EXPIRED, UNKNOWN

TASK='TEMPORAL-CONTRACT-X11-PROPERTYNOTIFY-R1-20260918-001'
DELTA_MS=80
SCENARIOS={
 'POSITIVE': [('A',20),('B',60)],
 'EXPIRE': [('A',20),('HB',130)],
 'NO_RESTART': [('A',20),('A',60),('B',120)],
}
EXPECTED={'POSITIVE':SATISFIED,'EXPIRE':EXPIRED,'NO_RESTART':EXPIRED}
ATOM_NAMES={'A':'_AI_TEMPORAL_A','B':'_AI_TEMPORAL_B','HB':'_AI_TEMPORAL_HEARTBEAT'}

def sleep_until_ns(target:int):
    while True:
        rem=target-time.perf_counter_ns()
        if rem<=0:return
        if rem>2_000_000: time.sleep((rem-500_000)/1e9)
        elif rem>100_000: time.sleep(rem/2e9)

def start_xvfb(root:Path):
    auth=root/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600)
    env=os.environ.copy();env['XAUTHORITY']=str(auth)
    p=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','320x180x24','-nolisten','tcp','-pn','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    line=p.stdout.readline().strip()
    if not line: raise RuntimeError('Xvfb displayfd failed')
    env['DISPLAY']=':'+line
    return p,env

def independent_oracle(events):
    anchor=None;last=None
    for row in events:
        t=row['server_time_ms'];label=row['label']
        if last is not None and t<last:return UNKNOWN
        if anchor is not None and t>anchor+DELTA_MS:return EXPIRED
        if anchor is None and label=='A':anchor=t
        if anchor is not None and label=='B' and anchor<=t<=anchor+DELTA_MS:return SATISFIED
        last=t
    return 'PENDING'

def cleanup(proc,root,watchD,pubD):
    for D in (watchD,pubD):
        try:
            if D is not None:D.close()
        except Exception:pass
    try:root.destroy()
    except Exception:pass
    if proc is not None:
        proc.terminate()
        try:proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill();proc.wait(timeout=2)

def run_case(case_root:Path,scenario:str,case_id:str):
    case_root.mkdir(parents=True,exist_ok=False)
    proc=None;root=None;watchD=None;pubD=None
    started=time.perf_counter_ns()
    try:
        proc,env=start_xvfb(case_root)
        old_display=os.environ.get('DISPLAY');old_auth=os.environ.get('XAUTHORITY')
        os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY']
        try:
            root=tk.Tk();root.title('AI temporal property fixture');root.geometry('200x100+10+10');root.update_idletasks();root.update()
            xid=root.winfo_id()
        finally:
            if old_display is None:os.environ.pop('DISPLAY',None)
            else:os.environ['DISPLAY']=old_display
            if old_auth is None:os.environ.pop('XAUTHORITY',None)
            else:os.environ['XAUTHORITY']=old_auth
        watchD=display.Display(env['DISPLAY']);pubD=display.Display(env['DISPLAY'])
        wwin=watchD.create_resource_object('window',xid);pwin=pubD.create_resource_object('window',xid)
        atoms={k:watchD.intern_atom(v,only_if_exists=False) for k,v in ATOM_NAMES.items()}
        pub_atoms={k:pubD.intern_atom(v,only_if_exists=False) for k,v in ATOM_NAMES.items()}
        reverse={v:k for k,v in atoms.items()}
        wwin.change_attributes(event_mask=X.PropertyChangeMask);watchD.sync()
        ready_ns=time.perf_counter_ns()
        publish=[];seq=0;base_ns=time.perf_counter_ns()
        for label,offset_ms in SCENARIOS[scenario]:
            sleep_until_ns(base_ns+offset_ms*1_000_000)
            seq+=1;before=time.perf_counter_ns()
            pwin.change_property(pub_atoms[label],Xatom.CARDINAL,32,[seq],X.PropModeReplace);pubD.sync()
            after=time.perf_counter_ns();publish.append({'seq':seq,'label':label,'offset_ms':offset_ms,'publish_begin_ns':before,'publish_end_ns':after})
        events=[];deadline=time.monotonic()+2.0
        while len(events)<len(SCENARIOS[scenario]) and time.monotonic()<deadline:
            if watchD.pending_events()==0:select.select([watchD.fileno()],[],[],0.05)
            while watchD.pending_events():
                ev=watchD.next_event()
                if ev.type!=X.PropertyNotify or ev.atom not in reverse:continue
                label=reverse[ev.atom]
                events.append({'seq_index':len(events),'label':label,'atom':int(ev.atom),'atom_name':ATOM_NAMES[label],'server_time_ms':int(ev.time),'parent_receive_ns':time.perf_counter_ns(),'state':int(ev.state)})
        m=Monitor('AB',DELTA_MS);statuses=[]
        for row in events:
            labs={'A'} if row['label']=='A' else ({'B'} if row['label']=='B' else set())
            statuses.append(m.feed(row['server_time_ms'],labs))
        actual=m.status;oracle=independent_oracle(events);times=[x['server_time_ms'] for x in events]
        nondecreasing=all(times[i]>=times[i-1] for i in range(1,len(times)))
        expected_labels=[x[0] for x in SCENARIOS[scenario]];observed_labels=[x['label'] for x in events];expected=EXPECTED[scenario]
        return {
          'task':TASK,'case_id':case_id,'scenario':scenario,'delta_ms':DELTA_MS,'display':env['DISPLAY'],'window_xid':xid,
          'listener_ready_ns':ready_ns,'publish':publish,'events':events,'observed_labels':observed_labels,'expected_labels':expected_labels,
          'server_times_nondecreasing':nondecreasing,'monitor_statuses':statuses,'candidate_terminal':actual,'oracle_terminal':oracle,'expected_terminal':expected,
          'event_count_ok':len(events)==len(expected_labels),'labels_exact':observed_labels==expected_labels,
          'candidate_oracle_match':actual==oracle,'terminal_correct':actual==expected,
          'elapsed_ns':time.perf_counter_ns()-started,'task_input_events':0
        }
    finally:
        if proc is not None:cleanup(proc,root,watchD,pubD)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['construction','formal'],required=True);ap.add_argument('--out',required=True);ap.add_argument('--root',required=True);a=ap.parse_args()
    out=Path(a.out);assert not out.exists();root=Path(a.root);root.mkdir(parents=True,exist_ok=True)
    schedule=list(SCENARIOS) if a.phase=='construction' else ['POSITIVE','EXPIRE','NO_RESTART']*4
    rows=[run_case(root/f'{i:02d}-{s.lower()}',s,f'{a.phase}-{i:02d}-{s}') for i,s in enumerate(schedule)]
    result={'task':TASK,'phase':a.phase,'formal_invocations':1 if a.phase=='formal' else 0,'reruns':0,'replacements':0,'tuning':0,'rows':rows}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'rows':len(rows),'terminals':[r['candidate_terminal'] for r in rows]},sort_keys=True))
if __name__=='__main__':main()
