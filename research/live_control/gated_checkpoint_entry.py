"""Test-only verifier gate; no input-owner or cancellation changes."""
import sys,time
from pathlib import Path
import effect_checkpoint
gate=Path(sys.argv.pop(1));original=effect_checkpoint.Checkpoints.request
def blocked(path,contract):
    gate.with_suffix('.waiting').write_text(str(time.perf_counter_ns()))
    deadline=time.monotonic()+20
    while not gate.exists():
        if time.monotonic()>deadline:raise TimeoutError('test verifier gate')
        time.sleep(.005)
    return effect_checkpoint.sample(path,contract)
def request(self,path,contract,metadata,verifier=None):
    return original(self,path,contract,metadata,blocked)
effect_checkpoint.Checkpoints.request=request
import interactive_v29
interactive_v29.main()
