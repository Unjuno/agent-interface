import sys,unittest,importlib.util,json
from pathlib import Path
sys.path[:0]=['/study/accepted-sink-source-02','/study']
p=Path('/study/accepted-sink-source-02/cancel_release_publication_59/test_cancel_release_publication.py');spec=importlib.util.spec_from_file_location('frozen_tests',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReferenceRegression(m.CancelReleasePublicationTest):
 @classmethod
 def setUpClass(cls):
  super().setUpClass()
  from accepted_sink_reference import Executor
  cls.Executor=Executor
suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceRegression)
with Path('/out/tests.txt').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
r={'scope':'five unchanged peer fake-Xlib tests with explicit reference Executor substitution; no physical key/game/model','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'success':result.wasSuccessful()};Path('/out/RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if result.wasSuccessful() else 1)
