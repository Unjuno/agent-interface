"""Actual selected backend/owner/Executor across pipes; all X/capture is fake."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'live_control'),str(HERE.parents[1])]

def child(case):
    from unittest.mock import patch
    from test_map01_process_identity_backend import backend_fixture,Executor,native
    gate=threading.Event();output_lock=threading.Lock();edges=[]
    def emit(row):
        with output_lock:print(json.dumps(row),flush=True)
    with backend_fixture() as (backend,events,generation,fake):
        original=native.xtest.fake_input.side_effect
        def send(connection,event,code):
            if event==native.X.KeyRelease and case=='blocked-release' and not gate.is_set():
                emit({'event':'fixture_release_blocked','code':code})
                if not gate.wait(8):raise TimeoutError('fixture release was not resumed')
            result=original(connection,event,code)
            row=dict(event='fixture_key_edge',native_event=event,code=code,
                     thread=threading.get_ident(),fake_down=sorted(fake.down),at_ns=time.perf_counter_ns())
            edges.append(row);emit(row)
            return result
        with patch.object(native.xtest,'fake_input',side_effect=send):
            executor=Executor(backend,emit)
            try:
                backend.snapshot('source',0)
                pins=[]
                for module in tuple(sys.modules.values()):
                    filename=getattr(module,'__file__',None)
                    if not filename or not filename.endswith('.py'):continue
                    path=Path(filename).resolve()
                    try:name=path.relative_to(HERE.parents[1]).as_posix()
                    except ValueError:continue
                    pins.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
                emit(dict(event='fixture_ready',pid=os.getpid(),parent_pid=os.getppid(),optimize=sys.flags.optimize,
                    source_pins=sorted(pins,key=lambda r:r['path']),sequence=backend.sequence,
                    source_events=copy.deepcopy(events)))
                for line in sys.stdin:
                    command=json.loads(line);emit(dict(event='fixture_command',command=command))
                    op=command['op']
                    if op=='submit':executor.submit(command['id'],[{'op':'hold','keys':['a'],'duration_ms':500}],
                        command['sequence'],time.perf_counter_ns()+5_000_000_000)
                    elif op=='cancel':executor.cancel(command['id'])
                    elif op=='generation':generation[0]='b'*64
                    elif op=='close-executor':executor.close()
                    elif op=='resume-release':gate.set()
                    elif op=='settle':
                        if not backend.owner._inner.stopped.wait(3):raise TimeoutError('retired owner did not stop')
                        backend.snapshot('after-late-release',0)
                    elif op=='inspect':
                        replacement_refused=None
                        if command.get('replacement'):
                            replacement=None
                            try:replacement=Executor(backend,emit);replacement_refused=False
                            except ValueError:replacement_refused=True
                            finally:
                                if replacement is not None:replacement.close()
                        artifacts=[]
                        for path in sorted(backend.out.glob('*.png')):
                            b=path.read_bytes();artifacts.append(dict(name=path.name,sha256=hashlib.sha256(b).hexdigest(),
                                bytes_b64=base64.b64encode(b).decode()))
                        emit(dict(event='fixture_inspection',tag=command['tag'],fake_down=sorted(fake.down),
                            executor_closed=executor.closed,custody=backend.executor_custody_snapshot(),
                            replacement_refused=replacement_refused,backend_events=copy.deepcopy(events),
                            edges=copy.deepcopy(edges),artifacts=artifacts,owner_stopped=backend.owner._inner.stopped.is_set()))
                    elif op=='finish':break
                    else:raise ValueError(op)
            finally:gate.set();executor.close()
    emit({'event':'fixture_closed'})

if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='child':
    child(sys.argv[2]);sys.exit(0)

ROWS=[]
class BackendPipeTests(unittest.TestCase):
    def drive(self,case):
        command=[sys.executable,'-I',*(['-O'] if sys.flags.optimize else []),str(Path(__file__).resolve()),'child',case]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            text=True,encoding='utf-8',bufsize=1)
        wire=[];condition=threading.Condition()
        row=dict(case=case,pid=process.pid,command=command,wire=wire,forced_cleanup=False)
        def reader():
            for line in process.stdout:
                value=json.loads(line)
                with condition:wire.append(value);condition.notify_all()
        thread=threading.Thread(target=reader);thread.start()
        def wait(predicate):
            with condition:
                if not condition.wait_for(lambda:any(predicate(r) for r in wire),timeout=5):raise TimeoutError(case)
                return next(r for r in wire if predicate(r))
        def event(name):return wait(lambda r:r['event']==name)
        def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
        def inspect(tag,replacement=False):
            send(dict(op='inspect',tag=tag,replacement=replacement))
            return wait(lambda r:r['event']=='fixture_inspection' and r['tag']==tag)
        try:
            ready=event('fixture_ready')
            send(dict(op='submit',id='original',sequence=ready['sequence']))
            wait(lambda r:r['event']=='fixture_key_edge' and r['native_event']==2)
            if case=='generation':send({'op':'generation'})
            else:send({'op':'cancel','id':'original'})
            terminal=event('terminal');row['terminal']=terminal
            if case=='blocked-release':
                event('fixture_release_blocked');send({'op':'close-executor'})
                row['before_resume']=inspect('before',True)
                send({'op':'resume-release'});send({'op':'settle'})
                row['after_resume']=inspect('after',True)
            else:row['after']=inspect('after')
        finally:
            try:send({'op':'resume-release'});send({'op':'finish'})
            except (BrokenPipeError,OSError):pass
            process.stdin.close()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                row['forced_cleanup']=True;process.terminate();process.wait(timeout=3)
            thread.join(1);row.update(exit_code=process.returncode,reader_alive=thread.is_alive(),stderr=process.stderr.read())
            process.stdout.close();process.stderr.close();ROWS.append(copy.deepcopy(row))
        self.assertEqual(row['exit_code'],0,row['stderr']);self.assertFalse(row['forced_cleanup']);self.assertFalse(row['reader_alive'])
        ready=next(r for r in wire if r['event']=='fixture_ready')
        source=next(r for r in ready['source_events'] if r['event']=='observation')
        self.assertEqual(source['target_process_identity']['digest'],'a'*64)
        self.assertEqual(sum(r['event']=='accepted' for r in wire),1)
        if case=='blocked-release':
            before,after=row['before_resume'],row['after_resume']
            self.assertFalse(terminal['release']['verified']);self.assertTrue(terminal['input_recovery_required'])
            self.assertEqual(before['fake_down'],[38]);self.assertEqual(after['fake_down'],[])
            self.assertTrue(before['replacement_refused']);self.assertTrue(after['replacement_refused'])
            self.assertEqual(before['custody']['release_obligation'],after['custody']['release_obligation'])
            self.assertIsNotNone(after['custody']['release_obligation'])
            self.assertTrue(after['owner_stopped'])
            final=after
        else:
            self.assertTrue(terminal['release']['verified']);self.assertEqual(row['after']['fake_down'],[])
            self.assertEqual(terminal['status'],'needs_decision' if case=='generation' else 'cancelled')
            final=row['after']
        self.assertEqual([(e['native_event'],e['code']) for e in final['edges']],[(2,38),(3,38)])
        self.assertEqual(len({e['thread'] for e in final['edges']}),1)
        self.assertTrue(final['artifacts'])
        for artifact in final['artifacts']:
            self.assertEqual(hashlib.sha256(base64.b64decode(artifact['bytes_b64'])).hexdigest(),artifact['sha256'])

    def test_cancel_actual_selected_owner_over_pipe(self):self.drive('cancel')
    def test_generation_change_autonomously_releases(self):self.drive('generation')
    def test_late_release_keeps_backend_custody_quarantined(self):self.drive('blocked-release')

if __name__=='__main__':unittest.main()
