"""Raw-only independently declared outcome/event oracle. Does not import candidate."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

ARMS=('independent','direct','shield','shield_refcount')
CASES=('stable','cancel_first','cancel_last','cancel_all','generation_change','owner_failure')
EXPECTED=set(itertools.product((2,3),CASES,ARMS))
PAYLOAD=hashlib.sha256(b'descriptive-read:surface-A:generation-1').hexdigest()

def check(raw):
    errors=[]
    try:
        rows=raw['rows']
        if raw['schema']!='asyncio-singleflight-cancellation-v1' or type(rows) is not list:
            return ['schema']
        keys=[(r['callers'],r['scenario'],r['policy']) for r in rows]
        if len(keys)!=48 or len(set(keys))!=48 or set(keys)!=EXPECTED:
            return ['denominator']
        for row in rows:
            n,case,arm=row['callers'],row['scenario'],row['policy']
            label=f'{n}/{case}/{arm}'
            def require(cond,reason):
                if not cond: errors.append(label+':'+reason)
            require(type(n) is int, 'caller type')
            events=row['events']
            require(type(events) is list and all(type(e['seq']) is int and e['seq']==i+1 for i,e in enumerate(events)), 'event sequence')
            kinds=[e['kind'] for e in events]
            producers=['p'+str(i) for i in range(n if arm=='independent' else 1)]
            starts=[e['actor'] for e in events if e['kind']=='producer_start']
            exits=[e['actor'] for e in events if e['kind']=='producer_exit']
            require(sorted(starts)==sorted(producers) and sorted(exits)==sorted(producers),'producer start/exit')
            barrier=[e['seq'] for e in events if e['kind']=='barrier_ready']
            require(len(barrier)==1 and all(e['seq']<barrier[0] for e in events if e['kind'] in ('producer_start','waiter_start')), 'barrier')
            cancelled=([0] if case=='cancel_first' else [n-1] if case=='cancel_last' else list(range(n)) if case=='cancel_all' else [])
            requests=[e['caller'] for e in events if e['kind']=='cancel_request']
            require(requests==cancelled, 'offered cancellation')
            require(all(e['seq']>barrier[0] for e in events if e['kind']=='cancel_request'),'cancel barrier order')
            outcomes=row['outcomes']
            require(len(outcomes)==n and [o['caller'] for o in outcomes]==list(range(n)), 'waiter denominator')
            for i,out in enumerate(outcomes):
                expected=('CANCELLED' if i in cancelled or (cancelled and arm=='direct') else
                          'STALE' if case=='generation_change' else 'OWNER_FAILED' if case=='owner_failure' else 'DELIVERED')
                require(out['status']==expected,'terminal '+str(i))
                actor='w'+str(i)
                terminal=[e for e in events if e['actor']==actor and e['kind'] in ('waiter_cancelled','waiter_result','waiter_error')]
                require(len(terminal)==1,'one terminal '+actor)
                if len(terminal)!=1: continue
                e=terminal[0]
                if expected in ('DELIVERED','STALE'):
                    require(e['kind']=='waiter_result' and e['status']==expected and
                            type(out['generation']) is int and out['generation']==1 and out['payload_sha256']==PAYLOAD,
                            'result identity '+actor)
                    require(type(e['current_generation']) is int and e['current_generation']==(2 if case=='generation_change' else 1),'current generation')
                    returns=[p for p in events if p['kind']=='producer_return' and p['actor']==('p'+str(i) if arm=='independent' else 'p0')]
                    require(len(returns)==1 and returns[0]['seq']<e['seq'] and type(returns[0]['generation']) is int and returns[0]['generation']==1 and returns[0]['payload_sha256']==PAYLOAD,'return-before-delivery')
                    if case=='generation_change':
                        changes=[p for p in events if p['kind']=='generation_change']
                        require(len(changes)==1 and changes[0]['seq']<e['seq'] and type(changes[0]['generation']) is int and changes[0]['generation']==2,'invalidation-before-delivery')
                else:
                    require(out['generation'] is None and out['payload_sha256'] is None,'non-delivery payload')
                    require(e['kind']==('waiter_cancelled' if expected=='CANCELLED' else 'waiter_error'),'terminal kind')
                require(sum(e['actor']==actor and e['kind']=='waiter_start' for e in events)==1 and
                        sum(e['actor']==actor and e['kind']=='waiter_detach' for e in events)==1,'waiter lifecycle')
            before=row['before_cleanup'];after=row['after_cleanup']
            require(len(before)==len(after)==len(producers),'producer state denominator')
            for states in (before,after):
                require([s['producer'] for s in states]==producers and all(type(s['done']) is bool and type(s['cancelled']) is bool for s in states),'producer state types')
            require(all(s['done'] for s in after),'bounded cleanup')
            pending=sum(not s['done'] for s in before)
            require(pending==(1 if case=='cancel_all' and arm=='shield' else 0),'pending ownership')
            require(kinds.count('cleanup_cancel')==pending,'cleanup count')
            require(kinds.count('last_waiter_cancel')==(1 if case=='cancel_all' and arm=='shield_refcount' else 0),'last-waiter cleanup')
    except (KeyError,TypeError,ValueError,IndexError) as exc:
        errors.append('malformed:'+type(exc).__name__)
    return errors

def mutations(raw):
    altered=[]
    def add(name,edit):
        value=copy.deepcopy(raw);edit(value);altered.append((name,value))
    add('drop-row',lambda d:d['rows'].pop())
    add('duplicate-row',lambda d:d['rows'].__setitem__(1,copy.deepcopy(d['rows'][0])))
    index=next(i for i,r in enumerate(raw['rows']) if r['scenario']=='cancel_first' and r['policy']=='shield')
    add('cancelled-delivery',lambda d:d['rows'][index]['outcomes'][0].__setitem__('status','DELIVERED'))
    add('generation',lambda d:d['rows'][0]['outcomes'][0].__setitem__('generation',2))
    add('producer-start',lambda d:d['rows'][0].__setitem__('events',[e for e in d['rows'][0]['events'] if e['kind']!='producer_start']))
    add('sequence-bool',lambda d:d['rows'][0]['events'][0].__setitem__('seq',True))
    add('cleanup-leak',lambda d:d['rows'][0]['after_cleanup'][0].__setitem__('done',False))
    add('payload',lambda d:d['rows'][0]['outcomes'][0].__setitem__('payload_sha256','0'*64))
    return [(name,bool(check(value))) for name,value in altered]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('raw');parser.add_argument('--output',required=True)
    args=parser.parse_args();blob=Path(args.raw).read_bytes();raw=json.loads(blob)
    errors=check(raw);controls=mutations(raw) if not errors else []
    result=dict(status='PASS_ASYNCIO_BOUNDARY_SCOPED' if not errors and len(controls)==8 and all(v for _,v in controls) else 'FAIL_AUDIT',
                raw_sha256=hashlib.sha256(blob).hexdigest(),rows=len(raw.get('rows',[])),errors=errors,corruption_controls=controls)
    with Path(args.output).open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(result,sort_keys=True))
    return int(result['status']!='PASS_ASYNCIO_BOUNDARY_SCOPED')

if __name__=='__main__':raise SystemExit(main())
