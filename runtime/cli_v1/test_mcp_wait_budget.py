import asyncio
from concurrent.futures import Future,ThreadPoolExecutor
import tempfile
import threading
import unittest
from unittest.mock import patch

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import FakeX,metadata


class WaitBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def ground(self,server):
        source=metadata(await server.call_tool('interface_guarded_observe',{}))
        minted=metadata(await server.call_tool('interface_guarded_mint',dict(alias='field',
            source_sequence=source['source']['sequence'],point=[8,8],region_size=[12,12])))
        return dict(alias='field',offset=minted['offset'],interaction='keyboard',observe_after=False,
                    tail=[dict(op='key_chord',keys=['CTRL','a'])])

    async def terminal(self,server,call_id):
        async def poll():
            while True:
                row=metadata(await server.call_tool('interface_results',dict(call_id=call_id,include_image=False)))
                if row['status']!='pending': return row
                await asyncio.sleep(.005)
        return await asyncio.wait_for(poll(),2)

    async def exercise_input_fault(self,boundary):
        fake=FakeX(self);fake.flip=True
        entered,resume=threading.Event(),threading.Event()
        def gate():
            entered.set()
            if not resume.wait(5): raise TimeoutError('test did not resume input transport')
        emit=fake.emit
        def guarded_emit(display,kind,code):
            if boundary=='send' and kind==3: gate()
            emit(display,kind,code)
        def sync():
            if boundary=='sync' and fake.emissions and fake.emissions[-1][0]==3: gate()
        def keymap():
            if boundary=='readback': gate()
            return fake.keymap()
        fake.backend.d.sync=sync;fake.backend.d.query_keymap=keymap
        with tempfile.TemporaryDirectory() as td,patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=guarded_emit):
            server=create_server({'app':20},td,session_mode='guarded-x11',guarded_process_identity=True)
            arguments=await self.ground(server)
            try:
                pending=metadata(await asyncio.wait_for(server.call_tool('interface_guarded_input',
                    dict(arguments,wait_for_result_ms=20)),2))
                self.assertTrue(await asyncio.to_thread(entered.wait,1))
                self.assertEqual(pending['status'],'pending',pending)
                self.assertFalse(pending['release_confirmed']);self.assertFalse(pending['replay_allowed'])
                self.assertIsNone(pending['task_success'])
                self.assertEqual(fake.down,{1} if boundary=='send' else set())
                before=list(fake.emissions)
                lookup=metadata(await server.call_tool('interface_results',dict(call_id=pending['call_id'])))
                self.assertEqual(lookup['status'],'pending')
                for tool,args in [('interface_guarded_input',arguments),('interface_close',{}),
                        ('interface_guarded_recover_input',dict(current_binding_revision=0))]:
                    self.assertEqual(metadata(await server.call_tool(tool,args))['status'],'busy')
                self.assertEqual(fake.emissions,before)
                deadline=fake.backend.owner.deadline
                resume.set()
                result=await self.terminal(server,pending['call_id'])
                self.assertEqual(result['status'],'execution_failed',result)
                self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertEqual(fake.down,set());self.assertEqual([r for r in fake.emissions if r[0]==2],[(2,1)])
                self.assertGreater(deadline,0)
            finally:
                resume.set()
                await server.call_tool('interface_close',{})

    async def test_blocked_release_send_returns_pending_without_release_claim(self): await self.exercise_input_fault('send')
    async def test_blocked_release_sync_returns_pending_even_if_fake_neutral(self): await self.exercise_input_fault('sync')
    async def test_blocked_readback_returns_pending_without_cancelling_worker(self): await self.exercise_input_fault('readback')

    async def test_queued_call_has_stable_id_and_executes_once(self):
        fake=FakeX(self)
        release,entered=threading.Event(),threading.Event()
        loop=asyncio.get_running_loop()
        previous=loop._default_executor
        pool=ThreadPoolExecutor(max_workers=1)
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            arguments=await self.ground(server)
            def blocker(): entered.set();release.wait(5)
            blocker_future=pool.submit(blocker)
            loop.set_default_executor(pool)
            try:
                pending=metadata(await server.call_tool('interface_guarded_input',dict(arguments,wait_for_result_ms=0)))
                self.assertEqual(pending['status'],'pending',pending)
                lookup=metadata(await server.call_tool('interface_results',dict(call_id=pending['call_id'])))
                self.assertEqual(lookup['call']['state'],'queued')
                self.assertEqual(fake.emissions,[])
                self.assertEqual(metadata(await server.call_tool('interface_close',{}))['status'],'busy')
                release.set()
                result=await self.terminal(server,pending['call_id'])
                self.assertEqual(result['status'],'completed',result)
                self.assertEqual(fake.emissions,[(2,1),(2,2),(3,2),(3,1)])
            finally:
                release.set();blocker_future.result(timeout=2)
                loop.set_default_executor(previous or ThreadPoolExecutor(max_workers=1))
                pool.shutdown(wait=True)
                await server.call_tool('interface_close',{})

    async def test_executor_rejection_finishes_preallocated_record(self):
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            with patch.object(asyncio.get_running_loop(),'run_in_executor',side_effect=RuntimeError('executor rejected')):
                row=metadata(await server.call_tool('interface_guarded_input',dict(alias='field',offset=[1,1],
                    tail=[dict(op='key_chord',keys=['a'])],wait_for_result_ms=0)))
            self.assertEqual(row['status'],'worker_submission_failed',row)
            listing=metadata(await server.call_tool('interface_results',{}))
            self.assertEqual(listing['calls'][0]['call_id'],row['call_id'])
            self.assertEqual(listing['calls'][0]['state'],'finished')
            self.assertFalse(row['operation_invoked']);self.assertFalse(row['replay_allowed'])

    async def test_quick_input_returns_original_terminal_shape(self):
        fake=FakeX(self)
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            arguments=await self.ground(server)
            result=metadata(await server.call_tool('interface_guarded_input',dict(arguments,wait_for_result_ms=1000)))
            self.assertEqual(result['status'],'completed',result)
            await server.call_tool('interface_close',{})

    async def test_recovery_wait_ends_but_same_attempt_keeps_revision_and_custody(self):
        fake=FakeX(self)
        entered,resume=threading.Event(),threading.Event()
        def keymap():
            entered.set()
            if not resume.wait(5): raise TimeoutError('test did not resume recovery')
            return fake.keymap()
        fake.backend.d.query_keymap=keymap
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            await server.call_tool('interface_guarded_observe',{})
            bridge=fake.backend.owner;bridge.session.recovery_required=True
            fake.backend.held_keycodes={'CTRL':1};fake.down.add(1)
            revision=bridge.binding_revision
            try:
                pending=metadata(await server.call_tool('interface_guarded_recover_input',dict(
                    current_binding_revision=revision,wait_for_result_ms=20)))
                self.assertTrue(await asyncio.to_thread(entered.wait,1))
                self.assertEqual(pending['status'],'pending',pending)
                self.assertFalse(pending['release_confirmed']);self.assertFalse(pending['replay_allowed'])
                self.assertEqual(bridge.binding_revision,revision+1)
                before=list(fake.emissions)
                self.assertEqual(metadata(await server.call_tool('interface_guarded_recover_input',dict(
                    current_binding_revision=revision)))['status'],'busy')
                self.assertEqual(fake.emissions,before)
                resume.set()
                recovered=await self.terminal(server,pending['call_id'])
                self.assertEqual(recovered['status'],'input_recovered',recovered)
                self.assertTrue(recovered['release']['verified']);self.assertTrue(recovered['review_required'])
                self.assertEqual([r for r in fake.emissions if r[0]==2],[])
            finally:
                resume.set();await server.call_tool('interface_close',{})

    async def test_invalid_wait_budget_does_not_open_or_register_input(self):
        with tempfile.TemporaryDirectory() as td,patch('runtime.cli_v1.mcp_guarded.open_bridge') as opened:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            for value in (-1,10001,True,1.5,'20'):
                result=await server.call_tool('interface_guarded_input',dict(alias='field',offset=[1,1],
                    tail=[dict(op='key_chord',keys=['a'])],wait_for_result_ms=value))
                self.assertTrue(result.isError)
            self.assertEqual(metadata(await server.call_tool('interface_results',{}))['calls'],[])
            opened.assert_not_called()

    async def test_failed_handle_before_entry_has_terminal_discoverable_record(self):
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            failed=asyncio.get_running_loop().create_future()
            failed.set_exception(RuntimeError('terminal executor handle'))
            with patch.object(asyncio.get_running_loop(),'run_in_executor',return_value=failed):
                row=metadata(await server.call_tool('interface_guarded_input',dict(alias='field',offset=[1,1],
                    tail=[dict(op='key_chord',keys=['a'])],wait_for_result_ms=0)))
            self.assertEqual(row['status'],'worker_handle_failed',row)
            self.assertEqual(row['call']['state'],'finished')
            self.assertFalse(row['call']['backend_attempted'])
            self.assertFalse(row['release_confirmed']);self.assertFalse(row['replay_allowed'])

    async def test_failed_executor_handle_after_entry_keeps_live_writer_custody(self):
        fake=FakeX(self);fake.flip=True
        entered,resume=threading.Event(),threading.Event()
        def keymap():
            entered.set()
            if not resume.wait(5): raise TimeoutError('test did not resume writer')
            return fake.keymap()
        fake.backend.d.query_keymap=keymap
        class FailedHandlePool(ThreadPoolExecutor):
            def submit(pool,function,*args,**kwargs):
                pool.actual=super().submit(function,*args,**kwargs)
                if not entered.wait(2): raise RuntimeError('worker did not enter')
                failed=Future();failed.set_exception(RuntimeError('failed handle after entry'));return failed
        loop=asyncio.get_running_loop();pool=FailedHandlePool(max_workers=1)
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11',guarded_process_identity=True)
            arguments=await self.ground(server)
            previous=loop._default_executor
            loop.set_default_executor(pool)
            try:
                failed=metadata(await server.call_tool('interface_guarded_input',dict(arguments,wait_for_result_ms=0)))
                self.assertEqual(failed['status'],'worker_handle_failed',failed)
                self.assertEqual(failed['call']['state'],'running')
                self.assertFalse(failed['release_confirmed']);self.assertFalse(failed['replay_allowed'])
                self.assertEqual(metadata(await server.call_tool('interface_close',{}))['status'],'busy')
                loop.set_default_executor(previous or ThreadPoolExecutor(max_workers=1))
                resume.set()
                result=await self.terminal(server,failed['call_id'])
                self.assertEqual(result['status'],'execution_failed')
                self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertEqual([r for r in fake.emissions if r[0]==2],[(2,1)])
            finally:
                resume.set();loop.set_default_executor(previous or ThreadPoolExecutor(max_workers=1))
                pool.shutdown(wait=True)
                await server.call_tool('interface_close',{})
