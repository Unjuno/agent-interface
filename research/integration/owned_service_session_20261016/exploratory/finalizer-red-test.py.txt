"""Session/controller selection qualification without any game or model."""
import importlib.util
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import ModuleType,SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'live_control'),str(HERE.parents[1])]
import test_owned_owner_backend_adapter as fixtures
from test_input_owner_process_v3 import fake_owner_start_error,edges

ROWS=[]


def helper():
    import session_owned_owner_backend
    return session_owned_owner_backend


def saved(path):
    result={}
    for item in sorted(Path(path).rglob('*')):
        if item.is_file():
            raw=item.read_bytes();result[item.relative_to(path).as_posix()]=dict(
                sha256=hashlib.sha256(raw).hexdigest(),bytes_b64=base64.b64encode(raw).decode('ascii'))
    return result


class OwnedSessionTests(unittest.TestCase):
    def test_owned_session_backend_available(self):
        self.assertIsNotNone(importlib.util.find_spec('session_owned_owner_backend'),
                             'selected session owner custody wrapper absent')

    def test_controller_requires_qualified_selection_and_forwards_flag(self):
        import map01_overlap_controller_v39 as controller
        args=NS(measurement_session=True,target_process_identity=True,target_window_lifecycle=False,
                owned_input_service=True,seed=7,load_fixture_manifest=Path('fixture.json'))
        command=controller.session_command(args,Path('runtime'))
        self.assertIn('--owned-input-service',command)
        invalid=[]
        for field,value in (('measurement_session',False),('target_process_identity',False),('target_window_lifecycle',True)):
            changed=copy.copy(args);setattr(changed,field,value)
            with self.subTest(field=field),self.assertRaises(ValueError):controller.session_command(changed,Path('runtime'))
            invalid.append(field)
        ROWS.append(dict(case='controller-selection',command=command,invalid_refused=invalid,scope='pure command; no process'))

    def test_v15_selects_wrapper_strips_flag_and_pins_sources(self):
        import session_map01_v15 as session
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'sources.json').write_text('{}')
            base=ModuleType('session_map01_v12');base.vd=NS(DoomGame=object,GameVariable=object)
            base.sys=NS(stdin=object());seen=[]
            base.main=lambda:seen.append((base.Backend,list(sys.argv)))
            argv=['session','--out',temp,'--target-process-identity','--owned-input-service']
            with patch.dict(sys.modules,{'session_map01_v12':base}),patch.object(session,'MainThreadScorerStdin',return_value=Mock()),patch.object(
                    session,'ScorerFileSink',return_value=Mock()),patch.object(sys,'argv',argv):session.main()
            self.assertIs(seen[0][0],helper().Backend)
            self.assertNotIn('--owned-input-service',seen[0][1]);self.assertNotIn('--target-process-identity',seen[0][1])
            manifest=json.loads((Path(temp)/'target-process-identity-sources.json').read_text())
            self.assertTrue(manifest['owned_input_service'])
            self.assertIn('research/doom/session_owned_owner_backend.py',manifest['files'])
            ROWS.append(dict(case='v15-selection',flags_stripped=True,wrapper_selected=True,manifest=manifest,files=saved(temp)))

    def run_session(self,blocked):
        with tempfile.TemporaryDirectory() as temp:
            row=dict(case='blocked-close' if blocked else 'normal-close');backend=executor=None
            entered=threading.Event();resume=threading.Event()
            def selected(*args,**kwargs):
                kwargs.pop('owner_service',None)
                return helper().Backend(*args,**kwargs,_owner_factory=fixtures.child_geometry)
            manager=None
            try:
                with patch.object(fixtures,'Backend',selected):
                    manager=fixtures.parent_backend(temp,None)
                    backend,events,_=manager.__enter__();backend.snapshot('source',0)
                    original=backend.raw
                    def raw(key,down):
                        result=original(key,down)
                        if blocked and down:
                            entered.set()
                            if not resume.wait(6):raise RuntimeError('test worker pause deadline')
                        return result
                    backend.raw=raw;executor=fixtures.Executor(backend,events.append)
                    executor.submit(row['case'],[{'op':'hold','keys':['a'],'duration_ms':5}],backend.sequence,
                                    time.perf_counter_ns()+10_000_000_000)
                    worker=executor.active[2] if executor.active else None
                    service=backend.owned_service
                    if blocked:
                        self.assertTrue(entered.wait(2));(service.out/'fixture-block-release').touch()
                        executor.cancel(row['case']);first=backend.owner.control.wait(backend.lease.intent_token,3)
                        self.assertFalse(first['release_verified']);row['first_control']=first
                        (service.out/'fixture-resume-release').touch();resume.set()
                    if worker:worker.join(4)
                    self.assertFalse(worker and worker.is_alive())
                    executor.close();row['terminal']=[e for e in events if e.get('event')=='terminal'][-1]
                    if blocked:
                        with self.assertRaises(helper().OwnerServiceCleanupUnverified):backend.close()
                        self.assertFalse(json.loads((Path(temp)/'session-owner-service-close.json').read_text())['verified'])
                    else:self.assertTrue(backend.close()['verified'])
                    row['events']=events
            finally:
                resume.set()
                if backend is not None:
                    (backend.owned_service.out/'fixture-resume-release').touch()
                    if executor:executor.close()
                    if manager:
                        try:manager.__exit__(None,None,None)
                        except helper().OwnerServiceCleanupUnverified:
                            if not blocked:raise
                    row.update(startup=backend.owned_service.startup,spawn_pid=backend.owned_service.process.pid,
                               service_report=backend.owned_service.wait(6),edges=edges(backend.owned_service.out),files=saved(temp))
                    self.assertFalse(backend.owned_service.process.is_alive())
                ROWS.append(row)

    def test_actual_session_wrapper_normal_cleanup(self):self.run_session(False)
    def test_session_close_refuses_late_upgrade(self):self.run_session(True)

    def test_effect_fence_checks_adapter_obligation(self):
        source=HERE/'session_map01_v12.py';tree=ast.parse(source.read_bytes())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='close_before_control_effect')
        namespace=dict(Path=Path,json=json)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),namespace)
        executor=NS(close=lambda:None,lock=threading.RLock(),release_obligation_snapshot=lambda:None,closed=True,active=None,
                    backend=NS(executor_custody_snapshot=lambda:dict(owner_service_obligation={'kind':'unverified'})))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):namespace['close_before_control_effect'](executor,Path(temp),lambda _:None,'finish')
            record=json.loads((Path(temp)/'control-boundary-failure.json').read_text())
            self.assertIsNotNone(record['owner_service_obligation'])
            ROWS.append(dict(case='effect-fence',record=record,scope='exact function AST/inert executor; no engine'))

    def test_startup_failure_preserves_handle_and_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(Exception) as caught:
                helper().Backend(NS(name=':fake'),Path(temp),lambda _:None,{},_owner_factory=fake_owner_start_error)
            service=caught.exception.owner_service_handle
            report=service.wait(5)
            self.assertFalse(report['process_alive']);self.assertFalse(report['verified'])
            self.assertTrue((Path(temp)/'session-owner-service-startup-failure.json').exists())
            ROWS.append(dict(case='startup-failure',spawn_pid=service.process.pid,service_report=report,files=saved(temp)))

    def test_startup_receipt_collision_cleans_owned_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'session-owner-service-startup.json';original=b'first startup artifact\n';path.write_bytes(original)
            def selected(*args,**kwargs):
                kwargs.pop('owner_service',None)
                return helper().Backend(*args,**kwargs,_owner_factory=fixtures.child_geometry)
            with patch.object(fixtures,'Backend',selected),self.assertRaises(FileExistsError) as caught:
                with fixtures.parent_backend(temp,None):pass
            service=caught.exception.owner_service_handle;report=service.wait(5)
            self.assertFalse(report['process_alive']);self.assertEqual(path.read_bytes(),original)
            self.assertTrue((Path(temp)/'session-owner-service-startup-failure.json').exists())
            ROWS.append(dict(case='startup-collision',startup=service.startup,spawn_pid=service.process.pid,
                             service_report=report,original_unchanged=True,files=saved(temp)))

    def test_close_publication_failure_remains_unverified(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'session-owner-service-close.json';original=b'first close artifact\n';path.write_bytes(original)
            backend=None
            def selected(*args,**kwargs):
                kwargs.pop('owner_service',None)
                return helper().Backend(*args,**kwargs,_owner_factory=fixtures.child_geometry)
            with patch.object(fixtures,'Backend',selected),self.assertRaises(BaseException):
                with fixtures.parent_backend(temp,None) as (backend,_,_):backend.close()
            self.assertIsNotNone(backend);service=backend.owned_service;report=service.wait(5)
            self.assertFalse(backend._session_close['verified'])
            self.assertEqual(path.read_bytes(),original);self.assertFalse(report['process_alive'])
            ROWS.append(dict(case='close-publication-failure',startup=service.startup,spawn_pid=service.process.pid,
                service_report=report,cached_receipt=copy.deepcopy(backend._session_close),
                original_unchanged=True,files=saved(temp)))

    def test_primary_and_cached_cleanup_errors_are_preserved(self):
        backend=helper().Backend.__new__(helper().Backend)
        backend._session_lock=threading.RLock();backend.owned_service=object()
        backend._session_close={'verified':False};cleanup=helper().OwnerServiceCleanupUnverified(backend._session_close)
        backend._session_error=cleanup;primary=KeyboardInterrupt('original caller interruption')
        with self.assertRaises(BaseExceptionGroup) as caught:
            try:raise primary
            except KeyboardInterrupt:backend.close()
        self.assertIs(caught.exception.exceptions[0],primary);self.assertIs(caught.exception.exceptions[1],cleanup)
        ROWS.append(dict(case='paired-close-errors',primary_preserved=True,cleanup_preserved=True,scope='inert cached close; no process'))

    def test_v15_finalizers_do_not_replace_primary_or_each_other(self):
        import session_map01_v15 as session
        base=ModuleType('session_map01_v12');base.vd=NS(DoomGame=object,GameVariable=object);base.sys=NS(stdin=object())
        primary=KeyboardInterrupt('base session interrupted');sink_error=OSError('scorer finalizer');source_error=ValueError('source finalizer')
        def main():raise primary
        base.main=main;sink=Mock();sink.finalize.side_effect=sink_error
        with tempfile.TemporaryDirectory() as temp,patch.dict(sys.modules,{'session_map01_v12':base}),patch.object(
                session,'MainThreadScorerStdin',return_value=Mock()),patch.object(session,'ScorerFileSink',return_value=sink),patch.object(
                session,'_merge_sources',side_effect=source_error),patch.object(sys,'argv',['session','--out',temp,'--target-process-identity','--owned-input-service']):
            with self.assertRaises(BaseExceptionGroup) as caught:session.main()
        self.assertEqual(caught.exception.exceptions,(primary,sink_error,source_error))
        ROWS.append(dict(case='v15-finalizer-errors',all_three_preserved=True,scope='inert base session/finalizers; no process'))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OwnedSessionTests))
    Path(sys.argv[1]).write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),optimize=sys.flags.optimize,rows=ROWS),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
