import sys,unittest,json,importlib.util
from pathlib import Path
sys.path.insert(0,'/source/research/live_control')
from input_owner_cancel_telemetry_v1 import InputOwner
import test_input_owner_v11 as telemetry
telemetry.InputOwner=InputOwner
path=Path('/source/research/doom/results/cause/test_cancel_release_cause.py')
spec=importlib.util.spec_from_file_location('cause_cases',path);cause=importlib.util.module_from_spec(spec);spec.loader.exec_module(cause)
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(telemetry.InputOwnerV11Tests),unittest.defaultTestLoader.loadTestsFromTestCase(cause.CancellationReleaseCauseTests)])
r=unittest.TextTestRunner(verbosity=2).run(suite)
record={'tests':r.testsRun,'errors':len(r.errors),'failures':len(r.failures),'pass':r.wasSuccessful(),'scope':'Existing five telemetry contracts explicitly substitute additive subclass; current three fake-Xlib cause cases point OWNER_UNDER_TEST at candidate. No physical input/game/model.'}
Path('/out/RESULT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(0 if r.wasSuccessful() else 1)
