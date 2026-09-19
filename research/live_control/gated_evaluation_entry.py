"""Test-only evaluation gate; input execution and ordinary scoring are unchanged."""
import json,sys,time
from pathlib import Path
import interactive_v26 as runtime
gate=Path(sys.argv.pop(1));original=runtime.suite.evaluate
def evaluate(*args,**kwargs):
    started=time.perf_counter_ns()
    gate.with_suffix('.waiting').write_text(json.dumps(dict(started_ns=started)))
    deadline=time.monotonic()+10
    while not gate.exists():
        if time.monotonic()>=deadline:raise TimeoutError('test evaluation gate not released')
        time.sleep(.005)
    released=time.perf_counter_ns()
    result=original(*args,**kwargs)
    gate.with_suffix('.timing').write_text(json.dumps(dict(started_ns=started,released_ns=released,finished_ns=time.perf_counter_ns())))
    return result
runtime.suite.evaluate=evaluate
runtime.main()
