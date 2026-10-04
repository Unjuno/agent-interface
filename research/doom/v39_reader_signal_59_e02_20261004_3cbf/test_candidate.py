import io
import json
import pathlib
import queue
import unittest
from candidate import extract,repair

SOURCE=(pathlib.Path(__file__).parent/'source/v39-original.py.txt').read_bytes()

class Process:
    def __init__(self,text): self.stdout=io.StringIO(text)
    def poll(self): return None

class Tests(unittest.TestCase):
    def make(self,text): return extract(repair(SOURCE))(Process(text),queue.Queue())

    def test_parse_fault_reaches_wait_with_original_cause(self):
        reader,wait,events=self.make('{"event":\n')
        caught=None
        try: reader()
        except Exception as exc: caught=exc
        self.assertIsNone(caught,'reader must transport exception, not lose it')
        with self.assertRaises(RuntimeError) as raised: wait(lambda r:False,timeout=.01)
        self.assertEqual(type(raised.exception).__name__,'_SessionReaderFailure')
        self.assertIsInstance(raised.exception.__cause__,json.JSONDecodeError)
        self.assertEqual(raised.exception.__cause__.doc,'{"event":\n')
        self.assertEqual(events,[])

    def test_normal_ready_precedes_later_reader_fault(self):
        reader,wait,events=self.make('{"event":"ready","fixture":"E02"}\n{"event":\n')
        try: reader()
        except Exception: pass
        self.assertEqual(wait(lambda r:r['event']=='ready',timeout=.01)['fixture'],'E02')
        caught=None
        try: wait(lambda r:False,timeout=.01)
        except Exception as exc: caught=exc
        self.assertEqual(type(caught).__name__,'_SessionReaderFailure')
        self.assertEqual(len(events),1)

    def test_shape_remains_separate_wait_fault(self):
        reader,wait,events=self.make('[1]\n')
        reader()
        with self.assertRaises(TypeError): wait(lambda r:False,timeout=.01)
        self.assertEqual(events,[[1]])

    def test_healthy_ready_preserved(self):
        reader,wait,events=self.make('{"event":"ready","fixture":"E02"}\n')
        reader()
        self.assertEqual(wait(lambda r:True,timeout=.01)['event'],'ready')

    def test_monitor_priority_preserved_before_later_fault(self):
        reader,wait,_=self.make('{"event":"observation","sequence":3}\n{"event":\n')
        class Monitor:
            event_types={'observation'}
            def observe(self,row): return {'event':'running_action_invalidation','reason':'guard'}
        reader()
        result=wait(lambda r:True,timeout=.01,observation_monitor=Monitor())
        self.assertEqual(result,{'event':'running_action_invalidation','reason':'guard'})

    def test_decoder_fault_reaches_wait(self):
        process=Process('')
        process.stdout=io.TextIOWrapper(io.BytesIO(b'\xff\n'),encoding='utf-8',errors='strict')
        reader,wait,_=extract(repair(SOURCE))(process,queue.Queue())
        reader()
        with self.assertRaises(RuntimeError) as raised: wait(lambda r:False,timeout=.01)
        self.assertIsInstance(raised.exception.__cause__,UnicodeDecodeError)
        self.assertEqual(raised.exception.__cause__.object,b'\xff\n')

    def test_last_cell_dead_peer_cannot_complete(self):
        from probe import is_complete
        rows=[dict(child_alive=True,fatal=None,cleanup_faults=[],cleanup_exit=0,reader_retired=True) for _ in range(6)]
        self.assertTrue(is_complete(rows))
        rows[-1]['child_alive']=False
        self.assertFalse(is_complete(rows))

    def test_eof_fixture_closes_actual_pipe_before_peer_exit(self):
        import selectors
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            peer=pathlib.Path(__file__).parent/'peer.py'
            process=subprocess.Popen([sys.executable,'-B',str(peer),'eof_live',str(pathlib.Path(tmp)/'peer.jsonl')],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout,selectors.EVENT_READ)
                    ready=bool(selector.select(timeout=1))
                self.assertTrue(ready,'actual stdout pipe must become EOF while peer remains alive')
                self.assertEqual(process.stdout.read(1),b'')
                self.assertIsNone(process.poll())
            finally:
                process.stdin.close();process.wait(timeout=5)
                process.stdout.close();process.stderr.close()

if __name__=='__main__': unittest.main()
