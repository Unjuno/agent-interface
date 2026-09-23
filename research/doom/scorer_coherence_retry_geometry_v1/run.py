from __future__ import annotations
import hashlib, json
from pathlib import Path
import geometry

HERE=Path(__file__).resolve().parent
T=geometry.T_NS
THREE_BOUND=(2*T)//3
TWO_BOUND=T//2
SPANS=[10_000_000,18_000_000,THREE_BOUND,((2*T+2)//3)+1_000,20_000_000,25_000_000,T]

def sha(p): return hashlib.sha256((HERE/p).read_bytes()).hexdigest()

def row(span,attempts):
    ints=geometry.continuous_all_failure_intervals(span,attempts,T)
    grid=geometry.grid_failure_phases(span,attempts,T,geometry.GRID_STEP_NS)
    measure=geometry.interval_measure(ints)
    return {
      'span_ns':span,'attempts':attempts,
      'interval_failure_exists':bool(ints),
      'intervals':ints,'failure_measure_ns':measure,
      'failure_fraction':measure/T,
      'grid_failure_exists':bool(grid),
      'grid_failure_count':len(grid),
      'grid_points':len(range(0,T,geometry.GRID_STEP_NS)),
      'first_grid_failure_phase_ns':grid[0] if grid else None,
    }

def main():
    out=HERE/'result.json'
    if out.exists(): raise RuntimeError('formal deterministic output already exists')
    rows=[row(s,3) for s in SPANS]
    controls=[row(TWO_BOUND,2),row(TWO_BOUND+1,2),row(T,2)]
    rejected=[]
    for bad in [0,-1]:
      try: geometry.continuous_all_failure_intervals(bad,3,T)
      except ValueError: rejected.append(bad)
    result={
      'task':'MAP01-SCORER-COHERENCE-RETRY-GEOMETRY-20260917-001',
      'formal_deterministic_invocations':1,'reruns':0,
      'period_ns':T,'sample_hz':35.0,'grid_step_ns':geometry.GRID_STEP_NS,
      'three_attempt_bound_floor_ns':THREE_BOUND,
      'two_attempt_bound_floor_ns':TWO_BOUND,
      'rows':rows,'two_attempt_controls':controls,'rejected_spans':rejected,
      'source_sha256':{'geometry.py':sha('geometry.py'),'run.py':sha('run.py')},
    }
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
