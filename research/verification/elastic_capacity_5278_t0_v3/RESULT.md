# Formal T0 result — allocation 03

Disposition: PASS_ELASTIC_CAPACITY_T0_SCOPED
Host CPython 3.11.9; local CPU only. One formal invocation, exit 0; no model, CUDA, GPU, Docker or network use. Raw output: evidence/formal01/raw.json, SHA-256 4731aee6ba284c26966a7a4178a0137a47091549aae3e9cfff5ab38d8da9ae29 (91,915 bytes). GitHub raw readback was exact before audit. Separate raw-only audit exit 0 is evidence/formal01/audit.json.

## Frozen endpoints

- Short burst usable completions by deadline: elastic 8/8; fixed-small 5/8; strict gain +3.
- Short + sustained burst idle worker-ms: elastic 17,367; fixed-large 43,400. Ratio 40.016%; reduction 59.984%; the frozen threshold was <=75%.
- Peak concurrency: <=4 for all rows; elastic burst peaks at 4.
- Semantic results: independent audit found zero errors, including cross-policy semantic equality.
- Stale work: no stale result completed. Some already-started stale computation is charged as wasted compute.
- Missing mandatory verification: outcomes remain UNCERTAIN, never PASS.
- Corruption controls: 5/5 rejected (missing row, forged digest, untraced completion, resource conservation, mandatory fail-closed).

The prespecified scoped gate passes. This establishes only the frozen deterministic synthetic T0; it is not a real verifier/backend, physical contention/memory/energy benchmark, production scaling, T1 authorization, or general autoscaling claim. Preserve prior v1 import STOP and v2 pre-run STOP; neither was a formal attempt.
