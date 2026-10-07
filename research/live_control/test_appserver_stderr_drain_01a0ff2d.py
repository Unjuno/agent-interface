"""Ordinary regressions for stderr progress, bounded custody and retirement.

Missing drain catches response backpressure; decoding stderr as text catches
malformed-byte loss; unbounded capture catches diagnostic growth; coupled
journal writes catch drain starvation. Dummy peer supplies no GUI authority.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from codex_app_server_client_v2 import CodexAppServerClient

PEER = r'''
import json, os, sys
request=json.loads(sys.stdin.readline())
payload=bytes.fromhex(sys.argv[1])
while payload:
    n=os.write(2,payload)
    payload=payload[n:]
os.write(1,json.dumps({'id':request['id'],'result':'ok'}).encode()+b'\n')
for line in sys.stdin:
    if json.loads(line).get('method')=='shutdown':break
'''


class StderrDrainTests(unittest.TestCase):
    @contextlib.contextmanager
    def peer(self, payload, journal=None):
        # Keep command short on Windows; the peer repeats one exact chunk.
        code=PEER.replace("payload=bytes.fromhex(sys.argv[1])", "payload=bytes.fromhex(sys.argv[1])*int(sys.argv[2])")
        client=CodexAppServerClient([sys.executable,'-X','utf8','-B','-c',code,payload[0].hex(),str(payload[1])],journal_path=journal)
        try:yield client
        finally:
            client.close(timeout=1)
            for stream in (client.process.stdin,client.process.stdout,client.process.stderr):stream.close()

    def test_large_stderr_does_not_block_response(self):
        with self.peer((b'x'*1024,1024)) as client:
            try:result=client.request('echo',timeout=1)
            except TimeoutError:self.fail('stderr backpressure blocked the JSONL response')
            self.assertEqual(result,'ok')

    def test_tail_is_bounded_exact_bytes_even_with_invalid_utf8(self):
        with self.peer((b'\xff\xfe'*512,1024)) as client:
            try:result=client.request('echo',timeout=1)
            except TimeoutError:self.fail('stderr backpressure blocked the JSONL response')
            self.assertEqual(result,'ok')
            client.notify('shutdown');client.process.wait(timeout=1);client.close(timeout=1)
            snapshot=client.stderr_snapshot()
            self.assertEqual(snapshot['bytes_received'],1048576)
            self.assertEqual(snapshot['tail'],b'\xff\xfe'*32768)
            self.assertTrue(snapshot['complete'])
            self.assertIsNone(snapshot['error'])
            snapshot['tail']=b'corrupted caller copy'
            self.assertEqual(len(client.stderr_snapshot()['tail']),65536)

    def test_journal_lock_does_not_block_stderr_consumption(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.peer((b'j'*1024,1024),str(Path(directory)/'journal.jsonl')) as client:
                self.assertTrue(callable(getattr(client,'stderr_snapshot',None)),
                                'stderr drain state must be observable while journal is locked')
                client._journal_lock.acquire()
                # Bypass only sent journaling to place a request in the real pipe
                # while received journaling is deliberately held at its boundary.
                client.process.stdin.write('{"id":1,"method":"echo"}\n');client.process.stdin.flush()
                try:
                    deadline=time.monotonic()+2
                    while time.monotonic()<deadline:
                        if client.stderr_snapshot()['bytes_received']==1048576:break
                        time.sleep(.005)
                    self.assertEqual(client.stderr_snapshot()['bytes_received'],1048576)
                finally:client._journal_lock.release()
                with client._condition:
                    deadline=time.monotonic()+1
                    while 1 not in client._responses and time.monotonic()<deadline:
                        client._condition.wait(max(0,deadline-time.monotonic()))
                    self.assertEqual(client._responses.pop(1)['result'],'ok')

    def test_stream_read_error_is_retained_without_claiming_eof(self):
        class Broken:
            def read(self,_):raise OSError('directed stderr read failure')
        client=CodexAppServerClient.__new__(CodexAppServerClient)
        client.process=type('Peer',(),{'stderr':Broken()})()
        client._stderr_lock=threading.Lock();client._stderr_tail=b'';client._stderr_bytes=0
        client._stderr_error=None;client._stderr_complete=False
        self.assertTrue(callable(getattr(client,'_read_stderr',None)),
                        'stderr reader must retain read errors without claiming EOF')
        client._read_stderr()
        snapshot=client.stderr_snapshot()
        self.assertFalse(snapshot['complete'])
        self.assertEqual(snapshot['error'],'OSError: directed stderr read failure')
        self.assertEqual(snapshot['tail'],b'')

    def test_close_waits_for_stderr_eof_before_retiring_journal(self):
        class Dead:
            def poll(self):return 0
        with tempfile.TemporaryDirectory() as directory:
            rfd,wfd=os.pipe()
            stream=os.fdopen(rfd,'rb')
            process=Dead();process.stdin=io.StringIO();process.stdout=io.StringIO();process.stderr=stream
            client=CodexAppServerClient([],process_factory=lambda *a,**k:process,journal_path=str(Path(directory)/'journal.jsonl'))
            try:
                with self.assertRaises(TimeoutError):client.close(timeout=.02)
                self.assertFalse(client._journal.closed)
            finally:
                os.close(wfd)
                client.close(timeout=1)
                stream.close()
            self.assertTrue(client._journal.closed)
            self.assertTrue(client.stderr_snapshot()['complete'])


if __name__=='__main__':unittest.main()
