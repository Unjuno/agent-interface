"""Ordinary ownership regressions; inert queues, no provider/model/GUI."""
import io
import json
import queue
import threading
import unittest
from codex_app_server_client_v2 import AppServerError, CodexAppServerClient

class Lines:
    def __init__(self):self.rows=queue.Queue();self.last=None
    def __iter__(self):return self
    def __next__(self):
        if self.last is not None:self.last.set();self.last=None
        value,done=self.rows.get(timeout=5)
        if value is None:raise StopIteration
        self.last=done;return json.dumps(value)+'\n'
    def emit(self,value):
        done=threading.Event();self.rows.put((value,done))
        if not done.wait(2):raise TimeoutError('fixture reader did not consume row')
    def finish(self):self.rows.put((None,None))
    def close(self):self.closed=True

class Sink:
    def __init__(self,process):self.process=process
    def write(self,text):
        row=json.loads(text);self.process.sent.append(row)
        self.process.reply(row)
    def flush(self):pass
    def close(self):self.closed=True

class Process:
    def __init__(self,reply):self.sent=[];self.stdout=Lines();self.stdin=Sink(self);self.stderr=io.StringIO();self.reply=reply
    def poll(self):return 0

class ResponseOwnershipTests(unittest.TestCase):
    def client(self,reply):
        p=Process(reply);c=CodexAppServerClient([],process_factory=lambda *a,**k:p)
        def close():p.stdout.finish();c.close(timeout=1)
        self.addCleanup(close);return c,p
    def assert_empty_pending(self,c):self.assertEqual(c._pending,set())
    def alias(self,identifier):
        c,p=self.client(lambda row:(p.stdout.emit({'id':identifier,'result':'poison'}),p.stdout.emit({'id':row['id'],'result':'proper'})))
        self.assertEqual(c.request('fixture',timeout=1),'proper')
        self.assertEqual(list(c._notifications),[{'id':identifier,'result':'poison'}]);self.assertEqual(len(p.sent),1);self.assert_empty_pending(c)
    def test_boolean_id_does_not_alias_active_integer(self):self.alias(True)
    def test_float_id_does_not_alias_active_integer(self):self.alias(1.0)
    def test_request_envelope_remains_notification(self):
        packet={'id':1,'method':'fixture/serverRequest'}
        c,p=self.client(lambda row:(p.stdout.emit(packet),p.stdout.emit({'id':row['id'],'result':'proper'})))
        self.assertEqual(c.request('fixture',timeout=1),'proper');self.assertEqual(list(c._notifications),[packet]);self.assert_empty_pending(c)
    def future(self,error):
        packet={'id':2,**({'error':{'code':-1,'message':'unissued'}} if error else {'result':'unissued'})}
        issued=threading.Event()
        def reply(row):
            if row['id']==1:
                p.stdout.emit(packet);p.stdout.emit({'id':1,'result':'proper-1'})
            else:issued.set()
        c,p=self.client(reply)
        self.assertEqual(c.request('fixture/one',timeout=1),'proper-1')
        value=[];errors=[];done=threading.Event()
        def second():
            try:value.append(c.request('fixture/two',timeout=1))
            except BaseException as e:errors.append(type(e).__name__+': '+str(e))
            finally:done.set()
        t=threading.Thread(target=second);t.start()
        try:
            self.assertTrue(issued.wait(1));done.wait(.05)
            p.stdout.emit({'id':2,'result':'proper-2'})
        finally:t.join(2)
        self.assertFalse(t.is_alive());self.assertEqual(errors,[]);self.assertEqual(value,['proper-2'])
        self.assertEqual(list(c._notifications),[packet]);self.assertEqual([r['id'] for r in p.sent],[1,2]);self.assert_empty_pending(c)
    def test_unissued_future_success_cannot_complete_later_request(self):self.future(False)
    def test_unissued_future_error_cannot_fail_later_request(self):self.future(True)
    def test_immediate_active_response_is_retained(self):
        c,p=self.client(lambda row:p.stdout.emit({'id':row['id'],'result':'proper'}))
        self.assertEqual(c.request('fixture',timeout=1),'proper');self.assert_empty_pending(c)
    def test_genuine_typed_error_is_preserved_and_retires_ownership(self):
        c,p=self.client(lambda row:p.stdout.emit({'id':row['id'],'error':{'code':-1,'message':'proper'}}))
        with self.assertRaisesRegex(AppServerError,'proper'):c.request('fixture',timeout=1)
        self.assert_empty_pending(c)
    def test_timeout_retires_id_and_late_packet_cannot_be_cached(self):
        c,p=self.client(lambda row:None)
        with self.assertRaises(TimeoutError):c.request('fixture',timeout=.01)
        self.assert_empty_pending(c)
        packet={'id':1,'result':'late'};p.stdout.emit(packet)
        self.assertEqual(c._responses,{});self.assertEqual(list(c._notifications),[packet]);self.assertEqual(len(p.sent),1)
    def test_write_error_retires_id_without_resend(self):
        def fail(row):raise OSError('fixture write failed')
        c,p=self.client(fail)
        with self.assertRaisesRegex(OSError,'write failed'):c.request('fixture',timeout=1)
        self.assert_empty_pending(c);self.assertEqual(len(p.sent),1)
    def test_concurrent_active_requests_accept_reverse_response_order(self):
        issued=threading.Event()
        c,p=self.client(lambda row:issued.set() if len(p.sent)==2 else None)
        values={};errors=[]
        def call(label):
            try:values[label]=c.request(label,timeout=2)
            except BaseException as e:errors.append(repr(e))
        threads=[threading.Thread(target=call,args=(label,)) for label in ['a','b']]
        for t in threads:t.start()
        try:
            self.assertTrue(issued.wait(1))
            for row in reversed(p.sent):p.stdout.emit({'id':row['id'],'result':row['method']})
        finally:
            for t in threads:t.join(3)
        self.assertTrue(all(not t.is_alive() for t in threads));self.assertEqual(errors,[]);self.assertEqual(values,{'a':'a','b':'b'});self.assert_empty_pending(c)

if __name__=='__main__':unittest.main()
