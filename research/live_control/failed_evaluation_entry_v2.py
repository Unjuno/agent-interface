"""Test-only evaluator exception after ordinary GUI input completes."""
import sys,time,json
from pathlib import Path
import interactive_v27 as runtime
marker=Path(sys.argv.pop(1))
def evaluate(*args,**kwargs):
    marker.write_text(json.dumps(dict(called_ns=time.perf_counter_ns(),injected='RuntimeError')))
    raise RuntimeError('injected evaluator failure')
runtime.suite.evaluate=evaluate
runtime.main()
