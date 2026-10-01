# Integrated efficiency preflight wall accounting v1 — retained result

Task: `INTEGRATED-EFFICIENCY-PREFLIGHT-WALL-ACCOUNTING-20260917-001`  
Issue: #829  
Immutable comparison BASE: `40072ec1962afe9fe1a9f6ade79ce36a2e8cc93f`

Disposition: **`PASS_PREFLIGHT_WALL_ACCOUNTING_RECONSTRUCTED_SCOPED`**.

The frozen formal runner was invoked exactly once. The independent auditor passed every recomputation check. No model, GUI, provider or task-input action occurred in this allocation.

## Finding

The retained #57 comparison audit's published `elapsed_ms` values are the sum of the six task rows only. They are therefore **task-phase elapsed**, not phase-complete elapsed including the separately executed fresh schema preflight. The preflight input tokens were already included in the retained token accounting, so the retained token break-even result is not recomputed here.

| arm | retained task phase | retained schema preflight | reconstructed phase-complete |
| --- | ---: | ---: | ---: |
| plain | 56,412.291157 ms | 6,341.907755 ms | **62,754.198912 ms** |
| ephemeral | 73,238.112924 ms | 7,140.746175 ms | **80,378.859099 ms** |
| persistent | 44,131.281228 ms | 7,495.828365 ms | **51,627.109593 ms** |

After charging the retained schema-preflight wall interval, persistent remains descriptively lower than both controls in this single retained allocation. This does not create a new causal speedup claim or population latency estimate.

The separately retained model subprocess lifetimes are 5,858.4102 ms (plain), 6,845.2538 ms (ephemeral) and 7,190.1764 ms (persistent). Each is positive and bounded by its enclosing preflight interval. They include CLI/process overhead and are **not** labelled model inference time.

## Integrity

- formal invocations: 1; reruns: 0;
- frozen retained source Git blobs: 7/7 exact;
- frozen source readback before formal: exact, `RESULT.json` absent;
- result SHA-256: `6b5525a5f1b26e3afda32cf707230924ecef2ec37014745813dbf6d444a5b3bd`;
- independent audit: PASS; audit SHA-256 `106ef98a08ba592d468892d33af0e31faa84dedb973ca4ebe9e58cd8a29e847c`;
- original retained disposition: `RETAIN`;
- original observed token break-even task: `2`, unchanged and not re-estimated.

## Interpretation boundary

This is a posthoc accounting repair over immutable retained evidence. It establishes that public/release summaries should not describe the old `audit.elapsed_ms` field as full end-to-end elapsed. It does not establish provider-only model latency, monetary cost, human-tempo equivalence, population reliability, or second-domain speed. A future integrated allocation should make schema-preflight/acquisition wall time a first-class field rather than requiring reconstruction.
