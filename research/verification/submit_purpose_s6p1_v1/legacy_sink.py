"""Cooperative document sink: identical transactions, different revision admission.
This is an experimental application component, not a production API.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

FIELDS = {'session', 'document', 'epoch', 'job_id', 'revision', 'value', 'kind'}
POLICIES = ('ARRIVAL_ORDER', 'REVISION_FENCE')

class Store:
    def __init__(self, path, session, policy):
        if policy not in POLICIES: raise ValueError('POLICY')
        self.session, self.policy = session, policy
        self.db = sqlite3.connect(path, isolation_level=None, timeout=2)
        self.db.execute('PRAGMA journal_mode=DELETE')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
CREATE TABLE document (id INTEGER PRIMARY KEY, revision INTEGER NOT NULL, value TEXT NOT NULL);
INSERT INTO document VALUES(1,0,'');
CREATE TABLE commits (ordinal INTEGER PRIMARY KEY, job_id TEXT, revision INTEGER, value TEXT, kind TEXT);
CREATE TABLE seen (job_id TEXT PRIMARY KEY, fingerprint TEXT, status TEXT);
''')
    def state(self):
        r,v=self.db.execute('SELECT revision,value FROM document WHERE id=1').fetchone()
        return {'revision':r,'value':v}
    def apply(self,j):
        # Equality, exact types and ownership precede all mutation.
        if (type(j) is not dict or set(j)!=FIELDS or
            j['session']!=self.session or j['document']!='doc' or j['epoch']!='epoch-1' or
            type(j['revision']) is not int or not 1<=j['revision']<2**63 or
            type(j['value']) is not str or len(j['value'])>64 or
            type(j['job_id']) is not str or not 1<=len(j['job_id'])<=80 or
            j['kind'] not in ('AUTO','SUBMIT')):
            return {'status':'INVALID','authority':False,'state':self.state()}
        wire=json.dumps(j,sort_keys=True,separators=(',',':')).encode()
        digest=hashlib.sha256(wire).hexdigest()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            before=self.state()
            old=self.db.execute('SELECT fingerprint,status FROM seen WHERE job_id=?',(j['job_id'],)).fetchone()
            if old:
                status='REPLAY' if old[0]==digest else 'CONFLICT_ID'
            elif self.policy=='REVISION_FENCE' and j['revision']<before['revision']:
                status='STALE'
            elif self.policy=='REVISION_FENCE' and j['revision']==before['revision']:
                status='DUPLICATE_REVISION' if j['value']==before['value'] else 'CONFLICT_REVISION'
            else:
                status='APPLIED'
            if status=='APPLIED':
                self.db.execute('UPDATE document SET revision=?,value=? WHERE id=1',(j['revision'],j['value']))
                self.db.execute('INSERT INTO commits(job_id,revision,value,kind) VALUES(?,?,?,?)',
                                (j['job_id'],j['revision'],j['value'],j['kind']))
            if old is None:
                self.db.execute('INSERT INTO seen VALUES(?,?,?)',(j['job_id'],digest,status))
            after=self.state()
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise
        return {'status':status,'before':before,'state':after,'authority':False}
    def close(self): self.db.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--session',required=True);p.add_argument('--policy',choices=POLICIES,required=True);a=p.parse_args()
    store=Store(a.out/'document.sqlite',a.session,a.policy)
    journal=(a.out/'sink.jsonl').open('x');seq=0;pending={}
    def event(kind,**kw):
        nonlocal seq
        seq+=1;r={'kind':kind,'seq':seq,'ns':time.monotonic_ns(),'pid':os.getpid(),**kw}
        journal.write(json.dumps(r,sort_keys=True)+'\n');journal.flush();return r
    def emit(x):print(json.dumps(x,sort_keys=True),flush=True)
    emit(event('READY',session=a.session,policy=a.policy,state=store.state()))
    for raw in sys.stdin:
        q=json.loads(raw);event('REQUEST',request=q,raw=raw)
        if q['op']=='enqueue':
            j=q['job']
            if j['job_id'] in pending:raise ValueError('DUPLICATE_QUEUE_ID')
            pending[j['job_id']]=j;emit(event('ENQUEUED',job=j,pending=list(pending)))
        elif q['op'] in ('release','submit'):
            j=pending.pop(q['job_id']) if q['op']=='release' else q['job']
            result=store.apply(j);emit(event('COMMIT_ATTEMPT',job=j,result=result,pending=list(pending)))
        elif q['op']=='state':emit(event('STATE',state=store.state(),pending=list(pending)))
        elif q['op']=='close':
            if pending:raise ValueError('UNRESOLVED_PENDING_AT_CLOSE')
            emit(event('CLOSE',state=store.state(),pending=[]));break
        else:raise ValueError('OP')
    store.close();journal.close()
if __name__=='__main__':main()
