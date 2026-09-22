"""Bounded one-case-at-a-time orchestration. Formal cases must never be replayed."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parent

def dump(path,obj):path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def statcopy(db,where):
    where.mkdir();items={}
    for suffix in ('','-wal','-shm'):
        src=Path(str(db)+suffix)
        if src.exists():
            st=src.stat();raw=src.read_bytes();dst=where/('store.sqlite'+suffix);dst.write_bytes(raw)
            if len(raw)!=st.st_size:raise RuntimeError('SNAPSHOT_RACE')
            items[suffix or 'db']={'file':str(dst.relative_to(where.parent)),
                'size':st.st_size,'allocated_bytes':st.st_blocks*512,'sha256':digest(dst)}
    return {'kind':'QUIESCENT_BYTE_COPY_NOT_LIVE_BACKUP','files':items}

class Child:
    def __init__(self,role,db,case,out):
        self.role=role;self.out=out;self.calls=[];self.pid=None
        self.err=open(out/(role+'.stderr'),'wb')
        self.p=subprocess.Popen([sys.executable,'-B',str(ROOT/'actor.py'),role,str(db),case],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,bufsize=8192)
        self.pid=self.p.pid;self.args=self.p.args
        self.wirein=open(out/(role+'.stdin'),'wb');self.wireout=open(out/(role+'.stdout'),'wb')
    def call(self,op,**kwargs):
        req={'op':op,'id':len(self.calls),**kwargs};wire=(json.dumps(req,sort_keys=True)+'\n').encode()
        t=time.monotonic_ns();self.wirein.write(wire);self.wirein.flush()
        self.p.stdin.write(wire);self.p.stdin.flush()
        # Outer supervisor is authoritative even if a partial line stalls here.
        if not select.select([self.p.stdout],[],[],3)[0]:raise TimeoutError('CHILD_RESPONSE')
        chunks=[]
        while True:
            b=self.p.stdout.readline()
            if not b:raise RuntimeError('EARLY_CHILD_EOF')
            chunks.append(b)
            if b.endswith(b'\n'):break
        wireout=b''.join(chunks);self.wireout.write(wireout);self.wireout.flush()
        response=json.loads(wireout)
        if response['request']!=req:raise RuntimeError('REQUEST_ID_MISMATCH')
        row={'sent_ns':t,'received_ns':time.monotonic_ns(),'request':req,'response':response}
        self.calls.append(row)
        with open(self.out/'JOURNAL.jsonl','a') as f:f.write(json.dumps({'role':self.role,**row},sort_keys=True)+'\n')
        return response
    def finish(self):
        self.call('close');self.p.stdin.close();rc=self.p.wait(timeout=3)
        extra=self.p.stdout.read();self.wireout.write(extra);self.wireout.close();self.wirein.close();self.err.close()
        return {'pid':self.pid,'args':self.args,'returncode':rc,'extra_stdout':extra.decode(),
                'stderr_file':self.role+'.stderr'}
    def rescue(self):
        if self.p.poll() is None:
            self.p.terminate()
            try:self.p.wait(timeout=1)
            except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=1)
        for f in (self.wirein,self.wireout,self.err):
            if not f.closed:f.close()

def run_case(config,out):
    out.mkdir();db=out/'store.sqlite';children=[]
    row={'config':config,'started_ns':time.monotonic_ns(),'stages':[], 'exits':{},'status':'STARTED'}
    dump(out/'ROW.json',row)
    try:
        writer=Child('writer',db,config['case'],out);children.append(writer)
        init=writer.call('init');row['init']=init
        reader=Child('reader',db,config['case'],out);children.append(reader)
        row['reader_start']=reader.call('start',mode=config['mode'])
        row['initial_files']=statcopy(db,out/'initial')
        count=0
        for target in config['milestones']:
            advanced=writer.call('advance',count=target-count);count=target
            row['stages'].append({'writes_total':count,'writer':advanced,
                                 'snapshot':statcopy(db,out/f'after-{count:03d}')})
            dump(out/'ROW.json',row)
        row['before_release_truncate']=writer.call('truncate')
        row['before_release_files']=statcopy(db,out/'before-release')
        row['reader_peek']=reader.call('peek')
        row['reader_release']=reader.call('release')
        row['after_release_truncate']=writer.call('truncate')
        row['after_release_files']=statcopy(db,out/'after-release')
        row['exits']['reader']=reader.finish();row['exits']['writer']=writer.finish()
        row['terminal_files']=statcopy(db,out/'terminal')
        if any(x['returncode']!=0 for x in row['exits'].values()):raise RuntimeError('CHILD_EXIT')
        row['status']='COMPLETE'
    except BaseException as exc:
        row['status']='STOP';row['error']=repr(exc);row['traceback']=traceback.format_exc();raise
    finally:
        for c in children:c.rescue()
        row['ended_ns']=time.monotonic_ns();dump(out/'ROW.json',row)
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['construction','formal'],required=True)
    ap.add_argument('--batch',type=int,default=0);a=ap.parse_args()
    plan=json.loads((ROOT/'PLAN.json').read_text());configs=plan['construction'] if a.mode=='construction' else plan['batches'][a.batch]
    dest=ROOT/(f'construction-{a.batch:02d}' if a.mode=='construction' else f'formal-{a.batch:02d}')
    dest.mkdir(exist_ok=False)
    dump(dest/'START.json',{'started_ns':time.monotonic_ns(),'configs':configs,'pid':os.getpid()})
    for c in configs:
        row=run_case(c,dest/c['case'])
        with open(dest/'ROWS.jsonl','a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
    dump(dest/'END.json',{'ended_ns':time.monotonic_ns(),'cases':len(configs),'pid':os.getpid()})
    print(json.dumps({'cases':len(configs),'directory':str(dest)}))
if __name__=='__main__':main()
