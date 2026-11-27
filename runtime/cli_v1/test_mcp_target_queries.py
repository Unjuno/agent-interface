"""Actual MCP/bridge/session cleanup while a separate Fake X query is stuck."""
import asyncio
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from Xlib import X
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata


class PendingQueries(unittest.IsolatedAsyncioTestCase):
    async def test_healthy_and_changed_generation_use_real_admission(self):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda: ':fake-qualified'
        closed = threading.Event()
        class Reader:
            def read(self, operation, xid):
                return True if operation == 'focus' else fake.generation
            def close(self): closed.set()
        with tempfile.TemporaryDirectory() as td, patch(
                'runtime.guarded_x11_v1.target_queries.X11TargetQueries',return_value=Reader()):
            server = create_server({'app':20},td,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True)
            try:
                source = metadata(await server.call_tool('interface_guarded_observe',{}))
                minted = metadata(await server.call_tool('interface_guarded_mint',dict(alias='field',
                    source_sequence=source['source']['sequence'],point=[8,8],region_size=[12,12])))
                arguments = dict(alias='field',offset=minted['offset'],interaction='keyboard',observe_after=False,
                                 tail=[{'op':'key_chord','keys':['CTRL','a']}])
                first = metadata(await server.call_tool('interface_guarded_input',arguments))
                self.assertEqual(first['status'],'completed',first)
                self.assertEqual([code for kind,code in fake.emissions if kind==X.KeyPress],[1,2])
                self.assertTrue(first['session']['query_worker'])
                before = list(fake.emissions)
                fake.generation = 'b'*64
                second = metadata(await server.call_tool('interface_guarded_input',arguments))
                self.assertEqual(second['status'],'refused',second)
                self.assertEqual(fake.emissions,before)
            finally:
                await server.call_tool('interface_close',{})
            self.assertTrue(await asyncio.to_thread(closed.wait,2))

    async def exercise(self, operation, trigger):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda: ':fake-qualified'
        entered, resume, closed = threading.Event(), threading.Event(), threading.Event()
        read_threads, close_threads = [], []
        now = [1_000_000]
        class Reader:
            def read(self, requested, xid):
                read_threads.append(threading.get_ident())
                if requested == operation and 1 in fake.down:
                    entered.set()
                    if not resume.wait(5): raise TimeoutError('test did not resume read')
                return True if requested == 'focus' else fake.generation
            def close(self):
                close_threads.append(threading.get_ident());closed.set()
        with tempfile.TemporaryDirectory() as td, \
                patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries', return_value=Reader()), \
                patch('time.monotonic_ns', side_effect=lambda:now[0]):
            server = create_server({'app':20},td,session_mode='guarded-x11',
                guarded_process_identity=True,guarded_query_worker=True)
            try:
                source = metadata(await server.call_tool('interface_guarded_observe',{}))
                minted = metadata(await server.call_tool('interface_guarded_mint',dict(alias='field',
                    source_sequence=source['source']['sequence'],point=[8,8],region_size=[12,12])))
                task = asyncio.create_task(server.call_tool('interface_guarded_input',dict(alias='field',
                    offset=minted['offset'],interaction='keyboard',observe_after=False,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertTrue(await asyncio.to_thread(entered.wait,2))
                self.assertEqual(fake.down,{1})
                listing = metadata(await server.call_tool('interface_results',{}))
                call_id = next(row['call_id'] for row in listing['calls'] if row['operation']=='guarded_input')
                wrong = metadata(await server.call_tool('interface_guarded_cancel',{'call_id':'0'*32}))
                self.assertEqual(wrong['status'],'not_active')
                if trigger == 'expiry':
                    now[0] = fake.backend.owner.deadline
                else:
                    first = metadata(await server.call_tool('interface_guarded_cancel',{'call_id':call_id}))
                    self.assertEqual(first['status'],'cancel_requested')
                    self.assertFalse(first['release_confirmed'])
                    # Duplicate request is harmless whether input is active or has completed.
                    second = metadata(await server.call_tool('interface_guarded_cancel',{'call_id':call_id}))
                    self.assertIn(second['status'],('cancel_requested','not_active'))
                response = await asyncio.wait_for(task,2)
                result = metadata(response)
                self.assertEqual(result['status'],'execution_failed',result)
                self.assertEqual(fake.emissions,[(X.KeyPress,1),(X.KeyRelease,1)])
                self.assertEqual(fake.down,set())
                self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertTrue(result['session']['review_required'])
                self.assertFalse(resume.is_set())
                before = list(fake.emissions)
                await server.call_tool('interface_results',{'call_id':call_id})
                self.assertEqual(fake.emissions,before)
                after = metadata(await server.call_tool('interface_guarded_cancel',{'call_id':call_id}))
                self.assertEqual(after['status'],'not_active')
                resume.set()
                self.assertTrue(await asyncio.to_thread(closed.wait,2))
                self.assertEqual(set(read_threads),set(close_threads))
                self.assertNotIn(threading.get_ident(), read_threads)
                refused = metadata(await server.call_tool('interface_guarded_input',dict(alias='field',
                    offset=minted['offset'],interaction='keyboard',observe_after=False,
                    tail=[{'op':'key_chord','keys':['CTRL','a']}])) )
                self.assertEqual(refused['status'],'refused')
                self.assertEqual(fake.emissions,before)
            finally:
                resume.set()
                await server.call_tool('interface_close',{})

    async def test_cancel_blocked_focus(self): await self.exercise('focus','cancel')
    async def test_expiry_blocked_focus(self): await self.exercise('focus','expiry')
    async def test_cancel_blocked_identity(self): await self.exercise('process_identity','cancel')
    async def test_expiry_blocked_identity(self): await self.exercise('process_identity','expiry')


class Startup(unittest.TestCase):
    def test_requires_explicit_guarded_identity_policy(self):
        with tempfile.TemporaryDirectory() as td:
            for mode, identity in [('one-shot',True),('persistent-x11',True),('guarded-x11',False)]:
                with self.assertRaises(ValueError):
                    create_server({'app':20},td,session_mode=mode,
                        guarded_process_identity=identity,guarded_query_worker=True)


if __name__ == '__main__': unittest.main()
