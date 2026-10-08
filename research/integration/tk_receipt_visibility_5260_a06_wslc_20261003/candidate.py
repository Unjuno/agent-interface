"""One no-GUI/no-input publication/reader phase construction."""
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def planned_rows(fixture):
    rows=[{'filesystem':fs,'phase':phase,'load':load}
          for fs in ('HOST_BIND','CONTAINER_TMP')
          for phase in ('PUBLISH_DELAY','READER_DELAY')
          for load in ('idle','cpu_busy')]
    random.Random(fixture['seed']).shuffle(rows)
    return rows


def writer(path,token,delay_ms):
    path=Path(path)
    payload={'schema':'issue5260-a06-token-v1','token':token,'pid':os.getpid(),
             'stamp_ns':time.monotonic_ns()}
    print(json.dumps(payload,sort_keys=True),flush=True)
    if delay_ms:
        time.sleep(delay_ms/1000)
    trace={'stamp_ns':payload['stamp_ns'],'publish_started_ns':time.monotonic_ns()}
    temporary=path.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        stream.write((json.dumps(payload,sort_keys=True,separators=(',',':'))+'\n').encode())
        stream.flush()
        trace['write_finished_ns']=time.monotonic_ns()
        os.fsync(stream.fileno())
        trace['fsync_finished_ns']=time.monotonic_ns()
    trace['replace_started_ns']=time.monotonic_ns()
    temporary.replace(path)
    trace['replace_finished_ns']=time.monotonic_ns()
    print(json.dumps(trace,sort_keys=True),flush=True)
    return 0


def read_payload(path,timeout_ms):
    deadline=time.monotonic_ns()+timeout_ms*1_000_000
    attempts=[]
    while time.monotonic_ns()<deadline:
        before=time.monotonic_ns()
        try:
            blob=Path(path).read_bytes()
            payload=json.loads(blob)
            after=time.monotonic_ns()
            if after>=deadline:
                raise TimeoutError('STOP_READ_DEADLINE')
            attempts.append({'start_ns':before,'end_ns':after,'status':'READ_OK',
                             'sha256':hashlib.sha256(blob).hexdigest()})
            return payload,blob,attempts
        except (OSError,ValueError) as error:
            attempts.append({'start_ns':before,'end_ns':time.monotonic_ns(),
                             'status':type(error).__name__})
        time.sleep(0.001)
    raise TimeoutError('STOP_READ_DEADLINE:'+json.dumps(attempts))


def worker_code():
    return ("import json,time;start=time.monotonic_ns();end=time.monotonic()+0.3;x=1\n"
            "while time.monotonic()<end:x=(x*1664525+1013904223)&0xffffffff\n"
            "print(json.dumps({'start_ns':start,'end_ns':time.monotonic_ns()}),flush=True)")


def run(fixture_path,out_path):
    source=Path(__file__).resolve().parent
    fixture=json.loads(Path(fixture_path).read_bytes())
    freeze=json.loads((source/'FREEZE.json').read_bytes())
    out=Path(out_path)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('STOP_OUTPUT_OCCUPIED')
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for index,plan in enumerate(planned_rows(fixture)):
        row_dir=out/f'row-{index:03d}';row_dir.mkdir()
        live_path=(row_dir if plan['filesystem']=='HOST_BIND' else
                   Path(tempfile.mkdtemp(prefix='5260-a06-row-')))/'receipt.json'
        token=fixture['allocation']+f':row-{index:03d}'
        row={'index':index,**plan,'token':token,'live_path':str(live_path)}
        process=worker=None
        try:
            if plan['load']=='cpu_busy':
                worker=subprocess.Popen([sys.executable,'-c',worker_code()],
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            delay=fixture['imposed_delay_ms'] if plan['phase']=='PUBLISH_DELAY' else 0
            process=subprocess.Popen([sys.executable,'-B',str(source/'candidate.py'),
                '--writer',str(live_path),token,str(delay)],stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True)
            initial=process.stdout.readline()
            announced=json.loads(initial)
            row['writer_pid']=process.pid
            started=time.monotonic_ns()
            if plan['phase']=='READER_DELAY':
                time.sleep(fixture['imposed_delay_ms']/1000)
            delay_end=time.monotonic_ns()
            payload,blob,attempts=read_payload(live_path,fixture['read_timeout_ms'])
            process.wait(timeout=2)
            rest=process.stdout.read()
            stderr=process.stderr.read()
            trace=json.loads(rest.strip())
            row.update(payload=payload,announced=announced,
                payload_sha256=hashlib.sha256(blob).hexdigest(),attempts=attempts,
                writer=trace,writer_exit=process.returncode,
                writer_stdout=initial+rest,writer_stderr=stderr,
                reader={'start_ns':started,'delay_end_ns':delay_end,
                        'first_read_started_ns':attempts[-1]['start_ns'],
                        'first_read_finished_ns':attempts[-1]['end_ns']})
            (row_dir/'payload.bin').write_bytes(blob)
            if worker:
                stdout,stderr=worker.communicate(timeout=2)
                row.update(worker_pid=worker.pid,worker_exit=worker.returncode,
                           worker_stdout=stdout,worker_stderr=stderr)
            else:
                row.update(worker_pid=None,worker_exit=None)
        except Exception as error:
            row['runner_error']=type(error).__name__+':'+str(error)
        finally:
            for child in (process,worker):
                if child and child.poll() is None:
                    child.kill();child.communicate()
        rows.append(row)
        if row.get('runner_error'):break
    raw={'schema':fixture['schema'],'allocation':fixture['allocation'],'fixture':fixture,
         'schedule':planned_rows(fixture),'rows':rows,'image_id':os.environ.get('EXPERIMENT_IMAGE_ID'),
         'python':sys.version,'container_id':os.environ.get('HOSTNAME'),
         'source_sha256':{name:sha(source/name) for name in freeze['sha256']},
         'freeze_sha256':sha(source/'FREEZE.json'),'fixture_sha256':sha(fixture_path)}
    (out/'candidate_stdout.json').write_text(json.dumps(raw,sort_keys=True)+'\n',encoding='utf-8')
    exit_code=0 if len(rows)==8 and not any(row.get('runner_error') for row in rows) else 1
    (out/'candidate_exit.txt').write_text(str(exit_code)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'exit_code':exit_code},sort_keys=True))
    return exit_code


if __name__=='__main__':
    if sys.argv[1]=='--writer':
        raise SystemExit(writer(sys.argv[2],sys.argv[3],int(sys.argv[4])))
    raise SystemExit(run(sys.argv[1],sys.argv[2]))
