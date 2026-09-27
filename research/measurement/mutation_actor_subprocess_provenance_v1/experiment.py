import os, json, socket, tempfile, time, random, hashlib
from collections import Counter

ACTORS={"THIS_INTENT","THIS_SESSION_OTHER_INTENT","EXTERNAL_PROCESS","HUMAN","OS","UNKNOWN"}
EXT={"THIS_SESSION_OTHER_INTENT","EXTERNAL_PROCESS","HUMAN","OS"}
FIELDS=("session_id","intent_id","action_id","target_id","delta_kind")

def classify(r):
    def okid(x): return isinstance(x,str) and x and all(c.isalnum() or c in '_-:.' for c in x)
    if not isinstance(r,dict) or any(not okid(r.get(k)) for k in FIELDS): return out('UNATTRIBUTED','UNKNOWN',True,True)
    if r.get('mutation') is False: return out('NO_MUTATION','UNKNOWN',False,False)
    if r.get('mutation') is not True: return out('UNATTRIBUTED','UNKNOWN',True,True)
    a,m=r.get('action_time_ns'),r.get('mutation_time_ns')
    if type(a) is not int or type(m) is not int or m<a: return out('UNATTRIBUTED','UNKNOWN',True,True)
    cur=tuple(r.get(k) for k in FIELDS); supported=set(); malformed=False
    for w in r.get('witnesses',[]):
        if not isinstance(w,dict): malformed=True; continue
        cls=w.get('actor_class'); t=w.get('time_ns')
        if cls not in ACTORS: malformed=True; continue
        if type(t) is not int or not (a<=t<=m): continue
        if cls=='THIS_INTENT':
            if tuple(w.get(k) for k in FIELDS)==cur: supported.add(cls)
        elif cls=='THIS_SESSION_OTHER_INTENT':
            if w.get('session_id')==r['session_id'] and w.get('target_id')==r['target_id'] and w.get('delta_kind')==r['delta_kind'] and (w.get('intent_id')!=r['intent_id'] or w.get('action_id')!=r['action_id']): supported.add(cls)
        elif cls in {'EXTERNAL_PROCESS','HUMAN','OS'}:
            if w.get('target_id')==r['target_id'] and w.get('delta_kind')==r['delta_kind']: supported.add(cls)
    if malformed: supported.add('UNKNOWN')
    concrete={x for x in supported if x!='UNKNOWN'}
    if len(concrete)==1 and 'UNKNOWN' not in supported:
        cls=next(iter(concrete)); return out('SELF_CONFIRMED' if cls=='THIS_INTENT' else 'EXTERNAL_CONFIRMED',cls,cls!='THIS_INTENT',False)
    return out('UNATTRIBUTED','UNKNOWN',True,malformed)

def out(state,actor,invalidate,malformed):
    return {'state':state,'actor_class':actor,'invalidate':invalidate,'grants_authority':False,'verifies_task_success':False,'malformed':malformed}

def temporal(r):
    if r.get('mutation') is not True: return 'NO_MUTATION' if r.get('mutation') is False else 'UNATTRIBUTED'
    d=r['mutation_time_ns']-r['action_time_ns']
    return 'SELF_CONFIRMED' if 0<=d<=500_000_000 else 'UNATTRIBUTED'

def make_case(i,kind):
    a=time.monotonic_ns(); r={'case_id':i,'session_id':f's{i%17}','intent_id':f'i{i%29}','action_id':f'a{i}','target_id':f't{i%43}','delta_kind':['VALUE','GEOMETRY','VISIBILITY'][i%3],'action_time_ns':a,'mutation_time_ns':a+1,'mutation':kind!='no_mutation','witnesses':[]}
    base={k:r[k] for k in FIELDS}
    if kind=='self': w=base|{'actor_class':'THIS_INTENT'}
    elif kind=='other_intent': w={'actor_class':'THIS_SESSION_OTHER_INTENT','session_id':r['session_id'],'intent_id':r['intent_id']+'x','action_id':r['action_id']+'x','target_id':r['target_id'],'delta_kind':r['delta_kind']}
    elif kind in {'external','human','os'}: w={'actor_class':{'external':'EXTERNAL_PROCESS','human':'HUMAN','os':'OS'}[kind],'target_id':r['target_id'],'delta_kind':r['delta_kind']}
    elif kind=='mismatch': w=base|{'actor_class':'THIS_INTENT','target_id':r['target_id']+'x'}
    elif kind=='conflict':
        return r,[base|{'actor_class':'THIS_INTENT'},{'actor_class':'HUMAN','target_id':r['target_id'],'delta_kind':r['delta_kind']}]
    else: return r,[]
    return r,[w]

def child_emit(payload,transport,endpoint):
    payload['emitter_pid']=os.getpid(); payload['time_ns']=time.monotonic_ns()
    data=(json.dumps(payload,sort_keys=True)+'\n').encode()
    if transport=='jsonl':
        fd=os.open(endpoint,os.O_WRONLY|os.O_APPEND); os.write(fd,data); os.fsync(fd); os.close(fd)
    else:
        s=socket.socket(fileno=endpoint); s.sendall(data); s.close()

def one_case(i,kind,transport,tmpdir):
    r,ws=make_case(i,kind); child_pids=[]; received=[]
    for j,w in enumerate(ws):
        if transport=='jsonl':
            path=os.path.join(tmpdir,f'{i}_{j}.jsonl'); open(path,'wb').close(); pid=os.fork()
            if pid==0: child_emit(w,'jsonl',path); os._exit(0)
            child_pids.append(pid); os.waitpid(pid,0); raw=open(path,'rb').read(); received.append(json.loads(raw))
        else:
            p,c=socket.socketpair(); pid=os.fork()
            if pid==0:
                p.close(); child_emit(w,'socket',c.detach()); os._exit(0)
            c.close(); child_pids.append(pid); buf=b''
            while not buf.endswith(b'\n'): buf+=p.recv(65536)
            p.close(); os.waitpid(pid,0); received.append(json.loads(buf))
    now=time.monotonic_ns(); r['mutation_time_ns']=now; r['witnesses']=received
    return r,child_pids

def run(n=1000,seed=122820260918001):
    kinds=['self','other_intent','external','human','os','unknown','conflict','mismatch','no_mutation']
    rng=random.Random(seed); counts=Counter(); actors=Counter(); mism=0; false_self=0; temp_false=0; cleanup=0; total_children=0; dig=hashlib.sha256()
    with tempfile.TemporaryDirectory() as td:
      for transport in ('jsonl','socket'):
        for j in range(n):
            kind=kinds[j%len(kinds)]; r,pids=one_case(j+(0 if transport=='jsonl' else n),kind,transport,td)
            exp=oracle(r); got=classify(r)
            if got!=exp: mism+=1
            if got['state']=='SELF_CONFIRMED' and kind!='self': false_self+=1
            if temporal(r)=='SELF_CONFIRMED' and kind not in {'self','no_mutation'}: temp_false+=1
            counts[(transport,got['state'])]+=1; actors[got['actor_class']]+=1
            total_children+=len(pids); cleanup+=len(pids)
            dig.update(json.dumps(r,sort_keys=True,separators=(',',':')).encode()); dig.update(b'\n')
    return {'records':2*n,'fresh_child_processes':total_children,'child_cleanup':cleanup,'mismatches':mism,'false_self_credit':false_self,'temporal_false_self_credit':temp_false,'states':{str(k):v for k,v in sorted(counts.items(),key=lambda x:str(x[0]))},'actors':dict(sorted(actors.items())),'authority_promotions':0,'task_success_promotions':0,'record_sha256':dig.hexdigest()}

def oracle(r):
    # Independently reduced actor-evidence intersection.
    if r.get('mutation') is False: return out('NO_MUTATION','UNKNOWN',False,False)
    if r.get('mutation') is not True: return out('UNATTRIBUTED','UNKNOWN',True,True)
    claims=[]
    for w in r.get('witnesses',[]):
        cls=w.get('actor_class')
        if cls=='THIS_INTENT' and all(w.get(k)==r.get(k) for k in FIELDS): claims.append(cls)
        elif cls=='THIS_SESSION_OTHER_INTENT' and w.get('session_id')==r['session_id'] and w.get('target_id')==r['target_id'] and w.get('delta_kind')==r['delta_kind'] and (w.get('intent_id')!=r['intent_id'] or w.get('action_id')!=r['action_id']): claims.append(cls)
        elif cls in {'EXTERNAL_PROCESS','HUMAN','OS'} and w.get('target_id')==r['target_id'] and w.get('delta_kind')==r['delta_kind']: claims.append(cls)
    s=set(claims)
    if len(s)!=1: return out('UNATTRIBUTED','UNKNOWN',True,False)
    a=next(iter(s)); return out('SELF_CONFIRMED' if a=='THIS_INTENT' else 'EXTERNAL_CONFIRMED',a,a!='THIS_INTENT',False)

if __name__=='__main__':
    import sys
    n=int(sys.argv[1]) if len(sys.argv)>1 else 1000
    print(json.dumps(run(n),sort_keys=True))
