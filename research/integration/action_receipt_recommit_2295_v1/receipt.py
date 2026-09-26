from __future__ import annotations
import argparse, hashlib, json, sqlite3, sys
from pathlib import Path

POLICIES={'REUSED_ID','FRESH_EPOCH','COMPOUND'}

def strict_int(v): return isinstance(v,int) and not isinstance(v,bool)

def digest_state(s):
    payload={k:s[k] for k in ('session','surface_id','target_id')}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def prepare(policy,s):
    r={'schema':'agent-interface/action-receipt-recommit-v1','policy':policy,
       'operation_id':s['operation_id'],'claim':s['claim'],'commit_id':s['commit_id'],
       'x':s['x'],'y':s['y']}
    if policy in {'FRESH_EPOCH','COMPOUND'}: r['commit_epoch']=s['commit_epoch']
    if policy=='COMPOUND':
        r.update(session=s['session'],surface_id=s['surface_id'],target_id=s['target_id'],
                 evidence_digest=s['evidence_digest'],authority_generation=s['authority_generation'])
    return r

def validate(policy, raw, cur, dedup):
    try: r=json.loads(raw)
    except Exception: return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
    if not isinstance(r,dict) or r.get('schema')!='agent-interface/action-receipt-recommit-v1' or r.get('policy')!=policy:
        return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
    for k in ('operation_id','claim','commit_id'):
        if not isinstance(r.get(k),str): return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
    if not strict_int(r.get('x')) or not strict_int(r.get('y')): return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
    if r['claim']!=cur['claim'] or r['commit_id']!=cur['commit_id']:
        return {'admitted':False,'reason':'COMMIT_MISMATCH'}
    if policy in {'FRESH_EPOCH','COMPOUND'}:
        if not strict_int(r.get('commit_epoch')): return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
        if r['commit_epoch']!=cur['commit_epoch']: return {'admitted':False,'reason':'STALE_COMMIT_EPOCH'}
    if policy=='COMPOUND':
        for k in ('surface_id','target_id','authority_generation'):
            if not strict_int(r.get(k)): return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
        for k in ('session','evidence_digest'):
            if not isinstance(r.get(k),str): return {'admitted':False,'reason':'MALFORMED_RECEIPT'}
        checks=('session','surface_id','target_id','evidence_digest','authority_generation')
        for k in checks:
            if r[k]!=cur[k]: return {'admitted':False,'reason':'BINDING_MISMATCH','field':k}
        db=sqlite3.connect(dedup)
        try:
            db.execute('PRAGMA journal_mode=DELETE')
            db.execute('CREATE TABLE IF NOT EXISTS consumed(operation_id TEXT PRIMARY KEY, receipt_sha256 TEXT NOT NULL)')
            sha=hashlib.sha256(raw.encode()).hexdigest()
            db.execute('BEGIN IMMEDIATE')
            seen=db.execute('SELECT receipt_sha256 FROM consumed WHERE operation_id=?',(r['operation_id'],)).fetchone()
            if seen:
                db.rollback(); return {'admitted':False,'reason':'DUPLICATE_OPERATION'}
            db.execute('INSERT INTO consumed(operation_id,receipt_sha256) VALUES(?,?)',(r['operation_id'],sha)); db.commit()
        finally: db.close()
    return {'admitted':True,'reason':'CURRENT_RECEIPT','x':r['x'],'y':r['y']}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['prepare','validate']); ap.add_argument('--policy',required=True,choices=sorted(POLICIES)); ap.add_argument('--dedup')
    a=ap.parse_args(); payload=sys.stdin.read()
    if a.mode=='prepare':
        s=json.loads(payload); out=prepare(a.policy,s)
    else:
        env=json.loads(payload); out=validate(a.policy,env['receipt_raw'],env['current_state'],a.dedup)
    sys.stdout.write(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
if __name__=='__main__': main()
