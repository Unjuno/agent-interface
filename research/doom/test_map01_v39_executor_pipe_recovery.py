"""Real owned pipes/Executor workers; synthetic backend, not session main/native."""
import copy
import importlib
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'live_control')]

def frame(sequence,health,ammo,event='observation'):
    binding={'focus':7,'surface':9,'geometry':[0,0,640,480]}
    capture=1_000_000_000+sequence*100_000_000
    return dict(event=event,sequence=sequence,capture_ns=capture,pointer_binding=binding,
        frame_rgb_sha256=format(sequence,'064x'),signals={name:dict(status='observed',
        signal_id=name,value=value,sequence=sequence,capture_ns=capture,binding=copy.deepcopy(binding))
        for name,value in [('health',health),('ammo',ammo)]})

def child(version,unknown):
    Executor=importlib.import_module('executor_v'+version).Executor
    from executor_v3 import Cancelled
    lock=threading.Lock();resume=threading.Event()
    def emit(row):
        with lock:print(json.dumps(row),flush=True)
    class Backend:
        sequence=10
        def validate(self,steps):pass
        def execute(self,step,lease,identifier,index):
            emit({'event':'fixture_started','id':identifier})
            if not lease.cancel.wait(5):raise RuntimeError('fixture cancel timeout')
            release=self.release_all();release.update(reason='cancelled',valid_until_ns=lease.deadline)
            lease.record_interruption(release)
            self.sequence=12
            emit(frame(12,96,4,'typed_observation'));emit(frame(12,96,4))
            emit({'event':'fixture_terminal_pending','id':identifier})
            if not resume.wait(5):raise RuntimeError('fixture resume timeout')
            raise Cancelled()
        def release_all(self):
            return dict(event='owner_release',verified=not unknown,keys_down=[],buttons_down=[],
                keys_unknown=['CTRL'] if unknown else [],key_state_errors=[],verified_ns=time.perf_counter_ns())
    executor=Executor(Backend(),emit)
    pins=[]
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if not filename or not filename.endswith('.py'):continue
        path=Path(filename).resolve()
        try:relative=path.relative_to(HERE.parents[1]).as_posix()
        except ValueError:continue
        pins.append(dict(path=relative,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    emit({'event':'fixture_ready','pid':__import__('os').getpid(),'parent_pid':__import__('os').getppid(),'executor':version,
          'optimize':sys.flags.optimize,'source_pins':sorted(pins,key=lambda p:p['path'])})
    try:
        for line in sys.stdin:
            command=json.loads(line)
            if command['op']=='submit':executor.submit(command['id'],command['steps'],command['expected_sequence'],command['valid_until_ns'])
            elif command['op']=='cancel':executor.cancel(command['id'])
            elif command['op']=='fixture_resume_terminal':resume.set()
            elif command['op']=='fixture_close':break
            else:raise ValueError('unknown fixture command')
    finally:
        resume.set();executor.close()
    emit({'event':'fixture_closed'})

if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='child':
    child(sys.argv[2],sys.argv[3]=='unknown');sys.exit(0)

from test_map01_v39_cancel_recovery_composition import current_wait,Reader,AUTHORED
import map01_overlap_controller_v39 as controller
ROWS=[]

class PipeRecoveryTests(unittest.TestCase):
    def drive(self,version,signal='health',unknown=False,drop=False):
        command=[sys.executable,'-I',*(['-O'] if sys.flags.optimize else []),str(Path(__file__).resolve()),
                 'child',version,'unknown' if unknown else 'known']
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 text=True,encoding='utf-8',bufsize=1)
        incoming=queue.Queue();wire=[];condition=threading.Condition();planner_events=[]
        row=dict(version=version,signal=signal,unknown=unknown,drop=drop,pid=process.pid,
                 command=command,wire=wire,planner_events=planner_events,forced_cleanup=False)
        def read():
            for line in process.stdout:
                value=json.loads(line)
                with condition:wire.append(value);condition.notify_all()
                incoming.put(value)
        reader=threading.Thread(target=read);reader.start()
        def seen(event):
            with condition:
                if not condition.wait_for(lambda:any(r['event']==event for r in wire),timeout=3):
                    raise TimeoutError(event)
        def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
        class Planner:
            def invalidate_turn(self,handle):planner_events.append('invalidate');return {'status':'invalidated'}
            def interrupt(self,handle):planner_events.append('interrupt');return {'status':'interrupt_requested'}
            def abort_pending_turn(self):planner_events.append('abort')
        result={};worker=None
        try:
            seen('fixture_ready')
            monitor,_=controller.build_cover_monitor(Reader('health'),frame(10,100,4),AUTHORED,0,
                ammo_reader=Reader('ammo'),requires_ammo=True)
            low=frame(11,80 if signal=='health' else 100,0 if signal=='ammo' else 4,'typed_observation')
            invalidation=monitor.observe(low)
            send(dict(op='submit',id='cover-0',steps=[{'op':'fixture_hold'}],expected_sequence=10,
                      valid_until_ns=time.perf_counter_ns()+8_000_000_000))
            seen('fixture_started')
            wait,latest=current_wait(incoming,process)
            handle=SimpleNamespace(turn_id='old-eligible-turn')
            def cancel():
                try:result['returned']=controller.cancel_invalidated_cover(Planner(),handle,process,wait,'cover-0')
                except Exception as error:result['failure']=dict(type=type(error).__name__,receipt=getattr(error,'cover_cancellation_receipt',None))
            worker=threading.Thread(target=cancel);worker.start()
            seen('fixture_terminal_pending')
            row['barrier']=dict(cancel_thread_alive=worker.is_alive(),planner_events=planner_events.copy(),
                terminal_seen=any(r['event']=='terminal' for r in wire))
            send({'op':'fixture_resume_terminal'})
            worker.join(3)
            if worker.is_alive():raise TimeoutError('cancel helper did not settle')
            row.update(result=result,invalidation=invalidation,latest=copy.deepcopy(latest()))
            terminal_ns=time.perf_counter_ns()
            row['final']=controller.final_admission_from_planner_result(SimpleNamespace(handle=handle,
                status='completed',answer_eligible=True),terminal_ns,None if drop else invalidation,time.perf_counter_ns())
        finally:
            try:send({'op':'fixture_resume_terminal'});send({'op':'fixture_close'})
            except (BrokenPipeError,OSError):pass
            process.stdin.close()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                row['forced_cleanup']=True;process.terminate();process.wait(timeout=3)
            if worker is not None:worker.join(1)
            reader.join(1);row.update(exit_code=process.returncode,reader_alive=reader.is_alive(),
                cancel_thread_alive=worker.is_alive() if worker else False,stderr=process.stderr.read())
            process.stdout.close();process.stderr.close();ROWS.append(copy.deepcopy(row))
        self.assertFalse(row['forced_cleanup']);self.assertEqual(row['exit_code'],0,row['stderr'])
        self.assertFalse(row['reader_alive']);self.assertFalse(row['cancel_thread_alive'])
        self.assertTrue(row['barrier']['cancel_thread_alive'])
        self.assertEqual(row['barrier']['planner_events'],['invalidate'])
        self.assertFalse(row['barrier']['terminal_seen'])
        self.assertEqual(row['latest'],frame(12,96,4))
        accepted=next(r for r in wire if r['event']=='accepted')
        terminal=next(r for r in wire if r['event']=='terminal')
        self.assertEqual(terminal['id'],accepted['id'])
        self.assertEqual(sum(r['event']=='accepted' for r in wire),1)
        self.assertEqual(sum(r['event']=='step_started' for r in wire),1)
        if unknown:
            self.assertIn('failure',result);self.assertEqual(planner_events,['invalidate','abort'])
            self.assertTrue(result['failure']['receipt']['input_recovery_required'])
            self.assertFalse(result['failure']['receipt']['grants_input_authority'])
            self.assertEqual(terminal['status'],'failed');self.assertTrue(terminal['input_recovery_required'])
        else:
            self.assertNotIn('failure',result);self.assertEqual(planner_events,['invalidate','interrupt'])
            self.assertEqual(terminal['status'],'cancelled');self.assertTrue(terminal['release']['verified'])
            self.assertEqual(terminal['release']['keys_unknown'],[])
            release=next(r for r in wire if r['event']=='input_released')
            self.assertEqual(release['intent_token'],accepted['intent_token'])
            self.assertLess(wire.index(release),wire.index(terminal))
        self.assertEqual(row['final']['status'],'READY_FOR_ACTION_VALIDITY' if drop else 'REJECTED_POLICY_INVALIDATED')
        self.assertFalse(row['final']['input_authority_admitted'])
        return row

    def test_both_executor_workers_preserve_cancellation_and_recovery(self):
        for version in ('12','13'):
            for signal in ('health','ammo'):
                with self.subTest(version=version,signal=signal):self.drive(version,signal)

    def test_unknown_cleanup_blocks_planner_interrupt_and_retains_custody(self):
        for version in ('12','13'):
            with self.subTest(version=version):self.drive(version,unknown=True)

    def test_explicit_dropped_invalidation_control_cannot_count_as_old_policy_refusal(self):
        for version in ('12','13'):
            with self.subTest(version=version):self.drive(version,drop=True)

if __name__=='__main__':unittest.main()
