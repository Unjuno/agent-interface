"""Current strict owner through real private sockets; X11 is entirely fake."""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import threading
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent/'doom'), str(HERE.parents[1])]
from lease_release_v1 import Lease
from test_map01_process_identity_backend import backend_fixture, native

ROWS = []

def rpc():
    import input_owner_rpc_v2
    return input_owner_rpc_v2


def bound(backend):
    lease = Lease(time.perf_counter_ns()+10_000_000_000)
    lease.intent_token = 'rpc-v2-intent'
    backend.bind_lease_source(lease, backend.sequence)
    return lease


class Wire:
    def __init__(self, sock, fault=None):
        self.sock, self.fault, self.sent = sock, fault, []
    def __getattr__(self, key):
        return getattr(self.sock, key)
    def recv(self,n):
        data=self.sock.recv(n)
        if self.fault=='coalesce-two':
            while data.count(b'\n')<2:
                chunk=self.sock.recv(n-len(data))
                if not chunk:break
                data+=chunk
        return data
    def sendall(self, data):
        row = json.loads(data)
        self.sent.append(row)
        if self.fault == 'bad-capabilities' and row.get('schema') == 'input-owner-rpc-ready-v2':
            row['capabilities']['process_identity'] = 1
            data = (json.dumps(row)+'\n').encode()
        if self.fault == 'bad-ready' and row.get('schema') == 'input-owner-rpc-ready-v2':
            row['service_id'] = 'wrong-service'
            data = (json.dumps(row)+'\n').encode()
        if self.fault == 'inconsistent-close' and type(row.get('result')) is dict and row['result'].get('schema') == 'input-owner-service-close-v2':
            row['result']['owner_thread_stopped'] = False
            row['result']['verified'] = True
            data = (json.dumps(row)+'\n').encode()
        if row.get('schema') == 'input-owner-rpc-response-v2' and row.get('request_id') == 1:
            if self.fault == 'extra-reply':
                extra=json.loads(json.dumps(row));extra['request_id']=2
                self.sent.append(extra)
                return self.sock.sendall((json.dumps(row)+'\n'+json.dumps(extra)+'\n').encode())
            if self.fault == 'drop': return
            if self.fault == 'wrong-id': row['request_id'] = 999
            if self.fault == 'invalid-records': row['records'] = None
            if self.fault == 'partial': return self.sock.sendall(data[:20])
            data = (json.dumps(row)+'\n').encode()
        return self.sock.sendall(data)


class OwnerRpcTests(unittest.TestCase):
    def test_module_available(self):
        self.assertIsNotNone(importlib.util.find_spec('input_owner_rpc_v2'),
                             'Current-generation sticky-quarantine RPC implementation is absent')

    def test_codec_roundtrip_preserves_immutable_source_and_sticky_cancel(self):
        c = rpc()
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('codec', 0)
            original = bound(backend)
            original.target_window_identity = (backend.sequence, 41, 'b'*64, original.deadline)
            wire = c.encode_lease(original)
            pool = {}
            decoded = c.decode_lease(json.loads(json.dumps(wire)), pool)
            self.assertEqual(decoded.target_process_identity, original.target_process_identity)
            self.assertEqual(decoded.target_window_identity, original.target_window_identity)
            wire['cancel_requested'] = True
            self.assertIs(c.decode_lease(wire, pool), decoded)
            wire['cancel_requested'] = False
            self.assertTrue(c.decode_lease(wire, pool).cancel.is_set())
            changed = json.loads(json.dumps(wire))
            changed['target_process_identity'][2] = 'c'*64
            with self.assertRaises(ValueError): c.decode_lease(changed, pool)
            ROWS.append(dict(case='codec', wire=wire, process=list(decoded.target_process_identity),
                             window=list(decoded.target_window_identity), cancel_sticky=decoded.cancel.is_set(),
                             changed_source_refused=True))

    def session(self, backend, fault=None, *, fake):
        c = rpc()
        fake.keysym_to_keycode = lambda value: {ord('a'):38, ord('d'):40}.get(value,0)
        fake.rpc_edges = []
        fake.rpc_released = threading.Event()
        previous = native.xtest.fake_input.side_effect
        def tracked(connection,event,code):
            result=previous(connection,event,code)
            fake.rpc_edges.append(dict(event=event,code=code,down=sorted(fake.down)))
            if event==native.X.KeyRelease:fake.rpc_released.set()
            return result
        native.xtest.fake_input.side_effect = tracked
        left, right = socket.socketpair()
        client_wire, server_wire = Wire(left), Wire(right, fault)
        results = []
        def serve():
            try: results.append(c.serve_owner(server_wire, backend.owner, display=':fake', service_id='owned-service-v2'))
            except BaseException as exc: results.append(dict(thread_error=repr(exc)))
        thread = threading.Thread(target=serve, name='owned-rpc-v2-test-service')
        thread.start()
        try:
            client = c.OwnerRpcClient(client_wire, display=':fake', service_id='owned-service-v2', timeout=.15)
        except BaseException:
            left.close(); thread.join(5); raise
        return client, client_wire, server_wire, results, thread

    def test_actual_strict_owner_roundtrip_and_eof_releases(self):
        c = rpc()
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('rpc-source', 0)
            lease = bound(backend)
            client, wire, peer, receipts, thread = self.session(backend, fake=fake)
            try:
                admission = client.call('down', lease, 'a')
                self.assertEqual(admission['target_process_identity'], list(lease.target_process_identity))
                self.assertEqual(fake.down, {38})
                wire.shutdown(socket.SHUT_RDWR); wire.close()
                thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertEqual(fake.down, set())
                self.assertTrue(receipts[0]['verified'], receipts)
                ROWS.append(dict(case='peer-eof', requests=wire.sent, receipts=receipts,
                                 admission=admission, edges=fake.rpc_edges, fake_down_after=[]))
            finally:
                client.close(); thread.join(5)

    def test_unknown_reply_permanently_refuses_second_send_then_eof_closes_owner(self):
        c = rpc()
        for fault in ('drop', 'wrong-id', 'invalid-records', 'partial'):
            with self.subTest(fault=fault), backend_fixture() as (backend, events, generation, fake):
                backend.snapshot('uncertain', 0)
                lease = bound(backend)
                client, wire, peer, receipts, thread = self.session(backend, fault, fake=fake)
                try:
                    with self.assertRaises(c.RpcOutcomeUnknown): client.call('down', lease, 'a')
                    before = list(wire.sent)
                    self.assertEqual(fake.down, {38})
                    with self.assertRaises(c.RpcQuarantined): client.call('down', lease, 'd')
                    self.assertEqual(wire.sent, before)
                    local_close = client.close()
                    self.assertFalse(local_close['verified'])
                    thread.join(3)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual(fake.down, set())
                    self.assertTrue(receipts[0]['verified'], receipts)
                    ROWS.append(dict(case=fault, requests=wire.sent, local_close=local_close,
                                     server_receipts=receipts, edges=fake.rpc_edges, fake_down_at_unknown=[38], fake_down_after=[], post_error_send_count=0))
                finally:
                    client.close(); thread.join(5)

    def test_changed_generation_is_refused_by_remote_current_owner(self):
        c = rpc()
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('stale', 0)
            lease = bound(backend)
            generation[0] = 'b'*64
            client, wire, peer, receipts, thread = self.session(backend, fake=fake)
            try:
                with self.assertRaises(c.RpcOutcomeUnknown): client.call('down', lease, 'a')
                with self.assertRaises(c.RpcQuarantined): client.call('down', lease, 'd')
                self.assertEqual(fake.down, set())
                client.close(); thread.join(3)
                self.assertFalse(thread.is_alive())
                ROWS.append(dict(case='stale-generation', requests=wire.sent, receipts=receipts,
                                 fake_down_after=[], post_error_send_count=0))
            finally: client.close(); thread.join(5)

    def test_window_source_rejected_before_send_without_canonical_service_contract(self):
        c = rpc()
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('window', 0)
            lease = bound(backend)
            lease.target_window_identity = (backend.sequence,41,'b'*64,lease.deadline)
            client, wire, peer, receipts, thread = self.session(backend, fake=fake)
            try:
                with self.assertRaises(ValueError): client.call('down', lease, 'a')
                self.assertEqual(wire.sent, [])
                lease.target_window_identity = None
                self.assertEqual(client.call('down', lease, 'a')['event'], 'input_admission')
                close = client.close(); thread.join(3)
                self.assertTrue(close['verified'])
                self.assertEqual(fake.down,set())
                ROWS.append(dict(case='unsupported-window', refused_before_send=True,
                                 requests=wire.sent, close=close, receipts=receipts))
            finally: client.close(); thread.join(5)

    def test_duplicate_id_and_lease_rebinding_close_before_second_input(self):
        c = rpc()
        for fault in ('duplicate-id','lease-rebind','duplicate-json-member'):
            with self.subTest(fault=fault), backend_fixture() as (backend,events,generation,fake):
                backend.snapshot('protocol',0); lease=bound(backend)
                client,wire,peer,receipts,thread=self.session(backend, fake=fake)
                try:
                    client.call('down',lease,'a')
                    request=json.loads(json.dumps(wire.sent[0]));request['key']='d'
                    if fault=='lease-rebind':
                        request['request_id']=2
                        request['lease']['target_process_identity'][2]='b'*64
                    data=json.dumps(request)
                    if fault=='duplicate-json-member':
                        request['request_id']=2
                        data=json.dumps(request)[:-1]+',"request_id":2}'
                    wire.sock.sendall((data+'\n').encode())
                    thread.join(3)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual(fake.down,set())
                    self.assertIsNotNone(receipts[0]['protocol_error'])
                    self.assertTrue(receipts[0]['verified'])
                    self.assertEqual([r['code'] for r in fake.rpc_edges if r['event']==2],[38])
                    ROWS.append(dict(case=fault, sent_second=request, receipts=receipts,
                                     fake_down_after=[], edges=fake.rpc_edges))
                finally:client.close();thread.join(5)

    def test_inconsistent_close_receipt_is_not_a_release_certificate(self):
        c=rpc()
        with backend_fixture() as (backend,events,generation,fake):
            backend.snapshot('close-receipt',0);lease=bound(backend)
            client,wire,peer,receipts,thread=self.session(backend,'inconsistent-close',fake=fake)
            try:
                client.call('down',lease,'a')
                result=client.close();thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertFalse(result['verified'])
                self.assertTrue(receipts[0]['verified'])
                ROWS.append(dict(case='inconsistent-close',local_close=result,server_receipts=receipts,
                                 received=peer.sent,edges=fake.rpc_edges))
            finally:client.close();thread.join(5)

    def test_blocked_release_keeps_transport_close_and_owner_stop_unverified(self):
        c=rpc();gate=threading.Event();entered=threading.Event()
        with backend_fixture() as (backend,events,generation,fake):
            backend.snapshot('blocked-cleanup',0);lease=bound(backend)
            client,wire,peer,receipts,thread=self.session(backend,fake=fake)
            client.call('down',lease,'a')
            previous=native.xtest.fake_input.side_effect
            def send(connection,event,code):
                if event==native.X.KeyRelease and not gate.is_set():
                    entered.set()
                    if not gate.wait(9):raise TimeoutError('test release gate not resumed')
                return previous(connection,event,code)
            try:
                with patch.object(native.xtest,'fake_input',side_effect=send):
                    local=client.close()
                    self.assertTrue(entered.wait(1))
                    self.assertFalse(local['verified'])
                    thread.join(5)
                    self.assertFalse(thread.is_alive())
                    self.assertFalse(receipts[0]['verified'])
                    self.assertFalse(receipts[0]['owner_thread_stopped'])
                    self.assertEqual(fake.down,{38})
                    before=sorted(fake.down)
                    gate.set()
                    self.assertTrue(backend.owner._inner.stopped.wait(3))
                    self.assertEqual(fake.down,set())
                ROWS.append(dict(case='blocked-release',local_close=local,server_receipts=receipts,
                                 fake_down_before_resume=before,fake_down_after=[],edges=fake.rpc_edges))
            finally:
                gate.set();client.close();thread.join(5);backend.owner._inner.thread.join(3)

    def test_readiness_is_bound_to_exact_service_before_any_input(self):
        c=rpc()
        for fault in ('bad-ready','bad-capabilities'):
            with self.subTest(fault=fault), backend_fixture() as (backend,events,generation,fake):
                backend.snapshot('ready',0)
                refused=False;session=None
                try:session=self.session(backend,fault,fake=fake)
                except ValueError:refused=True
                finally:
                    if session is not None:session[0].close();session[-1].join(3)
                self.assertTrue(refused,'Non-boolean readiness capability must not be accepted')
                self.assertEqual(fake.down,set())
                self.assertTrue(backend.owner._inner.stopped.is_set())
        ROWS.append(dict(case='bad-ready',no_client_created=True,fake_down_after=[],edges=[],
                         refused_faults=['bad-ready','bad-capabilities']))

    def test_expired_or_malformed_local_source_does_not_consume_request_identity(self):
        c=rpc()
        with backend_fixture() as (backend,events,generation,fake):
            backend.snapshot('local-refusal',0);lease=bound(backend)
            client,wire,peer,receipts,thread=self.session(backend,fake=fake)
            try:
                good=lease.target_process_identity
                lease.target_process_identity=None
                with self.assertRaises(ValueError):client.call('down',lease,'a')
                lease.target_process_identity=good
                expired=Lease(time.perf_counter_ns()-1);expired.intent_token='expired'
                expired.expected_focus=expired.expected_surface=41
                expired.expected_geometry=[0,0,32,32]
                expired.target_process_identity=(backend.sequence,41,'a'*64,expired.deadline)
                with self.assertRaises(ValueError):client.call('down',expired,'a')
                self.assertEqual(wire.sent,[])
                client.call('down',lease,'a')
                self.assertEqual(wire.sent[0]['request_id'],1)
                close=client.close();thread.join(3)
                self.assertTrue(close['verified'])
                ROWS.append(dict(case='pre-send-refusal',requests=wire.sent,close=close,
                                 edges=fake.rpc_edges,invalid_attempts_sent=0))
            finally:client.close();thread.join(5)

    def test_successful_raw_close_call_retires_the_same_client(self):
        c=rpc()
        with backend_fixture() as (backend,events,generation,fake):
            backend.snapshot('raw-close',0);lease=bound(backend)
            client,wire,peer,receipts,thread=self.session(backend,fake=fake)
            try:
                client.call('down',lease,'a')
                close=client.call('close');before=list(wire.sent)
                with self.assertRaises(c.RpcQuarantined):client.call('down',lease,'d')
                self.assertEqual(wire.sent,before)
                self.assertTrue(client.close()['verified'])
                thread.join(3);self.assertFalse(thread.is_alive())
                ROWS.append(dict(case='raw-close',requests=wire.sent,close=close,edges=fake.rpc_edges))
            finally:client.close();thread.join(5)

    def test_service_owner_reacts_while_rpc_idle_and_explicit_cancel_is_transferred(self):
        c=rpc()
        for change in ('generation','explicit-cancel','lease-expiry'):
            with self.subTest(change=change), backend_fixture() as (backend,events,generation,fake):
                backend.snapshot('active-watch',0);lease=bound(backend)
                if change=='lease-expiry':
                    lease.deadline=time.perf_counter_ns()+300_000_000
                    lease.target_process_identity=(*lease.target_process_identity[:3],lease.deadline)
                client,wire,peer,receipts,thread=self.session(backend,fake=fake)
                try:
                    admission=client.call('down',lease,'a')
                    self.assertEqual(fake.down,{38})
                    sent_before_change=len(wire.sent)
                    if change=='generation':generation[0]='b'*64
                    if change=='explicit-cancel':
                        lease.cancel.set()
                        client.call('input_state',lease)
                    self.assertTrue(fake.rpc_released.wait(2))
                    self.assertEqual(fake.down,set())
                    self.assertEqual(len(wire.sent),sent_before_change+(change=='explicit-cancel'))
                    client.call('input_state')
                    release=[r for r in client.records if r.get('event')=='owner_release'][-1]
                    self.assertTrue(release['verified'])
                    self.assertEqual(release['keys_down'],[])
                    client.close();thread.join(3);self.assertFalse(thread.is_alive())
                    ROWS.append(dict(case='active-'+change,admission=admission,release=release,
                                     requests=wire.sent,server_receipts=receipts,edges=fake.rpc_edges,
                                     explicit_update_sent=(change=='explicit-cancel')))
                finally:client.close();thread.join(5)

    def test_interrupted_close_keeps_an_unverified_repeatable_local_result(self):
        class FatalProbe(BaseException):pass
        errors=[('interrupted-close',KeyboardInterrupt('injected close interrupt')),
                ('fatal-close',FatalProbe('injected fatal close')),
                ('fatal-group-close',BaseExceptionGroup('fatal close group',[FatalProbe('member')]))]
        c=rpc()
        for case,error in errors:
            with self.subTest(case=case), backend_fixture() as (backend,events,generation,fake):
                backend.snapshot('interrupted-close',0);lease=bound(backend)
                client,wire,peer,receipts,thread=self.session(backend,fake=fake)
                try:
                    client.call('down',lease,'a')
                    with patch.object(wire,'recv',side_effect=error):
                        with self.assertRaises(type(error)) as raised:client.close()
                    self.assertIs(raised.exception,error)
                    thread.join(3);self.assertFalse(thread.is_alive())
                    result=client.close()
                    self.assertIsInstance(result,dict)
                    self.assertFalse(result['verified'])
                    self.assertEqual(fake.down,set())
                    ROWS.append(dict(case=case,local_close=result,server_receipts=receipts,
                                     edges=fake.rpc_edges,primary_interrupt_preserved=True))
                finally:client.close();thread.join(5)

    def test_buffered_unsolicited_reply_quarantines_before_a_second_send(self):
        c=rpc()
        with backend_fixture() as (backend,events,generation,fake):
            backend.snapshot('extra-reply',0);lease=bound(backend)
            client,wire,peer,receipts,thread=self.session(backend,'extra-reply',fake=fake)
            wire.fault='coalesce-two'
            try:
                with self.assertRaises(c.RpcOutcomeUnknown):client.call('down',lease,'a')
                with self.assertRaises(c.RpcQuarantined):client.call('down',lease,'d')
                self.assertEqual([r['op'] for r in wire.sent],['down'])
                result=client.close();thread.join(3)
                self.assertFalse(thread.is_alive());self.assertFalse(result['verified'])
                self.assertEqual(fake.down,set())
                ROWS.append(dict(case='extra-reply',requests=wire.sent,replies=peer.sent,
                                 local_close=result,server_receipts=receipts,edges=fake.rpc_edges,
                                 post_error_send_count=0))
            finally:client.close();thread.join(5)

    def test_primary_and_detach_failure_are_both_preserved(self):
        c=rpc()
        for phase in ('readiness','close','service'):
            with self.subTest(phase=phase):
                primary=KeyboardInterrupt('primary '+phase)
                cleanup=OSError('secondary socket close')
                class InertSocket:
                    def settimeout(self,_):pass
                    def sendall(self,_):pass
                    def recv(self,_):raise primary
                    def shutdown(self,_):pass
                    def close(self):raise cleanup
                if phase=='readiness':
                    invoke=lambda:c.OwnerRpcClient(InertSocket(),display=':fake',service_id='owned-service-v2')
                elif phase=='service':
                    def invoke():
                        with backend_fixture() as (backend,events,generation,fake):
                            return c.serve_owner(InertSocket(),backend.owner,display=':fake',service_id='owned-service-v2')
                else:
                    client=c.OwnerRpcClient.__new__(c.OwnerRpcClient)
                    client._closed=False;client._quarantined=False;client._close_result=None
                    client._sock=InertSocket();client.service_id='owned-service-v2';client.display=':fake'
                    client.call=lambda *_:(_ for _ in ()).throw(primary)
                    invoke=client.close
                with self.assertRaises(BaseExceptionGroup) as raised:invoke()
                self.assertIs(raised.exception.exceptions[0],primary)
                self.assertIs(raised.exception.exceptions[1],cleanup)
                if phase=='close':self.assertFalse(client.close()['verified'])
                ROWS.append(dict(case='paired-'+phase,primary_preserved=True,cleanup_preserved=True,
                                 primary_type=type(primary).__name__,cleanup_type=type(cleanup).__name__,
                                 scope='inert socket; no transport/native execution'))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path);parser.add_argument('--red',action='store_true')
    args=parser.parse_args()
    names=['test_module_available'] if args.red else None
    suite=unittest.TestSuite(OwnerRpcTests(name) for name in names) if names else unittest.defaultTestLoader.loadTestsFromTestCase(OwnerRpcTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if args.out:
        pins={}
        for module in list(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).resolve()
                if path.is_relative_to(HERE.parents[1]) and path.is_file() and path.suffix=='.py':
                    import hashlib
                    pins[path.relative_to(HERE.parents[1]).as_posix()]=hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        args.out.write_text(json.dumps(dict(source_sha256_lf=pins,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),rows=ROWS),indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
