# Issue #3895 formal outcome

## Disposition

**HOLD_PROTOCOL_DEVIATION**. The numeric, route, state, and independent row-audit gates passed for the single fresh synthetic seed 3444, but the formal task description in Issue #3895 required 400 base-pretraining updates. The frozen #3701 runner inherited for this allocation performs 120 base-pretraining updates (`STEPS=120`), and the successor runner preserved that value. Therefore the executed treatment did not match Issue #3895's stated base-update count. This discrepancy was discovered after the one-shot run; no training rerun or post-outcome tuning was performed. The result must not be promoted as a full preregistered PASS.

The scoped independent audit itself returned `PASS_MULTI_SKILL_ROUTING_SCOPED`, zero errors, and recomputed all 24,576 retained predictions. It establishes the recorded metrics for the executed 120-base-update treatment, not conformance to the issue's 400-update specification.

Dispatch-selected routed held-out accuracies: A **0.95923**, B **0.92603**, C **0.94678** (all >=0.90). Shared adapter after sequential B→C updates scored A **0.01904**, B **0.00024**, C **0.96143**. All six invalid routes yielded; base immutability and runner full-state round-trip/rollback checks passed. The auditor verified state payload hashes, tensor structure, unchanged frozen-core values, and recomputed every row metric.

## Execution

Exactly one local RTX 3080 Laptop GPU process completed with exit 0; no retry or tuning. Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1, deterministic algorithms, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8`. This is host CUDA evidence, not a container result.

Adapter setup 0.7277 ms; pretrain 205.2279 ms; updates global-B/C 143.3980/136.3524 ms and separate-B/C 149.1632/187.3515 ms. Dispatch-only median 0.000136 ms/call (not model inference or load latency).

The byte-exact original stdout is preserved losslessly as deterministic gzip Base64 in `FORMAL_STDOUT.json.gz.b64`; metadata records raw stdout SHA-256/size plus gzip and Base64 hashes. Empty stderr is retained. The source/output are unchanged by this disposition amendment.

## Limits

One fresh seed in one small synthetic related-task family. No realistic skill transfer, concurrency/crash durability, GUI usefulness, runtime integration, inference/model-load latency, or action-safety claim. The numeric findings describe only the executed 120-base-update treatment; they do not establish the requested 400-update allocation.
