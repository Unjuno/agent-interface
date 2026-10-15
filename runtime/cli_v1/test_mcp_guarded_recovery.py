import asyncio
import tempfile
import threading
import unittest
from unittest.mock import patch

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata
from runtime.guarded_x11_v1.bridge import NativeHandleBridge


class GuardedRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_recovery_does_not_open_a_session(self):
        with tempfile.TemporaryDirectory() as td,patch('runtime.cli_v1.mcp_guarded.open_bridge') as opened:
            server=create_server({'app':20},td,session_mode='guarded-x11')
            tools={tool.name for tool in await server.list_tools()}
            self.assertIn('interface_guarded_recover_input',tools)
            row=metadata(await server.call_tool('interface_guarded_recover_input',{'current_binding_revision':0}))
            self.assertEqual(row['status'],'refused',row)
            self.assertFalse(row['release_attempted'])
            opened.assert_not_called()

    async def test_pending_cleanup_failed_and_explicit_recovery_never_replay_input(self):
        fake=FakeX(self);fake.flip=True
        fake.backend.d.create_resource_object=lambda kind,xid:fake.backend.targets['app']
        entered,resume=threading.Event(),threading.Event()
        mode=['blocked']
        def keymap():
            if mode[0]=='blocked':
                entered.set()
                if not resume.wait(5): raise TimeoutError('harness did not resume readback')
            if mode[0]!='healthy': raise OSError('fake readback unavailable')
            return fake.keymap()
        fake.backend.d.query_keymap=keymap
        with tempfile.TemporaryDirectory() as td:
            server=create_server({'app':20},td,session_mode='guarded-x11',guarded_process_identity=True)
            try:
                source=metadata(await server.call_tool('interface_guarded_observe',{}))
                minted=metadata(await server.call_tool('interface_guarded_mint',dict(alias='field',
                    source_sequence=source['source']['sequence'],point=[8,8],region_size=[12,12])))
                arguments=dict(alias='field',offset=minted['offset'],interaction='keyboard',observe_after=False,
                               tail=[dict(op='key_chord',keys=['CTRL','a'])])
                unneeded=metadata(await server.call_tool('interface_guarded_recover_input',{'current_binding_revision':0}))
                self.assertEqual(unneeded['status'],'refused');self.assertFalse(unneeded['release_attempted'])
                pending=asyncio.create_task(server.call_tool('interface_guarded_input',arguments))
                self.assertTrue(await asyncio.to_thread(entered.wait,2))
                listing=metadata(await server.call_tool('interface_results',{}))
                call_id=next(r['call_id'] for r in listing['calls'] if r['operation']=='guarded_input')
                lookup=metadata(await server.call_tool('interface_results',{'call_id':call_id}))
                self.assertEqual(lookup['status'],'pending')
                before=list(fake.emissions)
                busy=metadata(await server.call_tool('interface_guarded_recover_input',{'current_binding_revision':0}))
                self.assertEqual(busy['status'],'busy');self.assertEqual(fake.emissions,before)
                resume.set()
                failed=metadata(await asyncio.wait_for(pending,2))
                self.assertEqual(failed['status'],'execution_failed')
                self.assertTrue(failed['session']['recovery_required'])
                self.assertEqual(fake.backend.held_keycodes,{'CTRL':1})
                self.assertEqual([item for item in fake.emissions if item[0]==2],[(2,1)])
                revision=failed['session']['binding_revision']
                before=list(fake.emissions)
                wrong=metadata(await server.call_tool('interface_guarded_recover_input',{'current_binding_revision':revision+100}))
                self.assertEqual(wrong['status'],'refused');self.assertEqual(fake.emissions,before)
                mode[0]='failed'
                recovery=metadata(await server.call_tool('interface_guarded_recover_input',{'current_binding_revision':revision}))
                self.assertEqual(recovery['status'],'recovery_failed',recovery)
                self.assertTrue(recovery['release_attempted']);self.assertTrue(recovery['recovery_required'])
                self.assertTrue(recovery['review_required'])
                self.assertEqual(recovery['binding_revision'],revision+1)
                before=list(fake.emissions)
                stale=metadata(await server.call_tool('interface_guarded_recover_input',{'current_binding_revision':revision}))
                self.assertEqual(stale['status'],'refused');self.assertEqual(fake.emissions,before)
                self.assertEqual(fake.backend.held_keycodes,{'CTRL':1})
                mode[0]='healthy'
                recovered=metadata(await server.call_tool('interface_guarded_recover_input',
                    {'current_binding_revision':recovery['binding_revision']}))
                self.assertEqual(recovered['status'],'input_recovered',recovered)
                self.assertFalse(recovered['recovery_required']);self.assertTrue(recovered['review_required'])
                self.assertTrue(recovered['release']['verified']);self.assertEqual(fake.backend.held_keycodes,{})
                self.assertIsNone(recovered['task_success']);self.assertFalse(recovered['replay_allowed'])
                self.assertEqual([item for item in fake.emissions if item[0]==2],[(2,1)])
                refused=metadata(await server.call_tool('interface_guarded_input',arguments))
                self.assertEqual(refused['status'],'refused')
                observed=metadata(await server.call_tool('interface_guarded_observe',{}))
                no_mint=metadata(await server.call_tool('interface_guarded_mint',dict(alias='fresh',
                    source_sequence=observed['source']['sequence'],point=[8,8],region_size=[12,12])))
                self.assertEqual(no_mint['status'],'refused')
                reviewed=metadata(await server.call_tool('interface_guarded_review_window',{'window_id':20}))
                self.assertEqual(reviewed['status'],'reviewed',reviewed)
                fresh=metadata(await server.call_tool('interface_guarded_mint',dict(alias='fresh',
                    source_sequence=reviewed['source']['sequence'],point=[8,8],region_size=[12,12])))
                fake.flip=False
                chosen=metadata(await server.call_tool('interface_guarded_input',dict(arguments,alias='fresh',offset=fresh['offset'])))
                self.assertEqual(chosen['status'],'completed',chosen)
            finally:
                resume.set();mode[0]='healthy'
                await server.call_tool('interface_close',{})


class PythonRecoveryTests(unittest.TestCase):
    def test_pending_recovery_owns_bridge_and_retired_reader_stays_retired(self):
        fake=FakeX(self)
        fake.backend.d.get_display_name=lambda:':fake-only'
        entered,resume=threading.Event(),threading.Event()
        results=[]
        def keymap():
            entered.set()
            if not resume.wait(5): raise TimeoutError('harness did not resume release readback')
            return fake.keymap()
        fake.backend.d.query_keymap=keymap
        with tempfile.TemporaryDirectory() as td:
            bridge=NativeHandleBridge(':fake-only',{'app':20},'app',td+'/bridge',process_identity=True,query_worker=True)
            bridge._target_queries.close()
            bridge.session.recovery_required=True
            fake.backend.held_keycodes={'CTRL':1};fake.down.add(1)
            revision=bridge.binding_revision
            worker=threading.Thread(target=lambda:results.append(bridge.recover_input(revision)))
            worker.start()
            try:
                self.assertTrue(entered.wait(2))
                before=list(fake.emissions)
                busy=bridge.recover_input(revision+1)
                self.assertEqual(busy['status'],'refused');self.assertFalse(busy['release_attempted'])
                self.assertEqual(busy['error'],'INPUT_OWNER_BUSY')
                with self.assertRaises(RuntimeError): bridge.review_window(20)
                self.assertEqual(fake.emissions,before)
                resume.set();worker.join(2)
                self.assertFalse(worker.is_alive());self.assertIsNone(bridge.active)
                self.assertEqual(results[0]['status'],'input_recovered')
                self.assertTrue(bridge._target_queries.snapshot()['retired'])
                self.assertEqual(bridge.review_window(20)['error'],'TARGET_QUERY_WORKER_RETIRED_CLOSE_SESSION')
            finally:
                resume.set();worker.join(5);bridge.close()
