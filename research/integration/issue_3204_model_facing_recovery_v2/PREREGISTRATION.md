# Preregistration — Issue #3204 model-facing recovery v2

Allocation: `issue3204-model-facing-recovery-orbstack-02`  
Base main: `ddb311528e96e2a613dd660f8cb24b14f413081d`  
Path: `research/integration/issue_3204_model_facing_recovery_v2/`  
Predecessor construction STOP: allocation 01, recorded on #3204; zero model calls.

## H / T / D / C / U

- **H:** An epoch-aware composer should preserve a correct model answer for aligned evidence and same-epoch context within a frozen 50 ms skew bound, while refusing a contradictory cross-epoch visual/state bundle before inference. A strict zero-skew rejector may be safe but lose useful context; latest-arrival and best-effort merges may spend inference on inconsistent bundles.
- **T:** Three fixed task cases, crossed with four frozen policies: `TYPED_EPOCH_AWARE_COMPOSER`, `LATEST_CHANNEL_WINS`, `BEST_EFFORT_MERGE`, `EPOCH_REJECT_ONLY`. Oracle answers are `READY`, `READY`, `ABSTAIN`. Exactly one local vision-model completion per eligible cell, no retries: 9 expected, maximum 9. Record answer correctness, safe abstention, useful coverage, model token/timing receipts, and policy disposition. No action/effect calls.
- **D:** Existing pinned OrbStack image `issue3204-epoch-composer@sha256:6a3bb69f7ab1e386ca0fd6421c7194024fd9acd2978d168a5b877949c890fa51` (`linux/arm64`). Container runs with `--network none`, read-only root/source, separate output and RPC-exchange mounts. A frozen host-side coordinator only forwards the container-produced request to local Ollama `127.0.0.1:11434` and returns the exact response through the shared volume; it makes no other network requests. Local model `qwen2.5vl:7b`, digest `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`, Ollama 0.34.2, temperature 0, seed 3204, maximum 32 generated tokens. A second network-none container independently audits results and mutation controls.
- **C:** Scenario manifest and all Python sources are SHA-256-frozen before the first inference. Construction STOP from allocation 01 remains unchanged. The host coordinator verifies the local model digest before and after the one-shot; no model pull. Any identity mismatch, RPC timeout, invalid model response, or container failure is retained as STOP/FAIL with no retry. Source and input are mounted read-only; only output and RPC exchange are writable. The independent auditor does not import runner/policy functions.
- **Decision gate:** `PASS_MODEL_FACING_EPOCH_COMPOSITION_SCOPED` iff the typed candidate returns the exact oracle answer on all three cases, makes zero calls for the conflict case, has at least one more exact task answer than `EPOCH_REJECT_ONLY`, and all sources/model/result/audit/corruption gates pass. Any wrong typed answer or unsafe non-abstaining conflict answer is FAIL. Infrastructure, model digest, or audit-integrity mismatch is STOP; malformed model output is retained and counts incorrect, without retry.
- **U:** Three synthetic visual-status cases, one local vision model, no GUI capture or action. This measures model-facing answer/abstention behavior for this declared channel contract only; no real application effect, general multimodal reasoning, recovery-time benefit, production synchronization, or efficiency claim.

## Frozen scenarios and expected outputs

1. `aligned`: image/UI tree/state all identify task A, epoch 4, green/READY, identical capture timestamp. Expected `READY`.
2. `bounded_skew`: same task and epoch 7; green/READY image at 200 ms, UI tree at 230 ms, state at 240 ms; maximum skew 40 ms, within 50 ms. Expected `READY`. Candidate marks context non-authoritative; reject-only abstains.
3. `cross_epoch_conflict`: same target, image red/BLOCKED at epoch 8, current UI tree/state green/READY at epoch 9, plus a delayed epoch-8 duplicate state arriving last. Expected `ABSTAIN`. Candidate and reject-only refuse before inference; the two merging policies receive their frozen selected/all-channel bundle.

Policy-by-scenario call count is fixed at 4 + 3 + 2 = 9. One prompt template and one JSON answer schema are used for all calls. No task action is available to the model or harness.
