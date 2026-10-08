# Issue #5420 T1 — adaptive symbolic privacy filter

## H/T/D/C/U (frozen before formal execution)

- **H:** When observation requests adapt to prior outputs, per-call authorization and a query-count-only global cap can exceed a declared composition budget; an adaptive filter using exact per-query privacy-loss increments can enforce the bound, while a secret-independent task predicate preserves the declared task utility without secret disclosure.
- **T:** Generate 2,048 paired neighboring synthetic states, differing only in one secret bit and sharing public task state/random uniforms. Compare `STATIC_PER_CALL`, `GLOBAL_QUERY_CAP`, `SYMBOLIC_ODOMETER`, `ADAPTIVE_EPSILON_FILTER`, and `PREDICATE_ONLY`. The first four use an explicitly defined binary randomized-response mechanism with per-query epsilon 0.4 or 0.8, selected adaptively from prior outputs; stop on absolute log-likelihood ratio 2.4 or after eight queries. The count-cap allows at most three requests. The filter admits a query only when cumulative epsilon remains ≤1.2. Predicate-only releases the same secret-independent task predicate and makes no secret query. Emit every input, query route, uniform, response, epsilon increment, likelihood increment, filter decision, and outcome. Independently replay rows and summary; reject four mutations.
- **D:** PASS for the bounded mechanism only if paired states differ nowhere except the secret bit; no adaptive-filter transcript exceeds epsilon 1.2; every request and admit/refuse decision is present in the odometer; static/count/odometer policies show at least one realized composition above 1.2; predicate-only has zero secret queries and exactly chance-level distinguisher accuracy (0.5) while matching task completion; independent row/summary replay has zero errors and rejects 4/4 mutations. Otherwise retain exact FAIL/HOLD.
- **C:** For a route with only one query, per-call authorization may be sufficient. If task utility actually depends on the secret, predicate-only release will not preserve utility. A fixed count cap may be adequate only if route costs/query choices are fixed and known.
- **U:** This is a synthetic, explicit randomized-response channel and a paired-state distinguisher—not a model of pixels/OCR/tool traces. The epsilon guarantee is limited to the declared randomized-response channels and adaptive composition accounting; it is not a DP claim for GUI observations, an end-to-end privacy guarantee, user consent policy, production utility result, or side-channel analysis.

## Frozen mechanism and corpus

- Seed base: `54200930`; 2,048 neighbor pairs, two secret values per pair; 8 potential uniforms per state; paired members share all public fields/uniforms.
- Two channels: `rr-mild` ε=0.4 and `rr-strong` ε=0.8, each exact binary randomized response with truthful probability `exp(ε)/(1+exp(ε))`.
- Adaptive route selection: first query mild; after one response, select strong iff it was `1`; afterward select strong iff the two most recent responses agree, otherwise mild.
- All policies stop at `abs(LLR) >= 2.4` or eight queries, except the adaptive filter additionally checks the next epsilon before admission. The global query budget is three, independent of epsilon.
- Public `task_ready` is independent of the secret, released exactly to every policy at zero secret privacy loss, and is sufficient for the synthetic task-completion predicate.

## Exact formal command

Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (local inspect before freeze must confirm digest/platform). Before invocation create `research/analysis/adaptive_privacy_filter_5420_t1_v1/raw/formal/`.

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --memory 256m --cpus 1 --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src="$PWD/research/analysis/adaptive_privacy_filter_5420_t1_v1",dst=/work,readonly --mount type=bind,src="$PWD/research/analysis/adaptive_privacy_filter_5420_t1_v1/raw/formal",dst=/results python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /work/experiment.py --out /results
```

The independent auditor runs once in the same isolated pinned image with the same mounts: `python /work/audit.py /results`. One formal experiment invocation only; preserve any failed output and do not retry or relabel it.
