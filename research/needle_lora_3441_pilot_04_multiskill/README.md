# Issue #3701 — two-skill adapter interference allocation

This additive pilot tests whether separate skill-keyed rank-2 adapters retain
base skill A while supporting skills B and C, compared with one adapter updated
sequentially for B then C. It does not modify pilot-01/02/03 evidence or runtime
code.

## H / T / D / C / U

- **H:** Explicit fail-closed dispatch can retain skill A on the immutable base
  and route B/C to separately named adapters with at least 0.90 held-out
  accuracy each. A shared adapter trained for B then C may interfere across
  skills; a separately reported drop of at least 0.10 is the preregistered
  threshold for calling that interference measurable.
- **T:** See `evidence/FREEZE.json` for exact source hashes, data seeds, MLP and
  LoRA shapes, optimizer/update schedule, host/GPU details and single-allocation
  protocol. `runner.py` performs one synthetic GPU allocation; it has no model
  provider, GUI, input or network use.
- **D:** Scoped routing PASS requires A/B/C held-out accuracy >=0.90, unknown or
  stale/mismatched/incomplete route metadata to yield, immutable base tensors,
  exact tensor-by-tensor learned snapshot round-trip and rollback for both
  adapters. A separate metric reports whether the shared sequential adapter
  loses >=0.10 accuracy on any skill. Snapshot mismatch is a distinct FAIL.
- **C:** This Issue explicitly allows the local Windows RTX 3080 host fallback
  when Docker Desktop is unavailable. The host result is never described as a
  container PASS. Docker availability and CUDA-memory-stat limitations are
  retained separately. Synthetic in-memory task only; no runtime authority.
- **U:** One seed and a simple 8-feature/four-class task do not establish
  realistic skill transfer, role-graph performance, concurrent writes,
  crash-safe persistence, vision/GUI utility, or action safety. Dispatch-only
  timing excludes inference and model loading.

Construction-only checks are in `test_runner.py`; they do not perform the
formal training/evaluation allocation. The formal script is invoked once after
the committed freeze, with raw JSON output retained under `artifacts/`.
