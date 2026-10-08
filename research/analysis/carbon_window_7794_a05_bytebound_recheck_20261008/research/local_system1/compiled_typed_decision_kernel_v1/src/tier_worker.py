from __future__ import annotations
import gc, json, os, platform, resource, statistics, sys, time
from pathlib import Path
import numpy as np
from kernel import CompiledTypedDecisionKernel, INPUT_DIM, HEADS, TOTAL_LOGITS, canonical_output_hash, validate_typed_output

WARMUPS = 16
MEASURED_QUERIES = 128
QUERY_SEED = 87620260917
KERNEL_SEED = 87617001

def percentile(values, q):
    xs = sorted(values)
    if not xs:
        raise ValueError('empty')
    pos = (len(xs)-1) * q
    lo = int(pos); hi = min(lo+1, len(xs)-1); frac = pos-lo
    return xs[lo]*(1-frac) + xs[hi]*frac

def blas_info():
    try:
        cfg = np.__config__.CONFIG
        return cfg
    except Exception:
        return {'unavailable': True}

def main(param_count: int, out: Path):
    env_threads = {k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    started = time.perf_counter_ns()
    kernel = CompiledTypedDecisionKernel(param_count, KERNEL_SEED + int(param_count))
    setup_done = time.perf_counter_ns()
    rng = np.random.default_rng(QUERY_SEED)
    queries = rng.standard_normal((MEASURED_QUERIES, INPUT_DIM), dtype=np.float32)
    fixed = np.linspace(-1.0, 1.0, INPUT_DIM, dtype=np.float32)
    # Warm the exact decision path; timing output is excluded from formal metrics.
    for i in range(WARMUPS):
        kernel.decide(queries[i % MEASURED_QUERIES])
    a = kernel.decide(fixed); b = kernel.decide(fixed)
    deterministic = canonical_output_hash(a) == canonical_output_hash(b)
    fixed_hash = canonical_output_hash(a)
    typed_errors = validate_typed_output(a)
    if a['yield_count'] <= 0:
        typed_errors.append('yield_unreachable_fixed_probe')
    gc.collect(); gc.disable()
    latencies_ns=[]; output_hashes=[]; all_errors=[]; yields=[]
    timed_start=time.perf_counter_ns()
    for q in queries:
        t0=time.perf_counter_ns(); result=kernel.decide(q); t1=time.perf_counter_ns()
        latencies_ns.append(t1-t0)
        output_hashes.append(canonical_output_hash(result))
        yields.append(result['yield_count'])
        all_errors.extend(validate_typed_output(result))
    timed_end=time.perf_counter_ns(); gc.enable()
    ms=[x/1e6 for x in latencies_ns]
    elapsed_s=(timed_end-timed_start)/1e9
    ru=resource.getrusage(resource.RUSAGE_SELF)
    row={
      'parameter_count':int(param_count),
      'parameter_bytes':int(kernel.parameter_bytes),
      'hidden_dim':int(kernel.hidden_dim),
      'tail_count':int(kernel.tail_count),
      'input_dim':INPUT_DIM,'total_logits':TOTAL_LOGITS,'head_count':len(HEADS),
      'warmups':WARMUPS,'measured_queries':MEASURED_QUERIES,
      'setup_ms':(setup_done-started)/1e6,
      'warm_single_ms':{
        'p50':percentile(ms,0.50),'p95':percentile(ms,0.95),'p99':percentile(ms,0.99),
        'max':max(ms),'min':min(ms),
      },
      'states_per_sec':MEASURED_QUERIES/elapsed_s,
      'deterministic_repeated_input':deterministic,
      'repeated_input_output_hash':fixed_hash,
      'unique_query_output_hashes':len(set(output_hashes)),
      'yield_count_min':min(yields),'yield_count_max':max(yields),'yield_count_total':sum(yields),
      'typed_errors':sorted(set(typed_errors+all_errors)),
      'peak_rss_kb':int(ru.ru_maxrss),
      'environment':{
        'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform(),
        'thread_env':env_threads,'blas':blas_info(),
      },
      'training_steps':0,'gradient_updates':0,'network_calls':0,'task_input_calls':0,'authority_grants':0,
    }
    out.write_text(json.dumps(row,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'parameter_count':param_count,'p95_ms':row['warm_single_ms']['p95'],'typed_errors':row['typed_errors']}))
if __name__=='__main__': main(int(sys.argv[1]),Path(sys.argv[2]))
