import json
import pathlib
import tempfile
import unittest
from audit import check

class Tests(unittest.TestCase):
    def fixture(self,root):
        runtime=dict(pid=1,uid=501,python='3.12.12',cgroup='0::/fixture',limits={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'},
            original_sha256='a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e',
            candidate_sha256='dca770e5e0c532b301b12032c9532bd5fae602947caff4fff21bde60634a57f1')
        specs=[('healthy',['ready'],[b'{"event":"ready","fixture":"E02"}\n'],True),
               ('json_fault',['_SessionReaderFailure'],[b'{"event":\n'],False),
               ('ready_then_fault',['ready','_SessionReaderFailure'],[b'{"event":"ready","fixture":"E02"}\n',b'{"event":\n'],False),
               ('array',['TypeError'],[b'[1]\n'],True),('utf8_fault',['_SessionReaderFailure'],[b'\xff\n'],False),
               ('eof_live',['TimeoutError'],[b''],False)]
        rows=[]
        for i,(case,outcomes,payloads,alive) in enumerate(specs):
            cause={'type':'UnicodeDecodeError','object_hex':'ff0a','doc':None} if case=='utf8_fault' else {'type':'JSONDecodeError','doc':'{"event":\n','object_hex':None}
            results=[dict(outcome=o,cause=cause if o=='_SessionReaderFailure' else None,start_ns=20+j*30,end_ns=30+j*30,elapsed_ns=10) for j,o in enumerate(outcomes)]
            row=dict(case=case,pid=i+8,producer_pid=1,results=results,reader_alive=alive,child_alive=True,
                cleanup_exit=0,reader_retired=True,fatal=None,cleanup_faults=[],unhandled=[],
                handshake={'ready_return_ns':30,'continue_start_ns':35,'continue_return_ns':40} if case=='ready_then_fault' else None,
                parsed_events=[{'event':'ready','fixture':'E02'}] if case in ('healthy','ready_then_fault') else ([[1]] if case=='array' else []))
            rows.append(row)
            (root/(case+'-result.json')).write_text(json.dumps(row))
            (root/(case+'-peer.jsonl')).write_text(''.join(json.dumps(dict(kind='stdout-close' if case=='eof_live' else 'write',pid=i+8,ppid=1,hex=p.hex(),written=len(p),start_ns=10+j*35,return_ns=11+j*35,monotonic_ns=12+j*35))+'\n' for j,p in enumerate(payloads)))
        summary=dict(status='COMPLETE',rows=rows,runtime=runtime,native_runs=1,retries=0,timeout_override_seconds=.35)
        (root/'SUMMARY.json').write_text(json.dumps(summary))
        (root/'RUNTIME.json').write_text(json.dumps(runtime))
        return summary

    def test_positive_and_semantic_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);summary=self.fixture(root)
            self.assertEqual(check(root)[0],'PASS_CANDIDATE_READER_SIGNAL')
            for key,value in [('cleanup_exit',False),('child_alive',False),('reader_retired',False),('reader_alive',0),('producer_pid',True)]:
                row=dict(summary['rows'][1]);row[key]=value
                changed=dict(summary);changed['rows']=[dict(r) for r in summary['rows']];changed['rows'][1]=row
                (root/'json_fault-result.json').write_text(json.dumps(row));(root/'SUMMARY.json').write_text(json.dumps(changed))
                with self.subTest(key=key),self.assertRaises(ValueError): check(root)
                (root/'json_fault-result.json').write_text(json.dumps(summary['rows'][1]));(root/'SUMMARY.json').write_text(json.dumps(summary))
            changed=dict(summary);del changed['native_runs']
            (root/'SUMMARY.json').write_text(json.dumps(changed))
            with self.assertRaises((KeyError,ValueError)): check(root)
            (root/'SUMMARY.json').write_text(json.dumps(summary))
            row=dict(summary['rows'][2]);row['handshake']=dict(row['handshake']);row['handshake']['continue_start_ns']=55
            changed=dict(summary);changed['rows']=[dict(r) for r in summary['rows']];changed['rows'][2]=row
            (root/'ready_then_fault-result.json').write_text(json.dumps(row));(root/'SUMMARY.json').write_text(json.dumps(changed))
            with self.assertRaises(ValueError): check(root)

if __name__=='__main__': unittest.main()
