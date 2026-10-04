"""Real Linux pipes: full, partial, broken-reader and intact Unicode controls."""
import fcntl,hashlib,json,os
from pathlib import Path
from bounded_pipe_writer import BoundedPipeWriter,WriteUncertain
from command_once import CommandOnce
HERE=Path(__file__).resolve().parent;out=HERE/'results/bounded-pipe-writer-02';out.mkdir(exist_ok=False);rows=[]
for case in ('normal','full','partial','broken'):
    r,w=os.pipe()
    try:
        fcntl.fcntl(w,fcntl.F_SETPIPE_SZ,4096);capacity=fcntl.fcntl(w,fcntl.F_GETPIPE_SZ)
        writer=BoundedPipeWriter(w,max_bytes=65536);sender=CommandOnce(writer)
        if case=='full':
            while True:
                try:os.write(w,b'x'*4096)
                except BlockingIOError:break
        elif case=='broken':os.close(r);r=None
        payload=dict(op='submit',id='test',text='日本語' if case=='normal' else 'x'*(capacity+100))
        first=sender.send('test',payload);retry=sender.send('test',payload)
        assert retry['replayed'] and len(writer.records)==1
        record=writer.records[0]
        if case=='normal':
            assert first['state']=='stdin_flushed' and not writer.poisoned
            os.set_blocking(r,False);data=os.read(r,65536)
            assert json.loads(data)==payload and data.endswith(b'\n')
        else:
            assert first['state']=='write_uncertain' and writer.poisoned
            if case=='partial':assert 0<record['sent']<record['total']
            else:assert record['sent']==0
            second=sender.send('later',dict(op='cancel',id='test'))
            assert second['state']=='write_uncertain' and len(writer.records)==1
        rows.append(dict(case=case,pipe_capacity=capacity,first=first,retry=retry,write=record))
    finally:
        if r is not None:os.close(r)
        os.close(w)
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'bounded_pipe_writer.py',HERE/'command_once.py')},indent=2)+'\n')
print(json.dumps([dict(case=r['case'],sent=r['write']['sent'],total=r['write']['total'],outcome=r['write']['outcome'],elapsed_ms=(r['write']['finished_ns']-r['write']['started_ns'])/1e6) for r in rows],indent=2))
