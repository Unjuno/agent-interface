# Rank-1 online LoRA skill update — Issue #4519

Successor allocation after #4507's pre-training output-contract STOP. Preserve that STOP unchanged; this is a new fresh-seed allocation, not a retry. See `PREREGISTRATION.json` for the machine-readable allocation and gates.

The paired arms share a trained immutable role-A base, generated support/held-out rows, support order, and precomputed minibatch indices. They differ only in output-LoRA rank (1 vs 2). Each of 16 feedback arrivals causes exactly eight AdamW updates over the bounded seen-row buffer. Per-feedback timing includes those eight optimizer updates and excludes held-out evaluation. Role A uses the base route; role B uses adapter version 1. Invalid role/version or missing adapter must YIELD.

Fresh seeds are 75111, 75222, and 75333. The independent auditor regenerates support/held-out data and sampling schedules, recomputes every held-out prediction from retained base/adapter tensors, derives every accuracy point and p95 from raw rows, and checks the frozen source/image. No real user feedback, GUI, provider, network, or action authority is involved.

The output contract explicitly permits only an empty output directory or one exact frozen FORMAL_INVOCATION.json marker, resolving #4507's orchestration mismatch. A construction test exercises this boundary without optimizer work.
