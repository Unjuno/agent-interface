# Issue #3895 formal outcome

## Disposition

**PASS_MULTI_SKILL_ROUTING_SCOPED** for the single fresh synthetic seed 3444. The frozen independent CPU auditor returned `integrity=true`, zero errors, and recomputed all 24,576 retained class predictions (3 skills × 2 arms × 4,096 rows).

Dispatch-selected routed held-out accuracies: A **0.95923**, B **0.92603**, C **0.94678** (all >=0.90). The shared adapter after sequential B→C updates scored A **0.01904**, B **0.00024**, C **0.96143**. These demonstrate this run's synthetic interference pattern only; not real-world skill transfer.

## Integrity and execution

One local RTX 3080 Laptop GPU process completed with exit 0; no retry or tuning. Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1, deterministic algorithms, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8`. This is host CUDA evidence, not a container result.

All six invalid skill/epoch/identity/version routes returned YIELD. The A base was tensor-identical. Full adapter module state_dicts (including frozen core tensors) were serialized for initial and learned states; runner round-trip and rollback assertions were exact, and the independent audit validated snapshot payload hashes, tensor structure and unchanged frozen-core values. Adapter setup 0.7277 ms; pretrain 205.2279 ms; updates global-B/C 143.3980/136.3524 ms and separate-B/C 149.1632/187.3515 ms. Dispatch-only median 0.000136 ms/call (not model inference or load latency).

Construction checks were 9/9 and auditor corruption checks 4/4 before the sole formal invocation. The byte-exact original stdout is preserved losslessly as deterministic gzip Base64 in `FORMAL_STDOUT.json.gz.b64`; metadata records raw stdout SHA-256/size plus gzip and Base64 hashes. Empty stderr is retained. No prior #3701/#3714 evidence was modified.

## Limits

One fresh seed in one small synthetic related-task family. No realistic skill transfer, concurrency/crash durability, GUI usefulness, runtime integration, inference/model-load latency, or action-safety claim. Shared-adapter contrasts are descriptive within this allocation; no broad causal or product claim follows.
