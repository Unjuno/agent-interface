import sys,json,time,unittest
from pathlib import Path
sys.path.insert(0,'/source')
import test_executor_owner_cancel_cause_v1 as fixture
original=fixture.executor_v12.Executor
events=[]
class TracedExecutor(original):
    def __init__(self,backend,emit):
        def traced(event):
            events.append({'observed_ns':time.perf_counter_ns(),'event':json.loads(json.dumps(event))})
            return emit(event)
        super().__init__(backend,traced)
fixture.executor_v12.Executor=TracedExecutor
suite=unittest.defaultTestLoader.loadTestsFromTestCase(fixture.ExecutorOwnerCancelCauseTests)
result=unittest.TextTestRunner(verbosity=2).run(suite)
record={'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'pass':result.wasSuccessful(),'events':events,'scope':'Actual software threads with fake Xlib and supplied schedule; no physical input/game/model'}
Path('/out/RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
raise SystemExit(0 if result.wasSuccessful() else 1)
