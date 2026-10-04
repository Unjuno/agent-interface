import hashlib
from pathlib import Path
import tempfile
import unittest
from verify_packet import manifest_errors, run_errors, busy_phase_errors


class RetainedTests(unittest.TestCase):
    def test_complete_manifest_and_nested_manifest_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'exact.bin').write_bytes(b'exact\r\n\x00')
            line=hashlib.sha256((root/'exact.bin').read_bytes()).hexdigest()+'  exact.bin'
            self.assertEqual(manifest_errors(root,[line]),[])
            self.assertTrue(manifest_errors(root,[]))
            self.assertTrue(manifest_errors(root,[line,line]))
            self.assertTrue(manifest_errors(root,['0'*64+'  ../other']))
            (root/'nested').mkdir();(root/'nested/SHA256SUMS').write_text('not root')
            self.assertTrue(manifest_errors(root,[line]))

    def test_summary_count_type_hypothesis_and_scope(self):
        audit={'status':'METHOD_PASS_CONSTRUCTION_ONLY','hypothesis':'H_PASS_BOUNDARY_CONSTRUCTION_ONLY',
               'rows':8,'old_stamp_expired':{'PUBLISH_DELAY':4,'READER_DELAY':4},'scope':'construction'}
        run={'disposition':audit['status'],'hypothesis':audit['hypothesis'],'rows':8,
             'old_stamp_expired':audit['old_stamp_expired'],'scope':'construction',
             'candidate_invocations':1,'auditor_invocations':1,'retries':0,'GUI_input':0}
        self.assertEqual(run_errors(run,audit),[])
        for field,value in [('candidate_invocations',True),('hypothesis','GENERAL_PASS'),
                            ('rows',9),('scope','A05_cause')]:
            self.assertTrue(run_errors({**run,field:value},audit))

    def test_busy_worker_must_overlap_writer_to_first_read(self):
        import copy
        import json
        row={'load':'cpu_busy','writer':{'stamp_ns':200},
             'reader':{'first_read_finished_ns':300},
             'worker_exit':0,'worker_pid':17,
             'worker_stdout':json.dumps({'start_ns':100,'end_ns':400})}
        self.assertEqual(busy_phase_errors(row),[])
        for start,end in ((1,199),(301,400),(1,200),(300,400),(250,250)):
            changed=copy.deepcopy(row)
            changed['worker_stdout']=json.dumps({'start_ns':start,'end_ns':end})
            self.assertTrue(busy_phase_errors(changed))
        for field,value in (('start_ns',True),('end_ns',None)):
            worker={'start_ns':100,'end_ns':400};worker[field]=value
            self.assertTrue(busy_phase_errors({**row,'worker_stdout':json.dumps(worker)}))


if __name__=='__main__':unittest.main()
