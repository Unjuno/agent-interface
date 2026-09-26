#!/usr/bin/env python3
import argparse, asyncio, json, time

SCHEMA='agent-interface/partial-async-readiness-v1'
PREDICATES=('P_fast_rule','P_medium_semantic','P_slow_semantic','P_eventual_temporal')
BASE_DELAY_MS={'P_fast_rule':20,'P_medium_semantic':45,'P_slow_semantic':160,'P_eventual_temporal':220}
SCENARIOS=('NORMAL','IRRELEVANT_FALSE','STALE_OBSERVATION','PRODUCER_RECONNECT','LATE_REQUIRED','REQUIRED_UNKNOWN')
ARMS=('GLOBAL_BARRIER','DEPENDENCY_READY')
NODE_DEPS=('P_fast_rule','P_medium_semantic')

def scenario_spec(name):
    vals={p:'TRUE' for p in PREDICATES}; obs={p:1 for p in PREDICATES}; prod={p:1 for p in PREDICATES}; intent={p:1 for p in PREDICATES}
    deadlines={p:500 for p in PREDICATES}; changes=[]
    if name=='IRRELEVANT_FALSE': vals['P_slow_semantic']='FALSE'
    elif name=='STALE_OBSERVATION': changes=[(30,'observation_generation',2)]
    elif name=='PRODUCER_RECONNECT': changes=[(30,'producer_generation',2)]
    elif name=='LATE_REQUIRED': deadlines['P_medium_semantic']=35
    elif name=='REQUIRED_UNKNOWN': vals['P_medium_semantic']='UNKNOWN'
    return vals,obs,prod,intent,deadlines,changes

def current_at(ms,changes):
    cur={'observation_generation':1,'producer_generation':1,'intent_version':1}
    for at,k,v in changes:
        if at <= ms: cur[k]=v
    return cur

async def producer(pred,value,delay_ms,obs_gen,prod_gen,intent_version,deadline_ms,t0,q):
    await asyncio.sleep(delay_ms/1000)
    now=(time.perf_counter_ns()-t0)/1e6
    await q.put({'predicate_id':pred,'value':value,'observation_generation':obs_gen,'producer_generation':prod_gen,
                 'intent_version':intent_version,'evaluated_ms':now,'decision_deadline_ms':deadline_ms})

def classify_required(results,current):
    for p in NODE_DEPS:
        if p not in results: return None,None
        r=results[p]
        if r['observation_generation'] != current['observation_generation']: return 'YIELD_STALE',p
        if r['producer_generation'] != current['producer_generation']: return 'YIELD_PRODUCER',p
        if r['intent_version'] != current['intent_version']: return 'YIELD_INTENT',p
        if r['evaluated_ms'] > r['decision_deadline_ms']: return 'YIELD_LATE',p
        if r['value']=='UNKNOWN': return 'YIELD_UNKNOWN',p
        if r['value']!='TRUE': return 'YIELD_FALSE',p
    return 'READY_A',None

async def run_case_async(arm,scenario,rep):
    vals,obs,prod,intent,deadlines,changes=scenario_spec(scenario)
    q=asyncio.Queue(); t0=time.perf_counter_ns(); tasks=[]
    for p in PREDICATES:
        tasks.append(asyncio.create_task(producer(p,vals[p],BASE_DELAY_MS[p],obs[p],prod[p],intent[p],deadlines[p],t0,q)))
    results={}; completed=[]; decision=None; decision_pred=None; decision_ms=None
    while len(completed)<len(PREDICATES):
        r=await asyncio.wait_for(q.get(),timeout=1)
        results[r['predicate_id']]=r; completed.append(r['predicate_id'])
        cur=current_at(r['evaluated_ms'],changes)
        if arm=='DEPENDENCY_READY' and decision is None:
            c,p=classify_required(results,cur)
            if c is not None: decision,decision_pred,decision_ms=c,p,r['evaluated_ms']
        if arm=='GLOBAL_BARRIER' and len(completed)==len(PREDICATES):
            barrier_ms=max(x['evaluated_ms'] for x in results.values())
            decision,decision_pred=classify_required(results,current_at(barrier_ms,changes)); decision_ms=barrier_ms
    await asyncio.gather(*tasks)
    return {'schema':SCHEMA,'arm':arm,'scenario':scenario,'rep':rep,'decision':decision,'decision_predicate':decision_pred,
            'decision_ms':decision_ms,'completion_order':completed,'results':results,'final_current':current_at(max(x['evaluated_ms'] for x in results.values()),changes),
            'worker_status':['done']*4,'authority':'none','input_dispatched':False}

def expected(s):
    return {'NORMAL':'READY_A','IRRELEVANT_FALSE':'READY_A','STALE_OBSERVATION':'YIELD_STALE','PRODUCER_RECONNECT':'YIELD_PRODUCER',
            'LATE_REQUIRED':'YIELD_LATE','REQUIRED_UNKNOWN':'YIELD_UNKNOWN'}[s]

async def run_all(mode,reps):
    rows=[]
    for rep in range(1,reps+1):
        for s in SCENARIOS:
            for arm in ARMS:
                rows.append(await run_case_async(arm,s,rep))
    return {'schema':SCHEMA,'mode':mode,'rows':rows,'expected':{s:expected(s) for s in SCENARIOS},'formal_reruns':0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('--reps',type=int); ap.add_argument('--out',required=True); a=ap.parse_args()
    reps=a.reps if a.reps is not None else (1 if a.mode=='construction' else 3)
    obj=asyncio.run(run_all(a.mode,reps))
    with open(a.out,'w',encoding='utf-8') as f: json.dump(obj,f,sort_keys=True,indent=2); f.write('\n')
    return 0
if __name__=='__main__': raise SystemExit(main())
