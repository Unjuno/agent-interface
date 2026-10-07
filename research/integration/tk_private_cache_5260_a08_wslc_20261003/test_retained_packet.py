import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from verify_packet import manifest_errors, run_errors, identity_errors, KNOWN_WARNING

class RetainedTests(unittest.TestCase):
    def test_complete_safe_manifest_and_duplicate_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'exact.bin').write_bytes(b'exact\r\n\x00')
            line=hashlib.sha256((root/'exact.bin').read_bytes()).hexdigest()+'  exact.bin'
            self.assertEqual(manifest_errors(root,[line]),[])
            for lines in ([],[line,line],['0'*64+'  ../outside']):
                self.assertTrue(manifest_errors(root,lines))

    def test_retention_must_not_expand_scope_or_boolean_count(self):
        audit={'status':'METHOD_PASS_CONSTRUCTION_ONLY','hypothesis':'DESCRIPTIVE_ONLY_NO_EFFICACY_THRESHOLD','cache_hypothesis':'H_PASS_ENVIRONMENT_CONSTRUCTION_ONLY','rows':8,'scope':'construction',
               'errors':['first-stop'],'groups':{},'observations':[]}
        run={k:v for k,v in audit.items() if k!='status'}
        run.update(disposition='METHOD_PASS_CONSTRUCTION_ONLY',candidate_invocations=1,auditor_invocations=1,
                   retries=0,key_requests=24,save_requests=8)
        self.assertEqual(run_errors(run,audit),[])
        for key,value in (('disposition','METHOD_PASS'),('hypothesis','H_PASS'),('candidate_invocations',True)):
            self.assertTrue(run_errors({**run,key:value},audit))

    def test_exact_warning_retained_without_erasing_identity(self):
        fixture={'allocation':'fresh'};token='fresh:row-000'
        row={'token':token,'app_pid':17,'app_exit':0,'app_stderr':KNOWN_WARNING,
             'instrumentation_mode':'MEMORY_ONLY','ready':{'pid':17,'token':token},
             'app':{'pid':17,'token':token,'schema':'issue5260-tk-app-v1',
                    'instrumentation_mode':'MEMORY_ONLY'}}
        self.assertEqual(identity_errors(row,fixture,0),[])
        for mutate in (lambda r:r.update(app_pid=True),lambda r:r.update(app_stderr='warning'),
                       lambda r:r['app'].update(token='other'),lambda r:r['ready'].update(pid=18)):
            changed=copy.deepcopy(row);mutate(changed)
            self.assertTrue(identity_errors(changed,fixture,0))

if __name__=='__main__':unittest.main()


