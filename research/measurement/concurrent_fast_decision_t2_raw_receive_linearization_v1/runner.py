from __future__ import annotations
import argparse, json, multiprocessing as mp, os, random, threading, time
from pathlib import Path
from candidate import select, CLEAR, WATCH, HARD

TASK='CONCURRENT-FAST-DECISION-T2-RAW-RECEIVE-LINEARIZATION-A10-20260918-013'
SAMPLE_NS=5_000_000
FORMAL_DELAYS_MS=(12,19,27,43,71)
PROGRAMS=('INITIAL_CLEAR','ACTIVATE','INVALIDATE','TRANSIENT')


def frontier_child(conn, delay_ns):
    start=time.perf_counter_ns(); target=start+delay_ns
    while True:
        now=time.perf_counter_ns(); rem=target-now
        if rem<=0: break
        time.sleep(min(rem/1e9,0.0005))
    send_ns=time.perf_counter_ns()
    conn.send({'kind':'RETURN','child_pid':os.getpid(),'child_send_ns':send_ns})
    conn.close()


def state_at(program, elapsed_ns, delay_ns):
    if program=='INITIAL_CLEAR': return CLEAR
    if program=='ACTIVATE': return CLEAR if elapsed_ns >= int(delay_ns*0.30) else WATCH
    if program=='INVALIDATE': return HARD if elapsed_ns >= int(delay_ns*0.45) else CLEAR
    if program=='TRANSIENT':
        if elapsed_ns < int(delay_ns*0.25): return CLEAR
        if elapsed_ns < int(delay_ns*0.55): return WATCH
        return CLEAR
    raise ValueError(program)


def run_case(mode, delay_ms, program, case_idx, post_recv_pause_ns=2_000_000, poll_sleep_ns=100_000):
    assert mode in ('PREDECESSOR_POSTRECV_LOCK','POLL_RECV_UNDER_LOCK')
    delay_ns=int(delay_ms*1_000_000)
    parent, child=mp.Pipe(duplex=False)
    proc=mp.Process(target=frontier_child,args=(child,delay_ns))
    lock=threading.Lock(); stop=threading.Event(); recv_event=threading.Event()
    auth={'generation':1,'closed':False,'raw_recv_return_ns':None,'close_ns':None,'close_count':0}
    samples=[]; admissions=[]; rejections=[]
    start_ns=time.perf_counter_ns(); proc.start(); child.close()

    def finish_receive_locked(msg):
        # Caller holds authority lock. Actual recv return has already occurred.
        raw=time.perf_counter_ns()
        auth['raw_recv_return_ns']=raw
        recv_event.set()
        if post_recv_pause_ns:
            time.sleep(post_recv_pause_ns/1e9)
        auth['closed']=True
        auth['generation']+=1
        auth['close_count']+=1
        auth['close_ns']=time.perf_counter_ns()
        msg['parent_raw_recv_return_ns']=raw
        auth['frontier_message']=msg

    def receiver():
        if mode=='PREDECESSOR_POSTRECV_LOCK':
            msg=parent.recv()
            raw=time.perf_counter_ns()
            auth['raw_recv_return_ns']=raw
            recv_event.set()
            if post_recv_pause_ns:
                time.sleep(post_recv_pause_ns/1e9)
            with lock:
                auth['closed']=True
                auth['generation']+=1
                auth['close_count']+=1
                auth['close_ns']=time.perf_counter_ns()
                msg['parent_raw_recv_return_ns']=raw
                auth['frontier_message']=msg
        else:
            while True:
                with lock:
                    if parent.poll(0):
                        msg=parent.recv()
                        finish_receive_locked(msg)
                        break
                time.sleep(poll_sleep_ns/1e9)
        stop.set()

    def commit(kind, prepared_generation, sample_idx=None, prepared_ns=None):
        attempt_begin=time.perf_counter_ns()
        with lock:
            commit_ns=time.perf_counter_ns()
            ok=(not auth['closed'] and prepared_generation==auth['generation'])
            row={'kind':kind,'sample_idx':sample_idx,'prepared_generation':prepared_generation,
                 'prepared_ns':prepared_ns,'attempt_begin_ns':attempt_begin,'commit_ns':commit_ns,
                 'admitted':ok,'generation_at_commit':auth['generation'],'closed_at_commit':auth['closed']}
            (admissions if ok else rejections).append(row)
            return ok

    def controller():
        prev=None; idx=0; next_tick=start_ns
        while not stop.is_set():
            now=time.perf_counter_ns()
            if now<next_tick:
                time.sleep(min((next_tick-now)/1e9,0.00025)); continue
            elapsed=now-start_ns; st=state_at(program,elapsed,delay_ns); disp=select(st)
            with lock: gen=auth['generation']
            samples.append({'idx':idx,'sample_ns':now,'elapsed_ns':elapsed,'state':st,'disposition':disp,'generation':gen})
            if disp=='ADVANCE' and prev!=CLEAR:
                commit('lane',gen,idx,now)
            prev=st
            if disp=='YIELD': break
            idx+=1; next_tick=start_ns+idx*SAMPLE_NS

    def boundary_probe():
        # Prepare under generation 1 before the return. Attempt immediately after actual recv return.
        with lock: gen=auth['generation']
        prepared_ns=time.perf_counter_ns()
        if not recv_event.wait(timeout=2):
            rejections.append({'kind':'boundary_probe','prepared_generation':gen,'prepared_ns':prepared_ns,
                'attempt_begin_ns':time.perf_counter_ns(),'commit_ns':time.perf_counter_ns(),'admitted':False,
                'generation_at_commit':auth['generation'],'closed_at_commit':auth['closed'],'probe_error':'recv_not_observed'})
            return
        commit('boundary_probe',gen,None,prepared_ns)

    rt=threading.Thread(target=receiver,name='frontier-receiver')
    ct=threading.Thread(target=controller,name='local-controller')
    bt=threading.Thread(target=boundary_probe,name='boundary-probe')
    rt.start(); ct.start(); bt.start()
    rt.join(timeout=3); ct.join(timeout=3); bt.join(timeout=3); proc.join(timeout=3)
    end_ns=time.perf_counter_ns()
    return {
      'case_id':f'{mode}-{delay_ms}ms-{program}-{case_idx}','mode':mode,'delay_ms':delay_ms,'program':program,
      'post_recv_pause_ns':post_recv_pause_ns,'poll_sleep_ns':poll_sleep_ns,'start_ns':start_ns,'end_ns':end_ns,
      'sample_period_ns':SAMPLE_NS,'frontier_child_pid':getattr(proc,'pid',None),'child_exitcode':proc.exitcode,
      'samples':samples,'admissions':admissions,'rejections':rejections,'authority':auth,
      'threads_alive':{'receiver':rt.is_alive(),'controller':ct.is_alive(),'boundary_probe':bt.is_alive()}
    }


def schedule_for(phase, n, seed):
    if phase=='construction':
        return [(12,'INITIAL_CLEAR'),(19,'ACTIVATE'),(27,'INVALIDATE'),(43,'TRANSIENT')]
    if phase=='formal':
        return [(d,p) for d in FORMAL_DELAYS_MS for p in PROGRAMS]
    rng=random.Random(seed); out=[]
    for _ in range(n):
        d=rng.uniform(6.0,35.0); p=rng.choice(PROGRAMS); out.append((d,p))
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--phase',choices=['construction','stress','formal'],required=True)
    ap.add_argument('--out',required=True); ap.add_argument('--cases',type=int,default=500); ap.add_argument('--seed',type=int,default=146520260918013)
    a=ap.parse_args()
    schedule=schedule_for(a.phase,a.cases,a.seed)
    pred=[]; cand=[]
    if a.phase=='construction':
        # One explicit predecessor discriminator is enough; candidate gets the four inherited state programs.
        pred=[run_case('PREDECESSOR_POSTRECV_LOCK',12,'INITIAL_CLEAR',0)]
    for i,(d,p) in enumerate(schedule):
        pause=2_000_000 if a.phase=='construction' else 250_000
        jitter_poll=100_000 if a.phase!='stress' else 50_000 + (i%7)*25_000
        cand.append(run_case('POLL_RECV_UNDER_LOCK',d,p,i,post_recv_pause_ns=pause,poll_sleep_ns=jitter_poll))
    out={'task':TASK,'phase':a.phase,'seed':a.seed,'formal_invocations':1 if a.phase=='formal' else 0,
         'reruns':0,'replacements':0,'tuning':0,'predecessor_discriminator':pred,'candidate_cases':cand}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'predecessor_cases':len(pred),'candidate_cases':len(cand)},sort_keys=True))

if __name__=='__main__': main()
