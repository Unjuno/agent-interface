import pathlib
import unittest
from core import extract, judge

SOURCE = pathlib.Path(__file__).parent / 'source/v39.py.txt'

class Tests(unittest.TestCase):
    def test_cleanup_attempts_after_first_error(self):
        from probe import cleanup
        calls=[]
        class Pipe:
            def close(self):
                calls.append('close')
                raise OSError('injected close fault')
            def read(self): return 'saved stderr'
        class Process:
            stdin=Pipe();stdout=Pipe();stderr=Pipe()
            def wait(self,timeout): calls.append('wait');return 0
            def poll(self): return 0
        class Thread:
            def join(self,timeout): calls.append('join')
            def is_alive(self): return False
        code,stderr,faults=cleanup(Process(),Thread())
        self.assertEqual(code,0)
        self.assertEqual(stderr,'saved stderr')
        self.assertEqual(calls,['close','wait','join','close','close'])
        self.assertEqual(len(faults),3)
        Process.poll=lambda self: (_ for _ in ()).throw(OSError('poll-fault'))
        calls.clear()
        code,stderr,faults=cleanup(Process(),Thread())
        self.assertEqual(calls,['close','wait','join'])
        self.assertEqual([f['step'] for f in faults],['stdin-close','poll','pipe-close-deferred'])

    def test_source_identity(self):
        receipt = extract(SOURCE.read_bytes())[1]
        self.assertEqual(receipt['sha256'], 'a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e')
        self.assertEqual(receipt['functions'], ['reader', 'wait'])

    def test_bad_source_rejected(self):
        with self.assertRaises(ValueError):
            extract(SOURCE.read_bytes()+b'\n')

    def test_real_functions_on_saved_lines(self):
        import io
        import queue
        factory,_=extract(SOURCE.read_bytes())
        class Process:
            stdout=io.StringIO('{"event":"ready"}\n')
            def poll(self): return None
        q=queue.Queue()
        reader,wait,events=factory(Process(),q)
        reader()
        self.assertEqual(wait(lambda r:r['event']=='ready',timeout=.1), {'event':'ready'})
        self.assertEqual(events,[{'event':'ready'}])
        Process.stdout=io.StringIO('not-json\n')
        reader,_,_=factory(Process(),queue.Queue())
        import json
        with self.assertRaises(json.JSONDecodeError): reader()

    def test_audit_typed_and_payload_checks(self):
        import json
        import tempfile
        from audit import check
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            rows=[]
            for i,(case,o,a,e) in enumerate([('healthy','ready',True,[]),('malformed','TimeoutError',False,['JSONDecodeError']),('array','TypeError',True,[])]):
                row=dict(case=case,pid=i+10,producer_pid=1,outcome=o,reader_alive=a,errors=e,child_alive=True,
                         cleanup_exit=0,reader_retired=True,error_details=[{'doc':'not-json\n','type':'JSONDecodeError','thread':'v39-reader-malformed'}] if e else [],
                         parsed_events=[{'event':'ready','fixture':'synthetic'}] if i==0 else ([[]] if i==2 else []))
                rows.append(row)
                (root/(case+'-result.json')).write_text(json.dumps(row))
                from audit import PAYLOADS
                (root/(case+'-peer.json')).write_text(json.dumps(dict(pid=i+10,ppid=1,written=len(PAYLOADS[case]),emitted_hex=PAYLOADS[case].hex())))
            (root/'RUNTIME.json').write_text(json.dumps({'pid':1,'uid':501,'limits':{'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}}))
            summary=dict(rows=rows,verdict='FINDING_PARSE_FAILURE_NOT_SURFACED',source={'sha256':'wrong'})
            (root/'SUMMARY.json').write_text(json.dumps(summary))
            (root/'source-identity.json').write_text(json.dumps(summary['source']))
            with self.assertRaises(ValueError): check(root)
            from audit import SOURCE_HASH
            summary['source']['sha256']=SOURCE_HASH
            (root/'SUMMARY.json').write_text(json.dumps(summary))
            (root/'source-identity.json').write_text(json.dumps(summary['source']))
            self.assertEqual(check(root),'FINDING_PARSE_FAILURE_NOT_SURFACED')
            for key,value in [('child_alive',False),('cleanup_exit',False),('reader_retired',False),('reader_alive',0),('parsed_events',[{}])]:
                changed=dict(rows[1]);changed[key]=value
                (root/'malformed-result.json').write_text(json.dumps(changed))
                changed_summary=dict(summary);changed_summary['rows']=[rows[0],changed,rows[2]]
                (root/'SUMMARY.json').write_text(json.dumps(changed_summary))
                with self.assertRaises(ValueError): check(root)
                (root/'malformed-result.json').write_text(json.dumps(rows[1]))
                (root/'SUMMARY.json').write_text(json.dumps(summary))

    def test_gate(self):
        rows = [dict(case=c, outcome=o, reader_alive=a, child_alive=True,
                     cleanup_exit=0, reader_retired=True, errors=e)
                for c,o,a,e in [('healthy','ready',True,[]),
                                ('malformed','TimeoutError',False,['JSONDecodeError']),
                                ('array','TypeError',True,[])]]
        self.assertEqual(judge(rows), 'FINDING_PARSE_FAILURE_NOT_SURFACED')
        for key,value in [('child_alive',False),('cleanup_exit',-9),('reader_retired',False)]:
            changed=[dict(x) for x in rows]
            changed[1][key]=value
            self.assertEqual(judge(changed), 'STOP_CUSTODY_OR_CLEANUP')
        rows[1]['outcome']='ready'
        self.assertEqual(judge(rows), 'HOLD_EXPECTATION_NOT_MET')

if __name__ == '__main__':
    unittest.main()
