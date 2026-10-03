import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from verify_packet import manifest_errors, stream_errors, run_errors


class RetainedPacketTests(unittest.TestCase):
    def test_manifest_exact_complete_including_nested_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'a.bin').write_bytes(b'exact\r\n\x00')
            line=hashlib.sha256((root/'a.bin').read_bytes()).hexdigest()+'  a.bin'
            self.assertEqual(manifest_errors(root,[line]),[])
            for lines in ([],[line,line],['0'*64+'  a.bin'],['0'*64+'  ../other']):
                self.assertTrue(manifest_errors(root,lines))
            (root/'nested').mkdir();(root/'nested/SHA256SUMS').write_text('not root')
            self.assertTrue(manifest_errors(root,[line]))

    def test_capture_has_exact_typed_receipt_and_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            attempt={'argv':['owned'],'binding':{'allocation':'new'},
                     'started_utc':'2026-10-03T15:00:00+00:00'}
            for name,value in [('attempt.json',json.dumps(attempt).encode()),
                               ('stdout.bin',b'out\n'),('stderr.bin',b'warning\n')]:
                (root/name).write_bytes(value)
            receipt={**attempt,'finished_utc':'2026-10-03T15:00:01+00:00',
                     'wall_seconds':1.0,'exit_code':0,'launch_error':None,
                     'output_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest()
                                      for x in root.iterdir()}}
            self.assertEqual(stream_errors(root,receipt),[])
            for field,value in [('exit_code',False),('wall_seconds',True),
                                ('wall_seconds',10),('argv',['other'])]:
                self.assertTrue(stream_errors(root,{**receipt,field:value}))
            (root/'stderr.bin').write_bytes(b'')
            self.assertTrue(stream_errors(root,receipt))

    def test_hypothesis_failure_cannot_be_promoted_in_summary(self):
        audit={'status':'METHOD_PASS_CONSTRUCTION_ONLY',
               'hypothesis':'H_FAIL_FINITE_FIXTURE_ONLY','errors':[],
               'rows':10,'groups':{'ACK_TARGET':{'n':4,'admitted':3}}}
        run={'allocation':'new','disposition':audit['status'],
             'hypothesis':audit['hypothesis'],'rows':10,'groups':audit['groups'],
             'candidate_invocations':1,'auditor_invocations':1,'retries':0,
             'freeze_sha256':'f','candidate_raw_sha256':'r','auditor_raw_sha256':'a'}
        self.assertEqual(run_errors(run,audit,'r','a','f'),[])
        for field,value in [('hypothesis','H_PASS_FINITE_FIXTURE_ONLY'),
                            ('rows',11),('candidate_invocations',True),
                            ('freeze_sha256','different')]:
            self.assertTrue(run_errors({**run,field:value},audit,'r','a','f'))


if __name__=='__main__':unittest.main()
