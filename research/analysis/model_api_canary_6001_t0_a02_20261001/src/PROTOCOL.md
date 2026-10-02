# Issue #6001 T0 allocation-02 protocol

## H / T / D / C / U

**H.** With a fixed opaque model alias, bracketed canaries plus balanced AB/BA
route order refuse a planted route-comparison confound caused by a hidden
behavior change, while a stationary stochastic control stays under the frozen
false-alarm bound.

**T.** A deterministic mock API emits the frozen five-probe canary deck and
route-task outcomes with fixed seed 60012026. It executes six cases:
stationary noise (200 independent episodes), in-deck behavior shift (matched
unbalanced AB and balanced BA order), out-of-deck shift, schema-only break,
prompt/context drift, and within-block model switch with pre/mid/post canary
brackets. Every request row retains alias, model fingerprint, metadata,
prompt hash, route, phase, probe, attempt, schema result, and outcome. A
separate auditor reads only raw JSONL and does not import the runner.

**D.** PASS_METHOD_SCOPED requires all of the following: zero false alarms
in 200 stationary episodes and a 95% Wilson upper bound at or below 0.05;
the unbalanced AB alias-only and metadata-only comparators falsely promote
the planted route effect; balanced AB/BA removes that main-effect attribution;
the bracketed canary rejects the in-deck shift; the out-of-deck case is
UNKNOWN_COVERAGE; schema-only and prompt/context drift receive distinct
holds; and the mid-block canary detects the within-block switch. Any mismatch
is FAIL_METHOD; provenance, missing rows, or launch ambiguity is STOP.

**C.** Strict snapshot pinning would remove the opaque-alias problem. Randomized
or balanced route order can reduce serial drift confounding without canary
calls. A canary can miss behavior outside its deck and adds request cost.

**U.** This is a finite synthetic mock only. Two hundred null episodes do not
prove a real provider's false-alarm rate, identify weights/system prompts, or
estimate canary sensitivity broadly. It establishes no GUI effect, action
authority, route speedup, real-provider drift, or product-safety claim.

## Frozen execution limits

- Candidate exactly once, in the isolated ARM64 Docker guest.
- Separate raw-only auditor exactly once, only after candidate exit 0.
- No provider/network, model, GUI, GPU, or input.
- No retry. Any Docker launch/setup failure is retained as STOP, not rerun in
  this allocation.
- Candidate and auditor use the exact pinned image digest and network-none;
  read-only source/root; bounded CPU, memory, and PIDs; only the output mount is
  writable.

Host runs before the reserved window are construction rehearsals only.
