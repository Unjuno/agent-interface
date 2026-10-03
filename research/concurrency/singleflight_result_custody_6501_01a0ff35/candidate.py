"""Actual Future result transfer with inert JSON; no policy oracle import."""
import asyncio
import copy
import hashlib
import json
from pathlib import Path


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


async def observe_case(policy,schedule,payload):
    owner_gate=asyncio.Event();b_gate=asyncio.Event();joined_gate=asyncio.Event()
    a_ready=asyncio.Event();sources=[];events=[];views={};joined=0
    original_bytes=encoded(payload);original_sha=hashlib.sha256(original_bytes).hexdigest()

    def log(kind,**fields):
        events.append({'ordinal':len(events),'kind':kind,**copy.deepcopy(fields)})

    async def read(call):
        log('read_enter',call=call)
        await owner_gate.wait()
        raw=json.loads(original_bytes);sources.append((call,raw))
        log('read_snapshot',call=call,sha256=digest(raw),snapshot=raw)
        if policy=='deep_completion':carrier=copy.deepcopy(raw)
        elif policy=='json_completion':carrier=encoded(raw)
        else:carrier=raw
        log('read_return',call=call,carrier_kind='bytes' if isinstance(carrier,bytes) else 'dict')
        return carrier

    owner_a=asyncio.create_task(read(0))
    owner_b=asyncio.create_task(read(1)) if policy=='independent' else owner_a
    tasks={'A':owner_a,'B':owner_b};carriers={}

    async def waiter(name):
        nonlocal joined
        log('waiter_join',waiter=name);joined+=1
        if joined==2:joined_gate.set()
        if name=='B':await b_gate.wait()
        carrier=await tasks[name];carriers[name]=carrier
        if policy in ('deep_delivery','deep_completion'):view=copy.deepcopy(carrier)
        elif policy=='shallow_delivery':view=copy.copy(carrier)
        elif policy=='json_completion':view=json.loads(carrier)
        else:view=carrier
        views[name]=view
        log('delivery',waiter=name,sha256=digest(view),snapshot=view)
        if name=='A':a_ready.set()
        return view

    a_task=asyncio.create_task(waiter('A'));b_task=asyncio.create_task(waiter('B'))
    await joined_gate.wait();log('producer_release');owner_gate.set()
    await a_ready.wait()
    if schedule=='caller_top':views['A']['generation']=8
    elif schedule=='caller_nested':views['A']['answer']['visible']=True
    elif schedule=='caller_list':views['A']['answer']['coordinates'].append(99)
    elif schedule=='owner_nested':dict(sources)[0]['answer']['visible']=True
    elif schedule!='none':raise ValueError('unknown schedule')
    log('post_completion_edit',schedule=schedule,a_snapshot=views['A'],
        first_owner_snapshot=dict(sources)[0],producer_done=owner_a.done())
    b_gate.set();a,b=await asyncio.gather(a_task,b_task)
    identities={'same_view_root':a is b,'same_answer':a['answer'] is b['answer'],
                'same_coordinates':a['answer']['coordinates'] is b['answer']['coordinates'],
                'same_carrier':carriers['A'] is carriers['B'],
                'a_is_first_owner':a is dict(sources)[0],
                'b_is_first_owner':b is dict(sources)[0]}
    scope_matches=b['generation']==payload['generation'] and b['target']==payload['target']
    scope_only=scope_matches and b['answer']['visible'] is True
    integrity=digest(b)==original_sha
    digest_admission=scope_only and integrity
    owners=sorted(sources)
    log('cleanup',producer_tasks_terminal=all(t.done() for t in set(tasks.values())),
        waiter_tasks_terminal=a_task.done() and b_task.done())
    return {'id':policy+'.'+schedule,'policy':policy,'schedule':schedule,
            'original_snapshot_sha256':original_sha,'read_calls':len(sources),
            'a_final':a,'b_final':b,'b_snapshot_sha256':digest(b),
            'b_snapshot_matches_original':integrity,'naive_scope_only_admission':scope_only,
            'digest_admission':digest_admission,'identity':identities,
            'first_owner_final':owners[0][1],'events':events,
            'producer_tasks_terminal':all(t.done() for t in set(tasks.values())),
            'waiter_tasks_terminal':a_task.done() and b_task.done()}


async def matrix(fixtures):
    rows=[]
    for policy in fixtures['policies']:
        for schedule in fixtures['schedules']:
            rows.append(await observe_case(policy,schedule,fixtures['payload']))
    return rows


def main():
    root=Path(__file__).resolve().parent
    raw_path=root/'evidence/raw.json'
    if raw_path.exists():raise SystemExit('original raw already exists')
    freeze_bytes=(root/'FREEZE.json').read_bytes();freeze=json.loads(freeze_bytes)
    for name,pin in freeze['source_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=pin:
            raise ValueError('frozen source mismatch:'+name)
    fixtures=json.loads((root/'fixtures.json').read_bytes())
    rows=asyncio.run(matrix(fixtures))
    raw={'schema':'result-custody-raw-v1','allocation':freeze['allocation'],
         'freeze_sha256':hashlib.sha256(freeze_bytes).hexdigest(),
         'source_sha256':freeze['source_sha256'],'runtime':freeze['runtime'],
         'fixture_sha256':hashlib.sha256((root/'fixtures.json').read_bytes()).hexdigest(),
         'rows':rows,'backend_calls':0,'input_emissions':0}
    stream=encoded(raw)+b'\n'
    if len(stream)>1048576:raise ValueError('raw exceeds frozen size cap')
    with raw_path.open('xb') as file:file.write(stream)
    print(json.dumps({'rows':len(rows),'deliveries':2*len(rows),
                      'producer_calls':sum(r['read_calls'] for r in rows),
                      'raw_sha256':hashlib.sha256(stream).hexdigest(),'bytes':len(stream)}))


if __name__=='__main__':main()
