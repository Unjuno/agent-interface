"""Independent raw-only reconstruction. Does not import runner, receiver or policy."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import sqlite3

SCENARIOS = ['RETAINED_APPLIED','RETIRED_APPLIED','RETIRED_NEVER_ACCEPTED',
             'RETIRED_CHANGED_PAYLOAD','FRESH_NEW_INTENT','RETAINED_CHANGED_PAYLOAD',
             'WRONG_SESSION','BOOLEAN_EPOCH']
ARMS = ['LOOKUP_ONLY','COVERAGE_AWARE']
BASE = {'session':'fixture-session','resource':'counter','epoch':7,'op_id':'work-A','delta':1}

def digest(b):
    return hashlib.sha256(b).hexdigest()

def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(',',':'))

def same(a,b):
    return canonical(a) == canonical(b)

def tables(blob):
    con = sqlite3.connect(':memory:')
    con.deserialize(blob)
    if con.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
        raise ValueError('database corrupt')
    names = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    if names != [('effects',),('meta',),('receipts',)]:
        raise ValueError('database table set')
    result = {n:[list(r) for r in con.execute('SELECT * FROM '+n+' ORDER BY 1,2')]
              for n in ('meta','receipts','effects')}
    con.close()
    return result

def validate(rows, repetitions):
    errors = []
    def ck(condition,label):
        if not condition:
            errors.append(label)
    ids = [f'r{r}-{s}-{a}' for r in range(repetitions) for s in SCENARIOS
           for a in (ARMS if r%2 == 0 else list(reversed(ARMS)))]
    ck([r.get('case_id') for r in rows] == ids,'case schedule/cardinality')
    for row in rows:
        cid = row.get('case_id','?')
        try:
            s,a,r = row['scenario'],row['policy'],row['repetition']
            ck(s in SCENARIOS and a in ARMS and type(r) is int and 0 <= r < repetitions,cid+':case types')
            ck(cid == f'r{r}-{s}-{a}' and row['status'] == 'COMPLETE',cid+':case identity/status')
            request = dict(BASE)
            if s.endswith('CHANGED_PAYLOAD'): request['delta'] = 2
            if s == 'FRESH_NEW_INTENT': request.update(epoch=8,op_id='work-B',delta=2)
            if s == 'WRONG_SESSION': request['session']='foreign-session'
            if s == 'BOOLEAN_EPOCH': request['epoch']=True
            ck(same(row['request'],request),cid+':request')
            retired = s.startswith('RETIRED_') or s == 'FRESH_NEW_INTENT'
            prior = s != 'RETIRED_NEVER_ACCEPTED'
            original = [1,'fixture-session','counter',7,'work-A',1]
            pre_effects = [original] if prior else []
            pre_receipts = [[7,'work-A',json.dumps(BASE,sort_keys=True),'COMPLETED']] if prior and not retired else []
            pre_meta = [[1,'fixture-session','counter',8 if retired else 7]]
            for name in ('pre','post_query','final'):
                snap = row[name]
                blob = base64.b64decode(snap['db_b64'],validate=True)
                ck(0 < len(blob) <= 131072,cid+':database size')
                ck(digest(blob) == snap['db_sha256'],cid+':database digest '+name)
                actual = tables(blob)
                ck(all(same(actual[k],snap[k]) for k in actual),cid+':database fields '+name)
            ck(same(row['pre']['meta'],pre_meta) and same(row['pre']['effects'],pre_effects)
               and same(row['pre']['receipts'],pre_receipts),cid+':prehistory')
            ck(same(row['pre'],row['post_query']),cid+':query mutated store')
            matching = [z for z in pre_receipts if z[0] == request['epoch'] and z[1] == request['op_id']]
            receipt = None if not matching else {'request':json.loads(matching[0][2]),'status':matching[0][3]}
            packet = {'request':request,'scope':{'session':'fixture-session','resource':'counter'},
                      'coverage_epoch':8 if retired else 7,'receipt':receipt,
                      'authority':'none','input_dispatched':False}
            ck(same(row['packet'],packet),cid+':packet reconstruction')
            if s == 'RETAINED_APPLIED': status='COMPLETED'
            elif s == 'RETAINED_CHANGED_PAYLOAD': status='CONFLICT_CONTENT'
            elif s == 'WRONG_SESSION': status='REFUSE_SCOPE'
            elif s == 'BOOLEAN_EPOCH': status='REFUSE_REQUEST'
            elif retired and s != 'FRESH_NEW_INTENT' and a == 'COVERAGE_AWARE': status='OUTCOME_UNKNOWN_RETIRED'
            else: status='NOT_FOUND_CURRENT'
            execute = status == 'NOT_FOUND_CURRENT'
            ck(same(row['decision'],{'status':status,'submit':execute,'authority':'none','input_dispatched':False}),cid+':decision')
            ck(same(row['recovery'],{'status':'APPLIED'} if execute else None),cid+':recovery')
            final_effects = copy.deepcopy(pre_effects)
            final_receipts = copy.deepcopy(pre_receipts)
            if execute:
                final_effects.append([len(pre_effects)+1,request['session'],request['resource'],request['epoch'],request['op_id'],request['delta']])
                final_receipts.append([request['epoch'],request['op_id'],json.dumps(request,sort_keys=True),'COMPLETED'])
            ck(same(row['final']['effects'],final_effects) and same(row['final']['receipts'],final_receipts)
               and same(row['final']['meta'],pre_meta),cid+':final effects/receipt/meta')
            if not execute: ck(same(row['pre'],row['final']),cid+':unexpected store change')
            commands = [{'op':'init'}]
            if prior: commands.append({'op':'execute','request':BASE})
            if retired: commands.append({'op':'retire'})
            commands.append({'op':'query','request':request})
            if execute: commands.append({'op':'execute','request':request})
            ck(same([json.loads(c['stdin']) for c in row['calls']],commands),cid+':command schedule')
            for c,command in zip(row['calls'],commands):
                ck(type(c['returncode']) is int and c['returncode']==0 and c['timeout'] is False
                   and c['stderr']=='',cid+':process exit')
                ck(type(c['pid']) is int and c['pid']>0,cid+':process pid')
                ck(type(c['start_ns']) is int and type(c['end_ns']) is int and c['end_ns']>=c['start_ns'],cid+':clock order')
                ck(Path(c['argv'][-2]).name=='receiver.py' and Path(c['argv'][-1]).parent.name==cid,cid+':argv identity')
                wire = json.loads(c['stdout'])
                ck(wire['pid']==c['pid'] and wire['operation']==command['op'],cid+':wire identity')
                if command['op']=='query':
                    ck(same(wire['result'],packet),cid+':query wire')
                    epoch = '1' if request['epoch'] is True else str(request['epoch'])
                    wanted = ['SELECT session,resource,epoch FROM meta WHERE id=1',
                              "SELECT request,status FROM receipts WHERE epoch="+epoch+" AND op_id='"+request['op_id']+"'"]
                    ck(wire['sql']==wanted,cid+':query SQL coverage')
                elif command['op']=='execute':
                    ck(wire['result']=={'status':'APPLIED'},cid+':execution wire')
                    ck('BEGIN IMMEDIATE' in wire['sql'] and wire['sql'][-1]=='COMMIT',cid+':transaction boundary')
                elif command['op']=='retire':
                    ck(wire['result']=={'status':'RETIRED','coverage_epoch':8},cid+':retirement wire')
            ck(all(row['calls'][i]['end_ns']<=row['calls'][i+1]['start_ns'] for i in range(len(row['calls'])-1)),cid+':serial ordering')
        except Exception as exc:
            errors.append(cid+':unreadable:'+repr(exc))
    # The decisive information-loss test compares actual delivered query packets,
    # not equal outcome labels generated by the candidate.
    index = {(r.get('repetition'),r.get('scenario'),r.get('policy')):r for r in rows}
    for r in range(repetitions):
        for a in ARMS:
            one=index.get((r,'RETIRED_APPLIED',a)); zero=index.get((r,'RETIRED_NEVER_ACCEPTED',a))
            if one and zero:
                ck(same(one['packet'],zero['packet']),f'r{r}-{a}:indistinguishable packets')
                ck(len(one['pre']['effects'])==1 and len(zero['pre']['effects'])==0,f'r{r}-{a}:different histories')
    return errors

def mutations(rows,reps):
    outputs={}
    changes=[('missing_case',lambda x:x.pop()),('duplicate_case',lambda x:x.append(copy.deepcopy(x[0]))),
             ('boolean_repetition',lambda x:x[0].__setitem__('repetition',False)),
             ('boolean_exit',lambda x:x[0]['calls'][0].__setitem__('returncode',False)),
             ('false_done',lambda x:x[3]['decision'].__setitem__('status','COMPLETED')),
             ('missing_sql',lambda x:alter_sql(x,[])),
             ('query_effect_access',lambda x:alter_sql(x,['SELECT * FROM effects'])),
             ('query_write',lambda x:alter_sql(x,['DELETE FROM receipts'])),
             ('false_coverage',lambda x:x[2]['packet'].__setitem__('coverage_epoch',7)),
             ('boolean_request_epoch',lambda x:x[0]['request'].__setitem__('epoch',True)),
             ('rehashed_effect_change',lambda x:alter_db(x[0]['final'])),
             ('foreign_wire_pid',lambda x:alter_pid(x))]
    for name,change in changes:
        edited=copy.deepcopy(rows);change(edited)
        outputs[name]=bool(validate(edited,reps))
    return outputs

def alter_sql(rows,sql):
    c=next(c for c in rows[0]['calls'] if json.loads(c['stdin'])['op']=='query')
    w=json.loads(c['stdout']);w['sql']=sql;c['stdout']=canonical(w)+'\n'

def alter_pid(rows):
    c=rows[0]['calls'][0];w=json.loads(c['stdout']);w['pid']+=1;c['stdout']=canonical(w)+'\n'

def alter_db(snap):
    db=sqlite3.connect(':memory:');db.deserialize(base64.b64decode(snap['db_b64']))
    db.execute('UPDATE effects SET delta=9');db.commit();b=db.serialize();db.close()
    snap.update(tables(b));snap['db_b64']=base64.b64encode(b).decode();snap['db_sha256']=digest(b)

def main():
    p=argparse.ArgumentParser();p.add_argument('parent',type=Path);p.add_argument('--construction',action='store_true');p.add_argument('--controls',action='store_true')
    a=p.parse_args();reps=1 if a.construction else 3;rows=[];errors=[]
    root=Path(__file__).resolve().parent
    freeze=None
    if not a.construction:
        freeze=json.loads((root/'FREEZE.json').read_text())
        for name,want in freeze['sources'].items():
            if digest((root/name).read_bytes())!=want: errors.append('source hash:'+name)
    for r in range(reps):
        path=a.parent/f'batch-{r}'
        try:
            b=(path/'RAW.jsonl').read_bytes();batch=[json.loads(line) for line in b.splitlines()]
            receipt=json.loads((path/'EXECUTION.json').read_text())
            if (type(receipt['returncode']) is not int or receipt['returncode']!=0 or receipt['timeout'] is not False
                or receipt['stderr']!='' or receipt['raw_sha256']!=digest(b)):
                errors.append('batch exit/hash:'+str(r))
            marker=json.loads((path/'CONSUMED.json').read_text());end=json.loads(receipt['stdout'])
            if end['rows']!=16 or end['batch']!=r or end['status']!='COMPLETE' or marker['pid']!=receipt['pid']:
                errors.append('batch identity:'+str(r))
            if not a.construction and (marker['freeze_sha256']!=digest((root/'FREEZE.json').read_bytes()) or end['freeze_sha256']!=marker['freeze_sha256']):
                errors.append('batch freeze:'+str(r))
            rows.extend(batch)
        except Exception as exc: errors.append('missing batch:'+str(r)+':'+repr(exc))
    errors.extend(validate(rows,reps))
    controls=mutations(rows,reps) if a.controls and not errors else {}
    if a.controls and (len(controls)!=12 or not all(controls.values())): errors.append('corruption controls')
    counts={arm:{} for arm in ARMS}
    for row in rows:
        counts[row['policy']][row['scenario']]= {'status':row['decision']['status'],
          'pre_effect_count':len(row['pre']['effects']),'final_effect_count':len(row['final']['effects']),
          'final_counter':sum(e[5] for e in row['final']['effects'])}
    verdict=('PASS_CONSTRUCTION_ONLY' if a.construction else 'PASS_RETIRED_OUTCOME_COVERAGE_SCOPED') if not errors else 'FAIL_OR_HOLD_AUDIT'
    result={'verdict':verdict,'rows':len(rows),'repetitions':reps,'errors':errors,'controls':controls,'by_scenario':counts}
    print(json.dumps(result,sort_keys=True,separators=(',',':')))
    raise SystemExit(0 if not errors else 1)

if __name__=='__main__': main()
