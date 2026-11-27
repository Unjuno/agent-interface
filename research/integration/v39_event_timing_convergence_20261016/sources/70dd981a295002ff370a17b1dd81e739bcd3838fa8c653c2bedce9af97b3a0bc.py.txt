"""Actual V39 reader/wait plus owned Python stdio; no game or platform input."""
import ast
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doom_controller_failure_cleanup_v1 as cleanup


def failure():
    return {'event':'control_boundary_failed', 'schema':'map01-control-retirement-failure-v1',
            'operation':'finish', 'executor_closed':True, 'active_intent':None,
            'release_obligation':{'id':'original', 'intent_token':'original-token',
                                  'release':{'verified':False}},
            'input_recovery_required':True, 'task_effect':'unknown',
            'grants_input_authority':False}


def actual_reader_wait(incoming, process, events, errors):
    source = Path(__file__).with_name('map01_overlap_controller_v39.py')
    tree = ast.parse(source.read_bytes(), filename=str(source))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    functions = {n.name:n for n in ast.walk(main) if isinstance(n, ast.FunctionDef)}
    arguments = ('incoming','process','all_events','reader_errors')
    wrapper = ast.FunctionDef(name='factory', args=ast.arguments(
        posonlyargs=[], args=[ast.arg(arg=n) for n in arguments], vararg=None,
        kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id='latest',ctx=ast.Store())],value=ast.Constant(None)),
              functions['reader'], functions['wait'],
              ast.Return(value=ast.Tuple(elts=[ast.Name(id='reader',ctx=ast.Load()),
                                              ast.Name(id='wait',ctx=ast.Load())],ctx=ast.Load()))],
        decorator_list=[])
    namespace = dict(time=time, queue=queue, json=json,
                     reject_duplicate_json_members=cleanup.reject_duplicate_json_members)
    if hasattr(cleanup, 'reject_control_boundary_failure'):
        namespace['reject_control_boundary_failure'] = cleanup.reject_control_boundary_failure
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),
                 str(source),'exec'),namespace)
    return namespace['factory'](incoming,process,events,errors)


class ControllerRetirementTests(unittest.TestCase):
    def test_failure_preempts_score_and_copies_original_obligation(self):
        rows=queue.Queue(); original=failure(); rows.put(original)
        rows.put({'event':'post_control_score'})
        reader,wait=actual_reader_wait(rows,SimpleNamespace(poll=lambda:None),[],[])
        with self.assertRaisesRegex(RuntimeError,'input retirement') as caught:
            wait(lambda row:row['event']=='post_control_score',timeout=.2)
        self.assertEqual(type(caught.exception).__name__,'SessionControlBoundaryFailure')
        original['release_obligation']['id']='external mutation'
        self.assertEqual(caught.exception.event['release_obligation']['id'],'original')
        self.assertEqual(rows.qsize(),1)

    def test_failure_preempts_predicate_and_observation_monitor(self):
        rows=queue.Queue(); row=failure(); rows.put(row); called=[]
        monitor=SimpleNamespace(event_types={'control_boundary_failed'},
                                observe=lambda r:called.append('monitor'))
        reader,wait=actual_reader_wait(rows,SimpleNamespace(poll=lambda:None),[],[])
        consumed=[]
        with self.assertRaisesRegex(RuntimeError,'input retirement'):
            wait(lambda r:called.append('predicate') or True, timeout=.2,
                 observation_monitor=monitor,consumed_events=consumed)
        self.assertEqual(called,[])
        self.assertEqual(consumed,[row])

    def test_incomplete_failure_payload_still_stops(self):
        rows=queue.Queue(); rows.put({'event':'control_boundary_failed'})
        reader,wait=actual_reader_wait(rows,SimpleNamespace(poll=lambda:None),[],[])
        with self.assertRaisesRegex(RuntimeError,'input retirement'):
            wait(lambda r:True,timeout=.2)

    def test_ordinary_score_path_unchanged(self):
        rows=queue.Queue(); expected={'event':'post_control_score'}; rows.put(expected)
        reader,wait=actual_reader_wait(rows,SimpleNamespace(poll=lambda:None),[],[])
        self.assertIs(wait(lambda r:r['event']=='post_control_score',timeout=.2),expected)

    def test_retained_failure_vetoes_otherwise_complete_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory); runtime=out/'runtime'; runtime.mkdir()
            (runtime/'score.json').write_text('{}')
            (runtime/'owner-events.json').write_text('[{"reason":"close","verified":true}]')
            events=[failure(),{'event':'post_control_score'}]
            child=SimpleNamespace(poll=lambda:0)
            reader=SimpleNamespace(join=lambda timeout:None,is_alive=lambda:False)
            planner=SimpleNamespace(close=lambda timeout=1:None)
            original=ValueError('original controller fault')
            with self.assertRaises(ValueError) as caught:
                with cleanup.ControllerFailureCleanup(planner,out) as scope:
                    scope.track(child); scope.observe_output(events,reader,None,runtime,[])
                    raise original
            self.assertIs(caught.exception,original)
            receipt=json.loads((out/'controller-failure.json').read_text())
            print(json.dumps({'case':'contradictory-cleanup-evidence','receipt':receipt}),flush=True)
            self.assertFalse(receipt['cleanup_complete'])
            self.assertFalse(receipt['input_releases_verified_empty'])
            self.assertEqual(receipt['control_boundary_failures'],[failure()])

    def test_real_stdio_failure_survives_later_score_and_cleanup(self):
        # The peer is a protocol fixture only. Its score and owner files are
        # deliberately synthetic contradictory evidence, never a task result.
        peer = "import json,sys\nprint(" + repr(json.dumps(failure())) + ",flush=True)\n" + (
            "sys.stdin.readline()\nprint(json.dumps({'event':'post_control_score'}),flush=True)\n")
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory); runtime=out/'runtime'; runtime.mkdir()
            (runtime/'score.json').write_text('{}')
            (runtime/'owner-events.json').write_text('[{"reason":"close","verified":true}]')
            child=subprocess.Popen([sys.executable,'-u','-c',peer],stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            events=[]; errors=[]; incoming=queue.Queue()
            reader,wait=actual_reader_wait(incoming,child,events,errors)
            thread=threading.Thread(target=reader)
            thread.start(); planner=SimpleNamespace(close=lambda timeout=1:None)
            def finish(stream,timeout):
                stream.write('{"op":"finish"}\n'); stream.flush()
            try:
                with patch.object(cleanup,'send_failure_finish',side_effect=finish):
                    with self.assertRaisesRegex(RuntimeError,'input retirement') as caught:
                        with cleanup.ControllerFailureCleanup(planner,out) as scope:
                            scope.track(child); scope.observe_output(events,thread,wait,runtime,errors)
                            scope.set_stage('final_score_wait')
                            wait(lambda r:r['event']=='post_control_score',timeout=2)
                self.assertEqual(type(caught.exception).__name__,'SessionControlBoundaryFailure')
                receipt=json.loads((out/'controller-failure.json').read_text())
                print(json.dumps({'case':'owned-stdio-retirement-failure', 'events':events,
                                  'receipt':receipt,'peer_exit':child.poll()}),flush=True)
                self.assertTrue(receipt['control_boundary_failed'])
                self.assertEqual(receipt['control_boundary_failures'],[failure()])
                self.assertEqual(receipt['task_effect'],'unknown')
                self.assertFalse(receipt['input_releases_verified_empty'])
                self.assertFalse(receipt['cleanup_complete'])
                self.assertTrue(receipt['scorer_terminal_observed'])
                self.assertTrue(receipt['stdout_reader_retired'])
                self.assertEqual(child.poll(),0)
                self.assertFalse(thread.is_alive())
            finally:
                if child.poll() is None: child.kill()
                child.wait(timeout=2); thread.join(timeout=2)
                for stream in (child.stdin,child.stdout,child.stderr): stream.close()


if __name__=='__main__': unittest.main()
