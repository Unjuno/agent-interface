from __future__ import annotations
import argparse, json, multiprocessing as mp, os, threading, time
from pathlib import Path
from candidate import select, CLEAR, WATCH, HARD

TASK='CONCURRENT-FAST-DECISION-T2-ASYNC-RETURN-PREFLIGHT-20260918-009'
SAMPLE_NS=5_000_000
DELAYS_MS=(12,19,27,43,71)
PROGRAMS=('INITIAL_CLEAR','ACTIVATE','INVALIDATE','TRANSIENT')

def frontier_child(conn, delay_ns):
    start=time.perf_counter_ns()
    target=start+delay_ns
    while True:
        now=time.perf_counter_ns()
        rem=target-now
        if rem<=0: break
        time.sleep(min(rem/1e9,0.001))
    send_begin=time.perf_counter_ns()
    conn.send({'kind':'RETURN','child_pid':os.getpid(),'child_send_ns':send_begin})
    conn.close()

def state_at(program, elapsed_ns, delay_ns):
    if program=='INITIAL_CLEAR': return CLEAR
    if program=='ACTIVATE':
        return CLEAR if elapsed_ns >= int(delay_ns*0.30) else WATCH
    if program=='INVALIDATE':
        return HARD if elapsed_ns >= int(delay_ns*0.45) else CLEAR
    if program=='TRANSIENT':
        if elapsed_ns < int(delay_ns*0.25): return CLEAR
        if elapsed_ns < int(delay_ns*0.55): return WATCH
        return CLEAR
    raise ValueError(program)

def run_case(delay_ms, program, case_idx):
    delay_ns=delay_ms*1_000_000
    parent, child=mp.Pipe(duplex=False)
    proc=mp.Process(target=frontier_child,args=(child,delay_ns))
    lock=threading.Lock()
    stop=threading.Event()
    auth={'generation':1,'closed':False,'return_receive_ns':None,'close_ns':None}
    samples=[]; admissions=[]; rejected=[]
    start_ns=time.perf_counter_ns()
    proc.start(); child.close()

    def receiver():
        msg=parent.recv()
        recv_ns=time.perf_counter_ns()
        with lock:
            auth['return_receive_ns']=recv_ns
            auth['closed']=True
            auth['generation']+=1
            auth['close_ns']=time.perf_counter_ns()
        stop.set()
        msg['parent_receive_ns']=recv_ns
        auth['frontier_message']=msg

    def commit(kind, prepared_generation, sample_idx=None, prepared_ns=None):
        with lock:
            commit_ns=time.perf_counter_ns()
            ok=(not auth['closed'] and prepared_generation==auth['generation'])
            row={'kind':kind,'sample_idx':sample_idx,'prepared_generation':prepared_generation,
                 'prepared_ns':prepared_ns,'commit_ns':commit_ns,'admitted':ok,
                 'generation_at_commit':auth['generation'],'closed_at_commit':auth['closed']}
            (admissions if ok else rejected).append(row)
            return ok

    def controller():
        prev=None; idx=0
        next_tick=start_ns
        while not stop.is_set():
            now=time.perf_counter_ns()
            if now<next_tick:
                time.sleep(min((next_tick-now)/1e9,0.0005)); continue
            elapsed=now-start_ns
            st=state_at(program,elapsed,delay_ns)
            disp=select(st)
            with lock:
                gen=auth['generation']
            s={'idx':idx,'sample_ns':now,'elapsed_ns':elapsed,'state':st,'disposition':disp,'generation':gen}
            samples.append(s)
            if disp=='ADVANCE' and prev!=CLEAR:
                commit('lane',gen,idx,now)
            prev=st
            if disp=='YIELD':
                break
            idx+=1; next_tick=start_ns+idx*SAMPLE_NS

    def stale_probe():
        with lock:
            gen=auth['generation']
        prep=time.perf_counter_ns()
        if not stop.wait(timeout=2):
            rejected.append({'kind':'stale_probe','prepared_generation':gen,'prepared_ns':prep,
                             'commit_ns':time.perf_counter_ns(),'admitted':False,
                             'generation_at_commit':auth['generation'],'closed_at_commit':auth['closed'],
                             'probe_error':'return_not_observed'})
            return
        commit('stale_probe',gen,None,prep)

    rt=threading.Thread(target=receiver,name='frontier-receiver')
    ct=threading.Thread(target=controller,name='local-controller')
    st=threading.Thread(target=stale_probe,name='stale-probe')
    rt.start(); ct.start(); st.start()
    rt.join(timeout=2); ct.join(timeout=2); st.join(timeout=2)
    proc.join(timeout=2)
    end_ns=time.perf_counter_ns()
    return {
      'case_id':f'{delay_ms}ms-{program}-{case_idx}', 'delay_ms':delay_ms,'program':program,
      'start_ns':start_ns,'end_ns':end_ns,'sample_period_ns':SAMPLE_NS,
      'frontier_child_pid':getattr(proc,'pid',None),'child_exitcode':proc.exitcode,
      'samples':samples,'admissions':admissions,'rejections':rejected,
      'authority':auth,'threads_alive':{'receiver':rt.is_alive(),'controller':ct.is_alive(),'stale_probe':st.is_alive()}
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args()
    cases=[]
    if a.phase=='construction':
        schedule=[(12,'INITIAL_CLEAR'),(19,'ACTIVATE'),(27,'INVALIDATE'),(43,'TRANSIENT')]
    else:
        schedule=[(d,p) for d in DELAYS_MS for p in PROGRAMS]
    for i,(d,p) in enumerate(schedule): cases.append(run_case(d,p,i))
    out={'task':TASK,'phase':a.phase,'formal_invocations':1 if a.phase=='formal' else 0,
         'reruns':0,'replacements':0,'tuning':0,'cases':cases}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'cases':len(cases)},sort_keys=True))
if __name__=='__main__': main()
