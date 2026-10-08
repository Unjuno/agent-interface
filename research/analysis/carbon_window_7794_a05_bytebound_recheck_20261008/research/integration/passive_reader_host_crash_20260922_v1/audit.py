"""Raw-only independent auditor for #3931; never imports study or reader.

Checks original source bytes, both process responses/exits, persisted file/SQLite
bytes, cursor-prefix identity, deterministic crash cuts, and final payloads.
Does not treat off-path supervisor stdout as the host's durable response store.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def unique(pairs):
    result = {}
    for k,v in pairs:
        require(k not in result, 'duplicate JSON key')
        result[k] = v
    return result


def load(data):
    def invalid(value):
        raise ValueError('non-finite JSON constant')
    return json.loads(data, object_pairs_hook=unique, parse_constant=invalid)


def b64(s):
    require(type(s) is str, 'base64 type')
    return base64.b64decode(s, validate=True)


def exact(a,b,label):
    # Canonical encoding is type-sensitive: JSON true cannot equal integer 1.
    require(json.dumps(a,sort_keys=True,allow_nan=False) ==
            json.dumps(b,sort_keys=True,allow_nan=False), label)


def cursor(data, stream):
    return {'schema':'agent-interface/experimental-read-cursor-v1', 'stream_id':stream,
            'offset':len(data), 'prefix_sha256':hashlib.sha256(data).hexdigest(),
            'next_sequence':data.count(b'\n')+1}


def snapshot(s, policy):
    files = s['files_b64']
    if policy == 'atomic':
        require(set(files)=={'store.sqlite'},'database snapshot file set')
        con = sqlite3.connect(':memory:')
        try:
            con.deserialize(b64(files['store.sqlite']))
            tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            exact(tables,[('state',)],'database table set')
            rows = con.execute('SELECT key,value FROM state').fetchall()
            require(len(rows)==2 and {r[0] for r in rows}=={'cursor','journal'},'db state keys')
            state = {k:load(v) for k,v in rows}
            exact(con.execute('PRAGMA integrity_check').fetchall(),[('ok',)],'sqlite integrity')
        finally:
            con.close()
    else:
        require(set(files)=={'cursor.json','journal.json'},'file snapshot set')
        state = {k:load(b64(files[k+'.json'])) for k in ('cursor','journal')}
    exact(state,s['state'],'raw persisted bytes versus snapshot declaration')
    return state


def process(p, code, request, records, end_cursor, cid, phase):
    require(type(p['returncode']) is int and p['returncode']==code,'process exit '+cid+'/'+phase)
    require(b64(p['stderr_b64'])==b'','stderr '+cid+'/'+phase)
    out = b64(p['stdout_b64'])
    require(out.endswith(b'\n') and len(out.splitlines())==1,'response JSONL framing')
    response = {'schema':'agent-interface/experimental-inbox-read-v1', 'records':records,
                'tail_state':'end','problem':None,'next_cursor':end_cursor,
                'authority':'none','acknowledged':False,'input_dispatched':False}
    exact(load(out),{'request_cursor':request,'response':response},'actual reader response '+cid+'/'+phase)
    args = p['command']
    require(type(args) is list and len(args)==11,'worker command arity')
    exact(args[2:3],['worker'],'worker mode')
    exact(args[3::2],['--out','--policy','--cut','--stream'],'worker option names')
    return len(records)


def verify(raw, expected_hashes):
    require(raw['schema']=='passive-host-crash-3931-v1','schema')
    require(raw['mode'] in ('construction','formal'),'mode')
    require(raw['stop'] is None,'infrastructure stop')
    exact(raw['source_sha256'],expected_hashes,'source identities')
    require(type(raw['started_ns']) is int and type(raw['finished_ns']) is int
            and raw['finished_ns']>=raw['started_ns'],'run times')
    reps = 3 if raw['mode']=='formal' else 1
    policies = ['cursor_first','response_first','atomic']
    cuts = ['before','after_first','after_second','after_commit','normal']
    schedule = [(p,c,r) for p in policies for c in cuts for r in range(reps)]
    require(len(raw['cases'])==len(schedule),'case denominator')
    totals = {p:{'cases':0,'lost':0,'duplicates':0,'loss_cases':0,'duplicate_cases':0}
              for p in policies}
    first_exits = Counter(); recovered = 0
    for row,(policy,cut,rep) in zip(raw['cases'],schedule):
        cid = f'{policy}-{cut}-{rep}'
        exact([row['id'],row['policy'],row['cut'],row['rep']],[cid,policy,cut,rep],'schedule')
        stream = raw['allocation']+':'+cid
        require(row['stream']==stream,'stream identity')
        data = b64(row['source_b64'])
        expected_records = [{'event':'diagnostic_notification','delivery_id':f'delivery:{i}',
                             'payload':f'{stream}:item:{i}'} for i in range(1,7)]
        records = [load(x) for x in data.splitlines()]
        exact(records,expected_records,'source payload identities')
        require(data.endswith(b'\n') and data.count(b'\n')==6,'source line denominator')
        end = cursor(data,stream)
        initial = snapshot(row['initial'],policy)
        exact(initial,{'journal':[],'cursor':None},'initial state')
        code = 0 if cut=='normal' else 73
        process(row['first'],code,None,records,end,cid,'first')
        first_exits[str(code)] += 1
        # Independent transition table based only on preregistered persistence order.
        if cut=='before' or (policy=='atomic' and cut in ('after_first','after_second')):
            expected_mid = {'journal':[],'cursor':None}
        elif cut=='after_first' and policy=='cursor_first':
            expected_mid = {'journal':[],'cursor':end}
        elif cut=='after_first' and policy=='response_first':
            expected_mid = {'journal':records,'cursor':None}
        else:
            expected_mid = {'journal':records,'cursor':end}
        mid = snapshot(row['after_first'],policy)
        exact(mid,expected_mid,'post-crash durable state '+cid)
        remaining = records if mid['cursor'] is None else []
        recovered += process(row['recovery'],0,mid['cursor'],remaining,end,cid,'recovery')
        for key,actual_cut in [('first',cut),('recovery','normal')]:
            cmd = row[key]['command']
            exact([cmd[6],cmd[8],cmd[10]],[policy,actual_cut,stream],'worker command identity')
            require(Path(cmd[4]).name==cid,'worker store identity')
        final = snapshot(row['final'],policy)
        exact(final,{'journal':mid['journal']+remaining,'cursor':end},'final durable state '+cid)
        counts = Counter(r['delivery_id'] for r in final['journal'])
        lost = sum(r['delivery_id'] not in counts for r in records)
        duplicates = sum(max(0,n-1) for n in counts.values())
        expected_lost = 6 if policy=='cursor_first' and cut=='after_first' else 0
        expected_duplicates = 6 if policy=='response_first' and cut=='after_first' else 0
        exact([lost,duplicates],[expected_lost,expected_duplicates],'retention decision '+cid)
        t = totals[policy]; t['cases']+=1; t['lost']+=lost; t['duplicates']+=duplicates
        t['loss_cases']+=int(lost>0); t['duplicate_cases']+=int(duplicates>0)
    return {'decision':'PASS_HOST_PERSISTENCE_BOUNDARY_SCOPED', 'mode':raw['mode'],
            'case_count':len(schedule), 'policies':totals, 'first_process_exits':dict(first_exits),
            'recovery_exit_zero':len(schedule),'recovery_records':recovered,
            'unsafe_policy_decision':'FAIL_NOTIFICATION_RETENTION',
            'atomic_scope':'local durable retention only; not model consumption or exactly-once delivery',
            'errors':[]}


def mutation_checks(raw, hashes):
    changes = {}
    def add(name, fn):
        changed = copy.deepcopy(raw); fn(changed); changes[name] = changed
    add('missing_case',lambda r:r['cases'].pop())
    add('duplicate_case',lambda r:r['cases'].__setitem__(1,copy.deepcopy(r['cases'][0])))
    add('missing_exit',lambda r:r['cases'][0]['first'].pop('returncode'))
    add('boolean_exit',lambda r:r['cases'][0]['recovery'].__setitem__('returncode',False))
    add('payload_declaration',lambda r:r['cases'][0]['final']['state']['journal'][0].__setitem__('payload','wrong'))
    add('prefix_declaration',lambda r:r['cases'][0]['final']['state']['cursor'].__setitem__('prefix_sha256','0'*64))
    add('boolean_cursor_offset',lambda r:r['cases'][0]['final']['state']['cursor'].__setitem__('offset',True))
    add('source_digest',lambda r:r['source_sha256'].__setitem__('reader.py','0'*64))
    def grant(r):
        p = r['cases'][0]['first']; response = load(b64(p['stdout_b64']))
        response['response']['acknowledged'] = True
        p['stdout_b64'] = base64.b64encode((json.dumps(response)+'\n').encode()).decode()
    add('invented_ack',grant)
    def frame(r):
        p = r['cases'][0]['first']
        p['stdout_b64'] = base64.b64encode(b64(p['stdout_b64'])[:-1]).decode()
    add('missing_response_lf',frame)
    results = {}
    for name, changed in changes.items():
        try:
            verify(changed,hashes)
        except (ValueError,KeyError,TypeError,sqlite3.Error) as e:
            results[name] = {'rejected':True,'reason':str(e)}
        else:
            results[name] = {'rejected':False}
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw',type=Path)
    p.add_argument('--controls',action='store_true')
    args = p.parse_args()
    raw_bytes = args.raw.read_bytes(); raw = load(raw_bytes)
    here = Path(__file__).resolve().parent
    hashes = {name:hashlib.sha256((here/name).read_bytes()).hexdigest()
              for name in ('reader.py','study.py','audit.py')}
    try:
        if raw['mode']=='formal':
            freeze = load((here/'FREEZE.json').read_bytes())
            exact(hashes,freeze['source_sha256'],'frozen source')
            exact(raw['environment'],freeze['environment'],'frozen environment')
            require(raw['allocation']==freeze['allocation'],'frozen allocation')
            require(raw['started_ns']>freeze['frozen_ns'],'freeze precedes allocation')
        result = verify(raw,hashes)
        if args.controls:
            result['corruption_controls'] = mutation_checks(raw,hashes)
            require(all(x['rejected'] for x in result['corruption_controls'].values()),'mutation accepted')
        result['raw_sha256'] = hashlib.sha256(raw_bytes).hexdigest()
        code = 0
    except (ValueError,KeyError,TypeError,sqlite3.Error) as e:
        result = {'decision':'HOLD_AUDIT_INCOMPLETE','errors':[str(e)]}; code=2
    print(json.dumps(result,sort_keys=True,indent=2))
    return code


if __name__=='__main__':
    sys.exit(main())
