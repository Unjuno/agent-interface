"""Owned session close must not claim completion while startup is in flight."""
import asyncio
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import metadata


class OwnedStartCloseTests(unittest.TestCase):
    def test_unregistered_failed_owner_does_not_claim_child_dead(self):
        with tempfile.TemporaryDirectory() as directory:
            owner=OwnedGuardedSessionOwner({'app':20},directory)
            self.assertIs(owner.snapshot()['owner_process']['alive'],False)
            owner.state='failed'
            process=owner.snapshot()['owner_process']
            self.assertIsNone(process['alive'])
            self.assertIsNone(process['retired'])
            self.assertIsNone(process['liveness_observed_monotonic_ns'])

    def test_close_after_spawn_before_registration_is_busy(self):
        with tempfile.TemporaryDirectory() as directory:
            owner=OwnedGuardedSessionOwner({'app':20},directory,
                process_identity=True,query_worker=True,_owner_factory=_fake_owner_factory)
            entered=threading.Event();resume=threading.Event();spawned=[];errors=[]
            original=multiprocessing.process.BaseProcess.start
            def gated_start(process):
                original(process);spawned.append(process);entered.set()
                if not resume.wait(5):raise TimeoutError('start fixture gate')
            def start_owner():
                try:owner._ensure_started()
                except BaseException as error:errors.append(type(error).__name__)
            worker=threading.Thread(target=start_owner)
            try:
                with patch.object(multiprocessing.process.BaseProcess,'start',gated_start):
                    worker.start();self.assertTrue(entered.wait(3))
                    report=owner.close()
                    self.assertEqual(report.get('status'),'busy',report)
                    self.assertFalse(report.get('verified',False))
                    self.assertIsNone(owner.close_report)
                    resume.set();worker.join(5)
                self.assertFalse(worker.is_alive())
                self.assertFalse(errors,errors)
                self.assertTrue(owner._process.is_alive())
                final=owner.close()
                self.assertFalse(owner._process.is_alive(),final)
                self.assertEqual(final.get('status'),'closed',final)
                self.assertTrue(final.get('verified'),final)
            finally:
                resume.set();worker.join(5)
                for process in spawned:
                    if process.is_alive():process.kill()
                    process.join(3)
                    self.assertFalse(process.is_alive(),'fixture child cleanup failed')
                worker.join(3)
                self.assertFalse(worker.is_alive(),'fixture startup thread did not finish')


class OwnedStartCloseMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_shutdown_busy_persists_pending_without_overwriting_prior(self):
        with tempfile.TemporaryDirectory() as directory:
            captured=[];original_init=OwnedGuardedSessionOwner.__init__
            entered=threading.Event();resume=threading.Event();written=threading.Event()
            spawned=[];errors=[]
            from runtime.cli_v1.mcp_server import _write_json as original_write
            def observe_write(path,value):
                result=original_write(path,value)
                if '-close-pending-' in Path(path).name:written.set()
                return result
            def capture(owner,*args,**kwargs):
                original_init(owner,*args,**kwargs);captured.append(owner)
            with patch.object(OwnedGuardedSessionOwner,'__init__',capture):
                server=create_server({'app':20},directory,session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,
                    guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            owner=captured[0];original_start=multiprocessing.process.BaseProcess.start
            prior=Path(directory)/('session-'+owner.session_id+'-close.json')
            prior.write_bytes(b'{"previous":"preserve"}')
            def gated_start(process):
                original_start(process);spawned.append(process);entered.set()
                if not resume.wait(5):raise TimeoutError('start fixture gate')
            def start_owner():
                try:owner._ensure_started()
                except BaseException as error:errors.append(type(error).__name__)
            worker=threading.Thread(target=start_owner)
            lifespan=server.settings.lifespan(server);await lifespan.__aenter__();exiting=None
            try:
                with patch.object(multiprocessing.process.BaseProcess,'start',gated_start), \
                     patch('runtime.cli_v1.mcp_server._write_json',side_effect=observe_write):
                    worker.start();self.assertTrue(await asyncio.to_thread(entered.wait,3))
                    exiting=asyncio.create_task(lifespan.__aexit__(None,None,None))
                    self.assertTrue(await asyncio.to_thread(written.wait,2),'pending receipt not written')
                    pending=list(Path(directory).glob('session-*-close-pending-*.json'))
                    self.assertEqual(len(pending),1)
                    record=json.loads(pending[0].read_text())
                    self.assertEqual(record['status'],'busy')
                    self.assertEqual(record['cleanup_status'],'UNKNOWN')
                    self.assertFalse(record['replay_allowed'])
                    self.assertEqual(prior.read_bytes(),b'{"previous":"preserve"}')
                    evidence=os.environ.get('AGENT_INTERFACE_LIFECYCLE_EVIDENCE')
                    if evidence:
                        target=Path(evidence)/'shutdown-receipt';target.mkdir(parents=True,exist_ok=False)
                        shutil.copy2(pending[0],target/'pending.json')
                        shutil.copy2(prior,target/'prior.json')
                    resume.set();await asyncio.to_thread(worker.join,5)
                    self.assertFalse(worker.is_alive());self.assertFalse(errors,errors)
                    await asyncio.wait_for(asyncio.shield(exiting),5)
            finally:
                resume.set();await asyncio.to_thread(worker.join,5)
                try:
                    if exiting is None:await lifespan.__aexit__(None,None,None)
                    else:await asyncio.wait_for(asyncio.shield(exiting),5)
                finally:
                    for process in spawned:
                        if process.is_alive():process.kill()
                        await asyncio.to_thread(process.join,3)
                        self.assertFalse(process.is_alive(),'fixture child cleanup failed')
                    await asyncio.to_thread(worker.join,3)
                    self.assertFalse(worker.is_alive(),'fixture startup thread did not finish')

    async def test_shutdown_during_direct_start_retains_child_custody(self):
        with tempfile.TemporaryDirectory() as directory:
            captured=[];original_init=OwnedGuardedSessionOwner.__init__
            entered=threading.Event();resume=threading.Event();spawned=[];errors=[]
            pending_written=threading.Event()
            from runtime.cli_v1.mcp_server import _write_json as original_write
            def observe_write(path,value):
                result=original_write(path,value)
                if '-close-pending-' in Path(path).name:pending_written.set()
                return result
            def capture(owner,*args,**kwargs):
                original_init(owner,*args,**kwargs);captured.append(owner)
            with patch.object(OwnedGuardedSessionOwner,'__init__',capture):
                server=create_server({'app':20},directory,session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,
                    guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            owner=captured[0];original_start=multiprocessing.process.BaseProcess.start
            prior=Path(directory)/('session-'+owner.session_id+'-close.json')
            prior.write_bytes(b'{"previous":"preserve"}')
            def gated_start(process):
                original_start(process);spawned.append(process);entered.set()
                if not resume.wait(5):raise TimeoutError('start fixture gate')
            def start_owner():
                try:owner._ensure_started()
                except BaseException as error:errors.append(type(error).__name__)
            worker=threading.Thread(target=start_owner)
            lifespan=server.settings.lifespan(server);await lifespan.__aenter__()
            exiting=None
            try:
                with patch.object(multiprocessing.process.BaseProcess,'start',gated_start), \
                     patch('runtime.cli_v1.mcp_server._write_json',side_effect=observe_write):
                    worker.start();self.assertTrue(await asyncio.to_thread(entered.wait,3))
                    exiting=asyncio.create_task(lifespan.__aexit__(None,None,None))
                    pending_observed=await asyncio.to_thread(pending_written.wait,1.5)
                    finished_while_busy=exiting.done()
                    resume.set();await asyncio.to_thread(worker.join,5)
                    self.assertFalse(worker.is_alive());self.assertFalse(errors,errors)
                    await asyncio.wait_for(asyncio.shield(exiting),5)
                    if pending_observed or finished_while_busy:
                        pending=list(Path(directory).glob('session-*-close-pending-*.json'))
                        self.assertEqual(len(pending),1)
                        record=json.loads(pending[0].read_text())
                        self.assertEqual(record['status'],'busy')
                        self.assertEqual(record['cleanup_status'],'UNKNOWN')
                        self.assertFalse(record['replay_allowed'])
                        self.assertEqual(prior.read_bytes(),b'{"previous":"preserve"}')
                        evidence=os.environ.get('AGENT_INTERFACE_LIFECYCLE_EVIDENCE')
                        if evidence:
                            target=Path(evidence)/'shutdown-busy';target.mkdir(parents=True,exist_ok=False)
                            shutil.copy2(pending[0],target/'pending.json')
                            shutil.copy2(prior,target/'prior.json')
                    self.assertFalse(owner._process.is_alive(),
                                     'shutdown returned while startup child remained alive')
            finally:
                resume.set();await asyncio.to_thread(worker.join,5)
                try:
                    if exiting is None:await lifespan.__aexit__(None,None,None)
                    else:await asyncio.wait_for(asyncio.shield(exiting),5)
                finally:
                    for process in spawned:
                        if process.is_alive():process.kill()
                        await asyncio.to_thread(process.join,3)
                        self.assertFalse(process.is_alive(),'fixture child cleanup failed')
                    await asyncio.to_thread(worker.join,3)
                    self.assertFalse(worker.is_alive(),'fixture startup thread did not finish')

    async def test_busy_close_during_direct_start_can_be_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            captured=[];original_init=OwnedGuardedSessionOwner.__init__
            entered=threading.Event();resume=threading.Event();spawned=[];errors=[]
            def capture(owner,*args,**kwargs):
                original_init(owner,*args,**kwargs);captured.append(owner)
            with patch.object(OwnedGuardedSessionOwner,'__init__',capture):
                server=create_server({'app':20},directory,session_mode='guarded-x11',
                    guarded_process_identity=True,guarded_query_worker=True,
                    guarded_owned_process=True,_guarded_owner_factory=_fake_owner_factory)
            owner=captured[0];original_start=multiprocessing.process.BaseProcess.start
            prior=Path(directory)/('session-'+owner.session_id+'-close.json')
            prior.write_bytes(b'{"previous":"preserve"}')
            def gated_start(process):
                original_start(process);spawned.append(process);entered.set()
                if not resume.wait(5):raise TimeoutError('start fixture gate')
            def start_owner():
                try:owner._ensure_started()
                except BaseException as error:errors.append(type(error).__name__)
            worker=threading.Thread(target=start_owner)
            try:
                with patch.object(multiprocessing.process.BaseProcess,'start',gated_start):
                    worker.start()
                    self.assertTrue(await asyncio.to_thread(entered.wait,3))
                    first=metadata(await server.call_tool('interface_close',{}))
                    self.assertEqual(first.get('status'),'busy',first)
                    self.assertEqual(first['session']['state'],'opening')
                    self.assertIsNone(first['session']['owner_process']['alive'])
                    self.assertIsNone(first['session']['owner_process']['retired'])
                    self.assertIsNone(first['session']['owner_process']['liveness_observed_monotonic_ns'])
                    self.assertEqual(prior.read_bytes(),b'{"previous":"preserve"}')
                    attempt=json.loads((Path(first['call_directory'])/'report.json').read_text())
                    self.assertEqual(attempt['status'],'busy')
                    self.assertEqual(attempt['reason'],'owned_lifecycle_in_progress')
                    evidence=os.environ.get('AGENT_INTERFACE_LIFECYCLE_EVIDENCE')
                    if evidence:
                        target=Path(evidence)/'manual-busy';target.mkdir(parents=True,exist_ok=False)
                        shutil.copy2(Path(first['call_directory'])/'report.json',target/'report.json')
                        shutil.copy2(prior,target/'prior.json')
                    resume.set();await asyncio.to_thread(worker.join,5)
                self.assertFalse(worker.is_alive());self.assertFalse(errors,errors)
                second=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(second.get('status'),'closed',second)
                self.assertFalse(owner._process.is_alive(),second)
            finally:
                resume.set()
                await asyncio.to_thread(worker.join,5)
                for process in spawned:
                    if process.is_alive():process.kill()
                    await asyncio.to_thread(process.join,3)
                    self.assertFalse(process.is_alive(),'fixture child cleanup failed')
                await asyncio.to_thread(worker.join,3)
                self.assertFalse(worker.is_alive(),'fixture startup thread did not finish')


if __name__ == '__main__':
    unittest.main()
