import multiprocessing as mp, time, json
CLEAR='CLEAR_PROGRESS'; WATCH='UNCERTAIN_TRANSIENT'; HARD='HARD_INVALIDATION'
SEL={CLEAR:'ADVANCE',WATCH:'WATCH',HARD:'YIELD'}
DELAYS=[12,19,27,43,71]
PROGS={'INITIAL_CLEAR':[(0,CLEAR)],'ACTIVATE':[(0,WATCH),(8,CLEAR)],'INVALIDATE':[(0,CLEAR),(8,HARD)],'TRANSIENT':[(0,CLEAR),(8,WATCH),(20,CLEAR)]}
def child(conn,delay_ms):
    time.sleep(delay_ms/1000); conn.send(time.perf_counter_ns()); conn.close()
def state_at(prog,ms):
    s=prog[0][1]
    for t,x in prog:
        if ms>=t:s=x
    return s
def case(delay,name):
    parent,ch=mp.Pipe(False); p=mp.Process(target=child,args=(ch,delay)); p.start()
    start=time.perf_counter_ns(); recv_ns=None; admissions=[]; stale_rejected=False; prepared=None; next_sample=0
    while True:
        now=time.perf_counter_ns(); ms=(now-start)/1e6
        if parent.poll(): parent.recv(); recv_ns=time.perf_counter_ns()
        if recv_ns is None and ms>=next_sample:
            st=state_at(PROGS[name],next_sample); d=SEL[st]
            if d=='ADVANCE': admissions.append({'sample_ms':next_sample,'commit_ns':time.perf_counter_ns(),'state':st})
            next_sample+=5
        if prepared is None and ms>=max(0,delay-2): prepared={'prepared_ns':time.perf_counter_ns()}
        if prepared is not None and 'done' not in prepared and recv_ns is not None:
            time.sleep(.001); commit=time.perf_counter_ns(); prepared['done']=commit
            if commit>=recv_ns: stale_rejected=True
        if recv_ns is not None and prepared and 'done' in prepared: break
        if ms>delay+30: break
        time.sleep(.0002)
    p.join(1)
    post=sum(a['commit_ns']>=recv_ns for a in admissions) if recv_ns else -1
    return {'delay_ms':delay,'program':name,'child_exit':p.exitcode,'recv_ns':recv_ns,'post_return_admissions':post,'stale_rejected':stale_rejected,'pre_return_advance':sum(a['commit_ns']<recv_ns for a in admissions) if recv_ns else 0}
def main():
    rows=[case(d,n) for d in DELAYS for n in PROGS]; errors=[]
    for r in rows:
        if r['child_exit']!=0 or r['recv_ns'] is None: errors.append('child')
        if r['post_return_admissions']!=0: errors.append('post')
        if not r['stale_rejected']: errors.append('stale')
    print(json.dumps({'rows':rows,'errors':errors,'decision':'PASS_T2_ASYNC_RETURN_AUTHORITY_PREFLIGHT_SCOPED' if not errors else 'FAIL_ASYNC_RETURN_AUTHORITY'},indent=2))
if __name__=='__main__': main()
