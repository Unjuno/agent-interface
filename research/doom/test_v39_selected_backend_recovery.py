"""Joined current helpers/AST + selected backend/Executor/pipes; Fake X/HUD."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'live_control'),str(HERE.parents[1])]

def child(blocked):
    from unittest.mock import patch
    import test_map01_process_identity_backend as fixture
    phase={'health':100,'ammo':4};release_gate=threading.Event();terminal_gate=threading.Event()
    output_lock=threading.Lock();edges=[]
    def emit(row):
        with output_lock:print(json.dumps(row),flush=True)
    original_reader=fixture.SignalReader.read_frame
    def read_frame(self,*args):
        row=original_reader(self,*args);row['value']=phase[self.name];return row
    with patch.object(fixture.SignalReader,'read_frame',read_frame),fixture.backend_fixture() as (backend,events,generation,fake):
        def backend_emit(row):events.append(row);emit(row)
        backend._external_emit=backend_emit
        original_send=fixture.native.xtest.fake_input.side_effect
        def send(connection,event,code):
            if blocked and event==fixture.native.X.KeyRelease and not release_gate.is_set():
                emit({'event':'fixture_release_blocked'})
                if not release_gate.wait(8):raise TimeoutError('fixture release timeout')
            original_send(connection,event,code)
            edge=dict(event='fixture_key_edge',native_event=event,code=code,thread=threading.get_ident(),fake_down=sorted(fake.down))
            edges.append(edge);emit(edge)
        original_execute=backend.execute
        def execute(*args):
            try:return original_execute(*args)
            except Exception:
                emit({'event':'fixture_before_terminal'})
                if not terminal_gate.wait(5):raise TimeoutError('fixture terminal timeout')
                raise
        backend.execute=execute
        with patch.object(fixture.native.xtest,'fake_input',side_effect=send):
            executor=fixture.Executor(backend,emit)
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
                    source_pins=sorted(pins,key=lambda r:r['path']),sequence=backend.sequence))
                for line in sys.stdin:
                    command=json.loads(line);emit(dict(event='fixture_command',command=command));op=command['op']
                    if op=='submit':executor.submit('cover-0',[{'op':'hold','keys':['a'],'duration_ms':1000}],backend.sequence,time.perf_counter_ns()+5_000_000_000)
                    elif op=='phase':phase.update(command['values'])
                    elif op=='capture':phase.update(command['values']);backend.snapshot(command['tag'],0)
                    elif op=='cancel':executor.cancel(command['id'])
                    elif op=='resume-terminal':terminal_gate.set()
                    elif op=='resume-release':release_gate.set()
                    elif op=='inspect':
                        artifacts=[]
                        for path in sorted(backend.out.glob('*.png')):
                            b=path.read_bytes();artifacts.append(dict(name=path.name,sha256=hashlib.sha256(b).hexdigest(),bytes_b64=base64.b64encode(b).decode()))
                        emit(dict(event='fixture_inspection',fake_down=sorted(fake.down),edges=copy.deepcopy(edges),
                            artifacts=artifacts,custody=backend.executor_custody_snapshot()))
                    elif op=='finish':break
                    else:raise ValueError(op)
            finally:terminal_gate.set();release_gate.set();executor.close()
    emit({'event':'fixture_closed'})

if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='child':
    child(sys.argv[2]=='blocked');sys.exit(0)

from test_map01_v39_cancel_recovery_composition import current_wait,AUTHORED
import map01_overlap_controller_v39 as controller
ROWS=[]
class JoinedRecoveryTests(unittest.TestCase):
    def drive(self,signal='health',blocked=False,drop=False):
        command=[sys.executable,'-I',*(['-O'] if sys.flags.optimize else []),str(Path(__file__).resolve()),'child','blocked' if blocked else 'known']
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1)
        wire=[];incoming=queue.Queue();condition=threading.Condition();planner_events=[];result={};worker=None
        row=dict(signal=signal,blocked=blocked,drop=drop,pid=process.pid,command=command,wire=wire,planner_events=planner_events,forced_cleanup=False)
        def read():
            for line in process.stdout:
                value=json.loads(line)
                with condition:wire.append(value);condition.notify_all()
                incoming.put(value)
        reader=threading.Thread(target=read);reader.start()
        def wait(predicate):
            with condition:
                if not condition.wait_for(lambda:any(predicate(r) for r in wire),timeout=5):raise TimeoutError(str(predicate))
                return next(r for r in wire if predicate(r))
        def event(name):return wait(lambda r:r['event']==name)
        def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
        class SignalReader:
            def __init__(self,name):self.name=name
            def read(self,frame):return next(r for r in wire if r['event']=='typed_observation' and r['sequence']==frame['sequence'])['signals'][self.name]
        class Planner:
            def invalidate_turn(self,handle):planner_events.append('invalidate');return {'status':'invalidated'}
            def interrupt(self,handle):planner_events.append('interrupt');return {'status':'interrupt_requested'}
            def abort_pending_turn(self):planner_events.append('abort')
        try:
            event('fixture_ready');source=wait(lambda r:r['event']=='observation' and r['sequence']==1)
            monitor,admission=controller.build_cover_monitor(SignalReader('health'),source,AUTHORED,0,ammo_reader=SignalReader('ammo'),requires_ammo=True)
            row.update(source=copy.deepcopy(source),source_admission=admission)
            send({'op':'submit'});wait(lambda r:r['event']=='fixture_key_edge' and r['native_event']==2)
            send(dict(op='phase',values={'health':80 if signal=='health' else 100,'ammo':0 if signal=='ammo' else 4}))
            low=wait(lambda r:r['event']=='typed_observation' and r['sequence']>source['sequence'] and r['signals'][signal]['value']==(80 if signal=='health' else 0))
            row['low']=copy.deepcopy(low)
            invalidation=monitor.observe(low);self.assertIsNotNone(invalidation)
            actual_wait,latest=current_wait(incoming,process);handle=SimpleNamespace(turn_id='old-eligible')
            def cancel():
                try:result['returned']=controller.cancel_invalidated_cover(Planner(),handle,process,actual_wait,'cover-0')
                except Exception as error:result['failure']=dict(type=type(error).__name__,receipt=getattr(error,'cover_cancellation_receipt',None))
            worker=threading.Thread(target=cancel);worker.start();event('fixture_before_terminal')
            event('fixture_release_blocked' if blocked else 'input_released')
            send(dict(op='capture',tag='recovery',values={'health':96,'ammo':4}))
            recovered=wait(lambda r:r['event']=='observation' and r['id']=='recovery')
            row['barrier']=dict(worker_alive=worker.is_alive(),planner_events=planner_events.copy(),terminal_seen=any(r['event']=='terminal' for r in wire))
            send({'op':'resume-terminal'});worker.join(3)
            if worker.is_alive():raise TimeoutError('cancel did not settle')
            observed=time.perf_counter_ns();row['final']=controller.final_admission_from_planner_result(SimpleNamespace(handle=handle,status='completed',answer_eligible=True),observed,None if drop else invalidation,time.perf_counter_ns())
            fresh_monitor,fresh=controller.build_cover_monitor(SignalReader('health'),latest(),AUTHORED,1,ammo_reader=SignalReader('ammo'),requires_ammo=True)
            row.update(result=result,invalidation=invalidation,latest=copy.deepcopy(latest()),recovered=copy.deepcopy(recovered),fresh=fresh,
                       fresh_source=fresh_monitor.guards['health'].spec)
            send({'op':'inspect'});row['inspection']=event('fixture_inspection')
        finally:
            try:send({'op':'resume-release'});send({'op':'resume-terminal'});send({'op':'finish'})
            except (BrokenPipeError,OSError):pass
            try:process.stdin.close()
            except OSError as error:row['stdin_close_error']=str(error)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:row['forced_cleanup']=True;process.terminate();process.wait(timeout=3)
            if worker:worker.join(1)
            reader.join(1);row.update(exit_code=process.returncode,reader_alive=reader.is_alive(),cancel_thread_alive=worker.is_alive() if worker else False,stderr=process.stderr.read())
            process.stdout.close();process.stderr.close();ROWS.append(copy.deepcopy(row))
        self.assertEqual(row['exit_code'],0,row['stderr']);self.assertFalse(row['forced_cleanup']);self.assertFalse(row['reader_alive']);self.assertFalse(row['cancel_thread_alive'])
        self.assertEqual(row['barrier'],dict(worker_alive=True,planner_events=['invalidate'],terminal_seen=False))
        self.assertEqual(row['latest'],row['recovered']);self.assertGreater(row['latest']['sequence'],row['low']['sequence'])
        self.assertEqual(row['fresh_source']['source_sequence'],row['recovered']['sequence']);self.assertEqual(row['fresh_source']['source_value'],96)
        self.assertEqual(row['fresh']['status'],'admitted')
        self.assertEqual(row['final']['status'],'READY_FOR_ACTION_VALIDITY' if drop else 'REJECTED_POLICY_INVALIDATED')
        self.assertFalse(row['final']['input_authority_admitted']);self.assertIsNone(row['final']['executor_admission'])
        if blocked:
            self.assertEqual(planner_events,['invalidate','abort']);self.assertTrue(result['failure']['receipt']['input_recovery_required'])
            self.assertIsNotNone(row['inspection']['custody']['release_obligation']);self.assertEqual(row['inspection']['fake_down'],[38])
        else:
            self.assertEqual(planner_events,['invalidate','interrupt']);self.assertNotIn('failure',result)
            self.assertEqual(row['inspection']['fake_down'],[])
            self.assertEqual([(r['native_event'],r['code']) for r in row['inspection']['edges']],[(2,38),(3,38)])

    def test_health_and_ammo_recovery_during_selected_backend_cancel(self):
        for signal in ('health','ammo'):
            with self.subTest(signal=signal):self.drive(signal)
    def test_unknown_release_keeps_joined_path_quarantined(self):self.drive(blocked=True)
    def test_explicit_dropped_invalidation_control_changes_old_answer_gate(self):self.drive(drop=True)

if __name__=='__main__':unittest.main()
