"""Read-only, separately structured oracle; never imports actor, runner or vendor."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parent


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def same(a,b):return encoded(a)==encoded(b)  # JSON booleans never equal integer fields.

def receipt(label,seq,lo=None,hi=None):
    return {'intent_id':label,'intent_seq':seq,'from_generation':seq if lo is None else lo,
            'to_generation':seq+1 if hi is None else hi,'confirmation_content_id':'content-'+label,
            'confirmation_revision':1}

def original():
    return {'meta':{'capacity':2,'generation':4,'retired_through_seq':1},
            'history':[receipt('B',2),receipt('C',3)]}

def retired():
    return {'meta':{'capacity':2,'generation':4,'retired_through_seq':3},'history':[]}

def probes():
    return {'EXACT_OLD':receipt('B',2),'REBOUND_OLD':receipt('B',2,4,5),'FRESH':receipt('D',4)}

def expected_view(cfg):
    old,new=original(),retired()
    when=cfg['schedule']
    if when in ('BEFORE_OPEN','AFTER_BEGIN'):return new
    if when!='BETWEEN_READS' or cfg['policy']=='SNAPSHOT':return old
    if cfg['order']=='META_FIRST':return {'meta':old['meta'],'history':new['history']}
    return {'meta':new['meta'],'history':old['history']}

def reference_decisions(view):
    """Finite independently specified table over the four possible observed states."""
    if same(view,original()):
        return {'EXACT_OLD':'ALREADY_COMMITTED_SELF','REBOUND_OLD':'CONFLICT_INTENT_CONTENT','FRESH':'NEW_INTENT_ALLOWED'}
    if same(view,retired()):
        return {'EXACT_OLD':'EXPIRED_INTENT','REBOUND_OLD':'EXPIRED_INTENT','FRESH':'NEW_INTENT_ALLOWED'}
    if view['history']==[] and view['meta']['retired_through_seq']==1:
        return {'EXACT_OLD':'INVALID_TRANSITION','REBOUND_OLD':'NEW_INTENT_ALLOWED','FRESH':'SEQUENCE_GAP'}
    if same(view['history'],original()['history']) and view['meta']['retired_through_seq']==3:
        return {'EXACT_OLD':'ALREADY_COMMITTED_SELF','REBOUND_OLD':'CONFLICT_INTENT_CONTENT','FRESH':'NEW_INTENT_ALLOWED'}
    raise ValueError('UNEXPECTED_STATE')

def db_read(path):
    pre=digest(path)
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.execute('BEGIN')
    meta=dict(db.execute('SELECT capacity,generation,retired_through_seq FROM meta WHERE id=1').fetchone())
    hist=[dict(r) for r in db.execute('SELECT * FROM history ORDER BY intent_seq')]
    db.close()
    if digest(path)!=pre:raise RuntimeError('AUDIT_MUTATED_DATABASE')
    return {'meta':meta,'history':hist}

def expected_ops(cfg):
    first,second=('meta','history') if cfg['order']=='META_FIRST' else ('history','meta')
    ops=[]
    if cfg['schedule']=='BEFORE_OPEN':ops.append(('writer','retire',None))
    ops.append(('reader','start',None))
    if cfg['schedule']=='AFTER_BEGIN':ops.append(('writer','retire',None))
    ops.append(('reader','read',first))
    if cfg['schedule']=='BETWEEN_READS':ops.append(('writer','retire',None))
    ops.append(('reader','read',second))
    if cfg['schedule']=='AFTER_READS':ops.append(('writer','retire',None))
    return ops+[('reader','finish',None),('reader','close',None),('writer','close',None)]

def validate(rows, scheduled, directories, external=True):
    errors=[];summary={p:{'cases':0,'mixed_views':0,'rebound_proposals':0,'fresh_refusals':0,
                         'historical_at_return':0} for p in ('AUTOCOMMIT','SNAPSHOT')}
    def check(condition,label):
        if not condition:errors.append(label)
    check(len(rows)==len(scheduled),'CASE_COUNT')
    for row,cfg,directory in zip(rows,scheduled,directories):
        tag=cfg['case_id'];check(same(row.get('config'),cfg),tag+':CONFIG')
        check(row.get('error') is None,tag+':ERROR')
        check(same(row.get('requests'),probes()),tag+':REQUESTS')
        expected=expected_view(cfg);result=row.get('result',{})
        check(same(result.get('view'),expected),tag+':VIEW')
        check(same(result.get('decisions'),reference_decisions(expected)),tag+':DECISIONS')
        check(result.get('authority')=='none' and result.get('input_dispatched') is False
              and result.get('state_applied') is False,tag+':AUTHORITY')
        before=row.get('snapshots',{}).get('before',{})
        final=row.get('snapshots',{}).get('final',{})
        endstate=original() if cfg['schedule']=='STABLE' else retired()
        for label,obj,truth in [('before',before,original()),('final',final,endstate)]:
            check(same({k:obj.get(k) for k in ('meta','history')},truth),tag+':'+label)
        if cfg['schedule']!='STABLE':
            aw=row.get('snapshots',{}).get('after_write',{})
            check(same({k:aw.get(k) for k in ('meta','history')},retired()),tag+':ATOMIC_WRITE')
        events=row.get('events',[])
        rpc=[e for e in events if e.get('type')=='rpc']
        ops=[(e.get('role'),e.get('request',{}).get('op'),e.get('request',{}).get('component')) for e in rpc]
        check(ops==expected_ops(cfg),tag+':ORDER')
        check(len([e for e in events if e.get('type')=='ready'])==2,tag+':READY_COUNT')
        ps={p.get('role'):p for p in row.get('processes',[])}
        check(set(ps)=={'reader','writer'},tag+':PROCESS_COUNT')
        for role,p in ps.items():
            check(type(p.get('returncode')) is int and p['returncode']==0 and p.get('normal_close') is True,tag+':EXIT:'+role)
            check(type(p.get('pid')) is int and p['pid']>0,tag+':PID:'+role)
        if set(ps)=={'reader','writer'}:check(ps['reader']['pid']!=ps['writer']['pid'],tag+':SEPARATE_PROCESSES')
        last=row.get('started_ns',0)
        for e in events:
            if e['type']=='ready':
                check(e['response'].get('pid')==ps.get(e['role'],{}).get('pid') and e['response'].get('case_id')==tag,tag+':READY_BINDING')
                continue
            req,resp=e['request'],e['response'];role=e['role']
            ns=[e['sent_ns'],resp['started_ns'],resp['ended_ns'],e['received_ns']]
            check(all(type(t) is int for t in ns) and last<=ns[0]<=ns[1]<=ns[2]<=ns[3],tag+':CLOCK_ORDER')
            last=ns[-1]
            check(resp.get('pid')==ps.get(role,{}).get('pid') and resp.get('case_id')==tag
                  and resp.get('request_id')==req.get('request_id') and resp.get('op')==req.get('op'),tag+':WIRE_IDENTITY')
            sql=resp.get('sql',[])
            if role=='reader':
                check(type(resp.get('total_changes')) is int and resp['total_changes']==0,tag+':READER_WRITES')
                if req['op']=='start':wanted=['BEGIN DEFERRED'] if cfg['policy']=='SNAPSHOT' else []
                elif req['op']=='read':
                    wanted=['SELECT capacity,generation,retired_through_seq FROM meta WHERE id=1'] if req['component']=='meta' else ['SELECT intent_id,intent_seq,from_generation,to_generation,confirmation_content_id,confirmation_revision FROM history ORDER BY intent_seq']
                    check(same(resp.get('value'),expected[req['component']]),tag+':COMPONENT_READ')
                elif req['op']=='finish':wanted=['COMMIT'] if cfg['policy']=='SNAPSHOT' else []
                else:wanted=[]
                check(sql==wanted,tag+':READER_SQL')
                tx=cfg['policy']=='SNAPSHOT' and req['op'] in ('start','read')
                check(resp.get('in_transaction') is tx,tag+':READ_TRANSACTION')
            elif req['op']=='retire':
                check(sql==['BEGIN IMMEDIATE','DELETE FROM history','UPDATE meta SET retired_through_seq=3 WHERE id=1','COMMIT'],tag+':WRITER_SQL')
                check(resp.get('in_transaction') is False and type(resp.get('total_changes')) is int and resp['total_changes']==3,tag+':ATOMIC_WRITER')
        if rpc:check(same(result,[e['response'] for e in rpc if e['request']['op']=='finish'][0]),tag+':RESULT_JOIN')
        check(last<=row.get('ended_ns',0),tag+':END_ORDER')
        if external:
            for label,obj in row.get('snapshots',{}).items():
                path=directory/obj['file']
                check(path.is_file() and digest(path)==obj['sha256'],tag+':DB_HASH:'+label)
                if path.is_file():check(same(db_read(path),{k:obj[k] for k in ('meta','history')}),tag+':DB_STATE:'+label)
            check(digest(directory/'store.sqlite')==row.get('db_sha256_final'),tag+':FINAL_ORIGINAL_BYTES')
            for role,p in ps.items():
                for suffix in ('stdin','stdout','stderr'):
                    check(digest(directory/f'{role}.{suffix}')==p.get(suffix+'_sha256'),tag+':WIRE_HASH:'+role+':'+suffix)
                actual_in=[json.loads(s) for s in (directory/f'{role}.stdin').read_text().splitlines()]
                actual_out=[json.loads(s) for s in (directory/f'{role}.stdout').read_text().splitlines()]
                check(same(actual_in,[e['request'] for e in rpc if e['role']==role]),tag+':INPUT_JOIN:'+role)
                er=[e['response'] for e in events if e['role']==role]
                check(same(actual_out,er),tag+':OUTPUT_JOIN:'+role)
                check((directory/f'{role}.stderr').stat().st_size==0,tag+':STDERR:'+role)
        s=summary[cfg['policy']];s['cases']+=1
        view=result.get('view',{})
        s['mixed_views']+=not (same(view,original()) or same(view,retired()))
        s['rebound_proposals']+=result.get('decisions',{}).get('REBOUND_OLD')=='NEW_INTENT_ALLOWED'
        s['fresh_refusals']+=result.get('decisions',{}).get('FRESH')!='NEW_INTENT_ALLOWED'
        s['historical_at_return']+=same(view,original()) and same(endstate,retired())
    return errors,summary


def controls(rows,scheduled,dirs):
    cases={}
    def challenge(name,mutate):
        changed=copy.deepcopy(rows);mutate(changed)
        try:errors,_=validate(changed,scheduled,dirs,external=False)
        except Exception as e:errors=['REJECT_EXCEPTION:'+type(e).__name__]
        cases[name]={'rejected':bool(errors),'errors':errors[:3]}
    challenge('drop_case',lambda r:r.pop())
    challenge('duplicate_case',lambda r:r.__setitem__(-1,copy.deepcopy(r[0])))
    challenge('boolean_rep',lambda r:r[0]['config'].__setitem__('rep',False))
    challenge('mixed_watermark',lambda r:r[0]['result']['view']['meta'].__setitem__('retired_through_seq',99))
    challenge('drop_history',lambda r:next(x for x in r if x['result']['view']['history'])['result']['view'].__setitem__('history',[]))
    challenge('false_fresh_refusal',lambda r:r[0]['result']['decisions'].__setitem__('FRESH','SEQUENCE_GAP'))
    challenge('authority',lambda r:r[0]['result'].__setitem__('state_applied',True))
    challenge('boolean_exit',lambda r:r[0]['processes'][0].__setitem__('returncode',False))
    challenge('lost_process',lambda r:r[0]['processes'].pop())
    def drop_sql(r):
        e=next(e for e in r[0]['events'] if e['type']=='rpc' and e['request']['op']=='read')
        e['response']['sql']=[]
    challenge('missing_sql_evidence',drop_sql)
    challenge('wrong_request',lambda r:r[0]['requests']['FRESH'].__setitem__('intent_seq',40))
    challenge('changed_final_state',lambda r:r[0]['snapshots']['final']['meta'].__setitem__('generation',5))
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--construction',action='store_true');p.add_argument('--controls',action='store_true')
    a=p.parse_args();plan=json.loads((ROOT/'PLAN.json').read_text());scheduled=plan['cases'];rows=[];dirs=[];errors=[]
    if a.construction:
        scheduled=[r for r in scheduled if r['rep']==0 and (r['schedule']=='BETWEEN_READS' or (r['schedule']=='AFTER_BEGIN' and r['policy']=='SNAPSHOT'))]
        batches=[ROOT/'construction-01']
    else:batches=[ROOT/'formal'/f'batch-{i:02d}' for i in range(4)]
    for b in batches:
        block=[json.loads(line) for line in (b/'RAW.jsonl').read_text().splitlines()]
        rows.extend(block);dirs.extend(b/r['config']['case_id'] for r in block)
        if not a.construction:
            start=json.loads((b/'START.json').read_text());end=json.loads((b/'END.json').read_text());ex=json.loads((b/'EXECUTION.json').read_text())
            if type(ex.get('returncode')) is not int or ex['returncode']!=0 or ex.get('timeout') is not False:errors.append('BATCH_EXIT:'+b.name)
            if ex['child_pid']!=start['pid'] or start['pid']!=end['pid']:errors.append('BATCH_IDENTITY:'+b.name)
            if end['raw_sha256']!=digest(b/'RAW.jsonl') or end['cases']!=len(block):errors.append('BATCH_HASH:'+b.name)
            if not ex['started_ns']<=start['started_ns']<=end['ended_ns']<=ex['ended_ns']:errors.append('BATCH_CLOCK:'+b.name)
            if start['cases']!=[r['config']['case_id'] for r in block]:errors.append('BATCH_ORDER:'+b.name)
    row_errors,summary=validate(rows,scheduled,dirs)
    errors.extend(row_errors)
    if not a.construction:
        freeze=json.loads((ROOT/'FREEZE.json').read_text())
        for name,sha in freeze['files'].items():
            if digest(ROOT/name)!=sha:errors.append('SOURCE_HASH:'+name)
    cc=controls(rows,scheduled,dirs) if a.controls else {}
    if any(not c['rejected'] for c in cc.values()):errors.append('CORRUPTION_CONTROL')
    if not a.construction:
        if summary['AUTOCOMMIT']!={'cases':20,'mixed_views':4,'rebound_proposals':2,'fresh_refusals':2,'historical_at_return':4}:errors.append('AUTOCOMMIT_GATE')
        if summary['SNAPSHOT']!={'cases':20,'mixed_views':0,'rebound_proposals':0,'fresh_refusals':0,'historical_at_return':8}:errors.append('SNAPSHOT_GATE')
    result={'decision':('PASS_CONSTRUCTION_ONLY' if a.construction else 'PASS_GC_READ_SNAPSHOT_BOUNDARY_SCOPED') if not errors else 'HOLD_OR_FAIL_EVIDENCE',
            'cases':len(rows),'classifications':len(rows)*3,'errors':errors,'summary':summary,'corruption_controls':cc}
    print(json.dumps(result,sort_keys=True,indent=2));sys.exit(bool(errors))

if __name__=='__main__':main()
