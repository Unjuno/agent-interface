#!/usr/bin/env python3
import argparse, hashlib, json, os, sqlite3, subprocess, sys, tempfile
from pathlib import Path
POLICIES=('STALE_SCAN_DELETE','TXN_REVALIDATE_DELETE')
SCENARIOS=('PRODUCER_BEFORE_SCAN','PRODUCER_BETWEEN_SCAN_DELETE','PRODUCER_AFTER_DELETE','NO_NEW_REFERENCE')
HERE=Path(__file__).resolve().parent

def snap(c):
    return {'pages':c.execute('select seq,acked from pages order by seq').fetchall(),'refs':c.execute('select seq,sha from page_blobs order by seq,sha').fetchall(),'blobs':[(r[0],len(r[1]),hashlib.sha256(r[1]).hexdigest()) for r in c.execute('select sha,data from blobs order by sha')]}

def setup(db,data,sha):
    c=sqlite3.connect(db,timeout=3); c.executescript('''pragma journal_mode=delete; pragma synchronous=full;
    create table pages(seq integer primary key, acked integer not null);
    create table blobs(sha text primary key, data blob not null);
    create table page_blobs(seq integer not null, sha text not null, primary key(seq,sha));'''); c.execute('insert into pages values(1,1)'); c.execute('insert into blobs values(?,?)',(sha,data)); c.execute('insert into page_blobs values(1,?)',(sha,)); c.commit(); out=snap(c); c.close(); return out

def actor(op,db,**kw):
    cmd=[sys.executable,'-B',str(HERE/'actor.py'),op,'--db',str(db)]
    for k,v in kw.items(): cmd += ['--'+k.replace('_','-'),str(v)]
    cp=subprocess.run(cmd,capture_output=True,text=True,timeout=3)
    rec={'op':op,'argv':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'pid_parent':os.getpid()}
    if cp.returncode!=0: raise RuntimeError('actor failure:'+json.dumps(rec,sort_keys=True))
    rec['result']=json.loads(cp.stdout); return rec

def resolve(db):
    c=sqlite3.connect(db,timeout=3); out=[]
    for seq,sha in c.execute('''select p.seq,pb.sha from pages p join page_blobs pb on pb.seq=p.seq where p.acked=0 order by p.seq'''):
      row=c.execute('select data from blobs where sha=?',(sha,)).fetchone(); out.append({'seq':seq,'sha':sha,'available':row is not None,'actual_sha256':hashlib.sha256(row[0]).hexdigest() if row else None})
    state=snap(c); c.close(); return out,state

def run(case_id,policy,scenario):
    data=(b'PNG-A:'+case_id.encode())*17; sha=hashlib.sha256(data).hexdigest()
    with tempfile.TemporaryDirectory(prefix='gcconc-') as td:
      db=Path(td)/'store.db'; initial=setup(db,data,sha); actors=[]
      def prod(): actors.append(actor('producer',db,data_hex=data.hex(),sha=sha))
      def scan():
        rec=actor('scan',db); actors.append(rec); return rec['result']['candidates']
      def delete(cands): actors.append(actor('delete',db,policy=policy,candidates=json.dumps(cands,separators=(',',':'))))
      if scenario=='PRODUCER_BEFORE_SCAN': prod(); cands=scan(); delete(cands)
      elif scenario=='PRODUCER_BETWEEN_SCAN_DELETE': cands=scan(); prod(); delete(cands)
      elif scenario=='PRODUCER_AFTER_DELETE': cands=scan(); delete(cands); prod()
      else: cands=scan(); delete(cands)
      resolution,state=resolve(db)
      return {'schema':'agent-interface/referenced-image-gc-concurrency-case-v1','case_id':case_id,'policy':policy,'scenario':scenario,'source_sha256':sha,'source_bytes':len(data),'initial':initial,'actors':actors,'resolution':resolution,'final':state,'authority':'none','input_dispatched':False,'pid':os.getpid()}

def main():
    a=argparse.ArgumentParser(); a.add_argument('--case-id',required=True); a.add_argument('--policy',choices=POLICIES,required=True); a.add_argument('--scenario',choices=SCENARIOS,required=True); x=a.parse_args(); print(json.dumps(run(x.case_id,x.policy,x.scenario),sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
