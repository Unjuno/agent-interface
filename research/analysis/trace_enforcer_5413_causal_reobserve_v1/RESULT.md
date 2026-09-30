# Issue #5413 causal-reobserve boundary T0

Allocation: `trace-causal-reobserve-5413-20261001-01`  
Frozen source main: `2197bead5ffa7dc226390becc811913159c8438e`  
Disposition: `PASS_CAUSAL_REOBSERVE_BOUNDARY_CONSTRUCTION_ONLY`.

## H / T / D / C / U

- **H:** A reobserve request is not fresh evidence. Invalidation should clear only after an observation is linked to the currently pending request, has the current generation, and has a strictly newer sequence. Polling while pending must be idempotent; actions remain blocked until such evidence arrives.
- **T:** Exhaustive candidate enumeration of every trace length 0–4 over seven frozen events (2,801 traces), eight fixed unit tests, a separately implemented raw-only reference audit, and five corruption controls.
- **D:** Unit suite 8/8. Candidate enumerated all 2,801 traces. Independent auditor returned `passed=true`, `errors=[]`, and rejected all 5/5 mutations. It reconstructed every transcript from the event word and independently verified generation/request/sequence binding, stale action blocking, and request idempotence.
- **C:** CPython 3.11.9 host CPU, standard library only. The synthetic event metadata is treated as input; it is not connected to a real capture channel, clock, X11 session, MAP01 episode, model, or task effect.
- **U:** This validates a finite bookkeeping boundary only. It does not demonstrate useful feedback, causal capture authenticity, reaction latency, live safety, end-to-end benefit, or MAP01 recovery. It does not close Issue #5413 or #59 and is not authorization to alter runtime behavior.

The raw transcript (stored with lossless gzip transport compression as `raw.json.gz`) and exact one-shot command outcomes are in `RUN_LOG.md`; frozen input/source identities are in `FREEZE.json`. No Docker, GPU, CUDA, model load, GUI, or external service was used because this finite deterministic checker requires none and the shared Docker lane has no assignment for this allocation.
