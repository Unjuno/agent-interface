"""Factory-failure cleanup retains the primary exception and native file states."""
import builtins
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import codex_app_server_client_v2 as source

class CleanupFault(OSError): pass
class HostileNoteError(OSError):
    def add_note(self, text): raise AssertionError('overridden diagnostic callback')
class JournalProxy:
    def __init__(self, real, mode): self.real=real; self.mode=mode; self.attempts=0; self.fd=real.fileno()
    def close(self):
        self.attempts+=1
        if self.mode=='before': raise CleanupFault('injected before native close')
        self.real.close()
        if self.mode=='after': raise CleanupFault('injected after native close')
    def __getattr__(self,name): return getattr(self.real,name)

class ConstructorFailureRegression(unittest.TestCase):
    def failure(self, error, mode='healthy', expected_closed=True, expect_note=False):
        with tempfile.TemporaryDirectory() as directory:
            opened=[]; factory_calls=[]
            def opened_file(*args,**kwargs):
                proxy=JournalProxy(builtins.open(*args,**kwargs),mode);opened.append(proxy);return proxy
            def factory(*args,**kwargs): factory_calls.append((args,kwargs));raise error
            try:
                with patch.object(source,'open',opened_file,create=True):
                    try: source.CodexAppServerClient(['inert-no-process'],process_factory=factory,journal_path=Path(directory)/'journal')
                    except BaseException as caught:
                        self.assertIs(caught,error)
                    else: self.fail('factory refusal returned')
                self.assertEqual(len(factory_calls),1);self.assertEqual(len(opened),1)
                proxy=opened[0];self.assertEqual(proxy.attempts,1)
                self.assertIs(proxy.real.closed,expected_closed)
                if expected_closed:
                    with self.assertRaises(OSError):os.fstat(proxy.fd)
                else:os.fstat(proxy.fd)
                if expect_note:self.assertIn('journal cleanup failed: CleanupFault',error.__notes__)
                return proxy.attempts
            finally:
                for proxy in opened:proxy.real.close()
    def test_factory_oserror_closes_journal_and_retains_original(self): self.failure(OSError('startup refusal'))
    def test_factory_typeerror_closes_journal_and_retains_original(self): self.failure(TypeError('factory arguments'))
    def test_factory_keyboardinterrupt_closes_journal_and_retains_original(self): self.failure(KeyboardInterrupt('inert fixture only'))
    def test_close_fault_before_native_close_keeps_primary_and_reports_incomplete(self): self.failure(OSError('startup refusal'),'before',False,True)
    def test_close_fault_after_native_close_keeps_primary_and_reports_cleanup_error(self): self.failure(OSError('startup refusal'),'after',True,True)
    def test_overridden_add_note_cannot_replace_primary(self): self.failure(HostileNoteError('startup refusal'),'after',True,True)
    def test_malformed_notes_cannot_replace_primary(self):
        error=OSError('startup refusal');error.__notes__=42;self.failure(error,'after',True)
    def test_without_journal_preserves_original_and_calls_factory_once(self):
        error=TypeError('factory refusal');calls=[]
        def factory(*a,**kw):calls.append(1);raise error
        with patch.object(source,'open',side_effect=AssertionError('unexpected open'),create=True):
            try:source.CodexAppServerClient(['inert-no-process'],process_factory=factory)
            except BaseException as caught:self.assertIs(caught,error)
            else:self.fail('unexpected constructor return')
        self.assertEqual(calls,[1])
    def test_existing_journal_refuses_before_factory_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'journal';p.write_bytes(b'prior exact evidence\n');calls=[]
            def factory(*a,**kw):calls.append(1);raise AssertionError('factory must not run')
            with self.assertRaises(FileExistsError):source.CodexAppServerClient(['inert-no-process'],process_factory=factory,journal_path=p)
            self.assertEqual(calls,[]);self.assertEqual(p.read_bytes(),b'prior exact evidence\n')
    def test_healthy_factory_queued_response_and_journal_preserved(self):
        class InertProcess:
            def __init__(self):
                self.stdin=io.StringIO();self.stdout=io.StringIO('{"id":1,"result":{"healthy":true}}\n');self.stderr=io.StringIO()
            def poll(self):return 0
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'journal';process=InertProcess();client=source.CodexAppServerClient([],process_factory=lambda *a,**kw:process,journal_path=p)
            try:
                client._reader.join(timeout=1);self.assertFalse(client._reader.is_alive())
                self.assertEqual(client.request('inert/healthy'),{'healthy':True})
                rows=[json.loads(x) for x in p.read_bytes().splitlines()]
                self.assertEqual([r['direction'] for r in rows],['received','sent'])
                self.assertEqual(rows[0]['message'],{'id':1,'result':{'healthy':True}})
                self.assertEqual(rows[1]['message'],{'method':'inert/healthy','id':1})
            finally:
                client.close();process.stdin.close();process.stdout.close();process.stderr.close()

if __name__=='__main__':unittest.main()
