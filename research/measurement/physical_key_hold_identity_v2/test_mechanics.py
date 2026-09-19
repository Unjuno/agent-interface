from model import Candidate,Event,LifecycleError
from oracle import HistoryOracle
def run(events):
 c=Candidate();o=HistoryOracle()
 for e in events:
  assert c.step(e)==o.step(e);assert c.snapshot()==o.snapshot()
 return c.snapshot()
run([Event('down','o','i','K',True),Event('down','o','i','K',False),Event('up','o','i','K',True),Event('down','o','i','K',True)])
try: Candidate().step(Event('bad','o','i','K',True));raise AssertionError
except LifecycleError: pass
print('MECHANICS_PASS')
