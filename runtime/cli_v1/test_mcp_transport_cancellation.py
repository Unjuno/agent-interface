"""Public cancellation cannot unsend blocked transport; Fake X only."""
import asyncio
import copy
from contextlib import nullcontext
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from Xlib import X
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import FakeX,metadata
from runtime.cli_v1.test_mcp_interruption_receipt import grounded
from runtime.guarded_x11_v1.test_observation_worker import reader_backend

ROWS=[]


class MCPTransportCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def cell(self,boundary):
        fake=FakeX(self);fake.flip=boundary.startswith('release')
        fake.backend.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
        fake.backend.d.get_display_name=lambda:':fake-qualified'
        entered,resume,left=threading.Event(),threading.Event(),threading.Event()
        gated=[False];stage=[None];timeline=[];worker_threads=[];server_queue=[]
        clock=[1_000_000]
        clock_patch=(patch('time.monotonic_ns',side_effect=lambda:clock[0])
                     if boundary=='press_queued_expiry' else nullcontext())
        def mark(event,**values):timeline.append(dict(event=event,host_monotonic_ns=time.monotonic_ns(),**values))
        def gate():
            if gated[0]:return
            gated[0]=True;worker_threads.append(threading.get_ident());mark('transport_entered');entered.set()
            if not resume.wait(5):raise TimeoutError('owned transport gate not resumed')
            mark('transport_resumed');left.set()
        def emit(connection,kind,code):
            if boundary=='press_send' and kind==X.KeyPress and code==1:gate()
            if boundary=='release_send' and kind==X.KeyRelease and code==1:gate()
            if boundary in ('press_queued_sync','press_queued_expiry'):
                server_queue.append((connection,kind,code))
                mark('server_queued',writer_is_session=connection is fake.backend.d,kind=kind,code=code)
                if kind==X.KeyPress and code==1:stage[0]='press'
                if kind==X.KeyRelease and code==1:stage[0]='release'
                return
            fake.emit(connection,kind,code);mark('fake_emission',kind=kind,code=code)
            if kind==X.KeyPress and code==1:stage[0]='press'
            if kind==X.KeyRelease and code==1:stage[0]='release'
        def sync():
            if boundary in ('press_queued_sync','press_queued_expiry'):
                if stage[0]=='press' and not gated[0]:gate()
                queued,server_queue[:]=list(server_queue),[]
                for connection,kind,code in queued:
                    fake.emit(connection,kind,code)
                    mark('server_applied',writer_is_session=connection is fake.backend.d,kind=kind,code=code)
                return
            if boundary=='press_sync' and stage[0]=='press':gate()
            if boundary=='release_sync' and stage[0]=='release':gate()
        fake.backend.d.sync=sync
        reader=reader_backend(fake,lambda *a:SimpleNamespace(data=fake.raw,depth=24,visual=1))
        reader.d.create_resource_object=lambda kind,xid:SimpleNamespace(id=xid)
        with tempfile.TemporaryDirectory(prefix='mcp-transport-stop-') as td, clock_patch, \
                patch('runtime.backends.x11_v1.backend.xtest.fake_input',side_effect=emit), \
                patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend',return_value=reader), \
                patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity',side_effect=lambda *a:fake.generation), \
                patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries') as query:
            query.return_value.read.side_effect=lambda op,xid:True if op=='focus' else fake.generation
            server=create_server({'app':20},td,session_mode='guarded-x11',guarded_process_identity=True,
                guarded_query_worker=True,guarded_observation_worker=True)
            arguments=await grounded(server);bridge=fake.backend.owner
            async def lookup(call_id):
                return metadata(await server.call_tool('interface_results',dict(call_id=call_id,include_image=False)))
            async def terminal(call_id):
                while True:
                    result=await lookup(call_id)
                    if result['status']!='pending':return result
                    await asyncio.sleep(.005)
            try:
                if boundary=='stable':
                    pending=None;before=None
                    result=metadata(await server.call_tool('interface_guarded_input',arguments))
                    self.assertEqual(result['status'],'completed',result)
                    self.assertEqual(fake.emissions,[(2,1),(2,2),(3,2),(3,1)])
                    old_cancel=None;replay=None
                else:
                    pending=metadata(await server.call_tool('interface_guarded_input',dict(arguments,wait_for_result_ms=0)))
                    self.assertEqual(pending['status'],'pending',pending)
                    self.assertTrue(await asyncio.to_thread(entered.wait,2))
                    original_deadline=bridge.deadline
                    if boundary=='press_queued_expiry':
                        clock[0]=original_deadline+1
                        mark('lease_expired_while_transport_blocked',deadline=original_deadline,
                             clock_ns=clock[0])
                        cancel=duplicate=None
                    else:
                        mark('cancel_requested')
                        cancel=metadata(await server.call_tool('interface_guarded_cancel',{'call_id':pending['call_id']}))
                        duplicate=metadata(await server.call_tool('interface_guarded_cancel',{'call_id':pending['call_id']}))
                        mark('cancel_acknowledged')
                        self.assertEqual(cancel['status'],'cancel_requested',cancel)
                        self.assertFalse(cancel['release_confirmed']);self.assertTrue(duplicate['already_requested'])
                    outstanding=await lookup(pending['call_id'])
                    busy_input=metadata(await server.call_tool('interface_guarded_input',arguments))
                    busy_close=metadata(await server.call_tool('interface_close',{}))
                    busy_recovery=metadata(await server.call_tool('interface_guarded_recover_input',
                        {'current_binding_revision':bridge.binding_revision}))
                    self.assertTrue(all(row['status']=='busy' for row in (busy_input,busy_close,busy_recovery)))
                    self.assertEqual(outstanding['status'],'pending')
                    self.assertIsNot(outstanding.get('release_confirmed'),True)
                    self.assertFalse(resume.is_set());self.assertFalse(left.is_set())
                    self.assertEqual(bridge.deadline,original_deadline)
                    before=dict(cancel=cancel,duplicate_cancel=duplicate,lookup=outstanding,
                        busy_input=busy_input,busy_close=busy_close,busy_recovery=busy_recovery,
                        down=sorted(fake.down),ledger=copy.deepcopy(fake.backend.held_keycodes),
                        emissions=copy.deepcopy(fake.emissions),transport_running=not left.is_set(),
                        server_pending=[dict(writer_is_session=connection is fake.backend.d,
                            kind=kind,code=code) for connection,kind,code in server_queue],
                        worker_threads=worker_threads,clock_ns=clock[0],
                        live_worker_handles=[t.ident for t in threading.enumerate()
                            if t.ident in worker_threads and t.is_alive()],original_deadline=original_deadline,
                        reader=bridge._observations.snapshot())
                    self.assertEqual(before['live_worker_handles'],worker_threads)
                    self.assertEqual(before['ledger'],{'CTRL':1})
                    self.assertEqual(before['down'],[] if boundary in ('press_send','release_sync','press_queued_sync','press_queued_expiry') else [1])
                    mark('resume_requested');resume.set()
                    result=await asyncio.wait_for(terminal(pending['call_id']),2)
                    mark('terminal_received')
                    self.assertEqual(result['status'],'execution_failed',result)
                    self.assertEqual(fake.emissions,[(2,1),(3,1)])
                    review_required_after_terminal=bridge.review_required
                    if boundary=='press_queued_expiry':
                        self.assertTrue(review_required_after_terminal)
                    old_cancel=metadata(await server.call_tool('interface_guarded_cancel',{'call_id':pending['call_id']}))
                    self.assertEqual(old_cancel['status'],'not_active')
                    replay=metadata(await server.call_tool('interface_guarded_input',arguments))
                    self.assertEqual(replay['status'],'refused',replay)
                    self.assertEqual(fake.emissions,[(2,1),(3,1)])
                    self.assertTrue(bridge.review_required)
                    self.assertTrue(result['result']['execution']['releases'][-1]['verified'])
                self.assertEqual(fake.down,set());self.assertEqual(fake.backend.held_keycodes,{})
                closed=metadata(await server.call_tool('interface_close',{}))
                self.assertEqual(closed['status'],'closed',closed)
                for client in (bridge._target_queries,bridge._observations):
                    if client.thread is not None:
                        await asyncio.to_thread(client.thread.join,2);self.assertFalse(client.thread.is_alive())
                row=dict(boundary=boundary,pending=pending,before_resume=before,result=result,
                    review_required_after_terminal=locals().get('review_required_after_terminal'),
                    old_cancel=old_cancel,replay=replay,closed=closed,down=sorted(fake.down),
                    ledger=copy.deepcopy(fake.backend.held_keycodes),emissions=copy.deepcopy(fake.emissions),timeline=timeline,
                    files_hex={p.relative_to(td).as_posix():p.read_bytes().hex() for p in Path(td).rglob('*') if p.is_file()})
                ROWS.append(row);return row
            finally:
                resume.set()
                if boundary!='stable' and entered.is_set():
                    try:await asyncio.wait_for(terminal(pending['call_id']),2)
                    finally:await server.call_tool('interface_close',{})
                else:await server.call_tool('interface_close',{})

    async def test_cancel_during_press_send(self):await self.cell('press_send')
    async def test_cancel_during_press_sync(self):await self.cell('press_sync')
    async def test_cancel_during_release_send(self):await self.cell('release_send')
    async def test_cancel_during_release_sync(self):await self.cell('release_sync')
    async def test_cancel_with_press_queued_before_server_processing(self):
        row=await self.cell('press_queued_sync')
        self.assertEqual(row['before_resume']['down'],[])
        self.assertEqual(row['before_resume']['ledger'],{'CTRL':1})
        self.assertEqual(row['result']['status'],'execution_failed')
        self.assertEqual(row['before_resume']['server_pending'],[{'writer_is_session':True,'kind':X.KeyPress,'code':1}])
        self.assertEqual(row['emissions'],[(2,1),(3,1)])
        self.assertEqual(row['down'],[])
        self.assertEqual(row['ledger'],{})
    async def test_lease_expiry_with_press_queued_before_server_processing(self):
        row=await self.cell('press_queued_expiry')
        before=row['before_resume']
        self.assertIsNone(before['cancel'])
        self.assertIsNone(before['duplicate_cancel'])
        self.assertGreater(before['clock_ns'],before['original_deadline'])
        self.assertEqual(before['lookup']['status'],'pending')
        self.assertIsNot(before['lookup'].get('release_confirmed'),True)
        self.assertEqual(before['server_pending'],[{'writer_is_session':True,'kind':X.KeyPress,'code':1}])
        self.assertEqual(before['down'],[])
        self.assertEqual(before['ledger'],{'CTRL':1})
        self.assertEqual(row['result']['status'],'execution_failed')
        self.assertTrue(row['review_required_after_terminal'])
        self.assertEqual(row['emissions'],[(2,1),(3,1)])
        self.assertEqual(row['down'],[])
        self.assertEqual(row['ledger'],{})
    async def test_stable_selected_worker_route(self):await self.cell('stable')


if __name__=='__main__':unittest.main()
