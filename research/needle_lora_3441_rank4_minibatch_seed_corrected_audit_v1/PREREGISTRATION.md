# Issue #3887 independent CPU audit — H / T / D / C / U

## H — Hypothesis

An independent implementation that does not import the frozen runner or its
buggy auditor can reconstruct all 160 retained held-out prediction rows
(five seeds × two arms × sixteen arrivals), their exact 4,096-label metrics,
routes, sampler schedules, deterministic data hashes, and the preregistered
`HOLD_LEGACY_COLLAPSE_NOT_REPRODUCED` decision from the merged evidence.

## T — Treatment and freeze

- Audit only the immutable Issue #3887 allocation already on `main`; do not
  launch an optimizer, model evaluation, or GPU operation.
- Read `FORMAL_STDOUT.json`, `RAW_RESULT.json.gz.b64`, `FORMAL_METADATA.json`,
  `FREEZE.json`, `SHA256SUMS.txt`, `SOURCE_RUNNER.py`,
  `SOURCE_3807_BASELINE.py`, `audit.py`, and `AUDIT.json` from
  `research/needle_lora_3441_rank4_minibatch_seed_corrected_v1/`.
- Verify frozen source hashes, both encodings of the compressed raw payload,
  decompressed byte length/SHA-256, all regenerated CPU tensors/labels, all
  held-out predictions, metrics, routes, sampler streams, and the decision
  gates. The original auditor is evidence only; do not import or execute it.
- Construction controls cover packed-label round trips, independent metric
  recomputation, route rejection, prediction/hash mismatch, and a wrong
  stored metric. Run those controls before the single formal audit invocation.
- Frozen audit code: `audit.py`; frozen controls: `test_audit.py`. Formal audit
  output goes only to a new, previously absent `AUDIT_RESULT.json`.

## D — Decision

Report `PASS_INDEPENDENT_AUDIT_SCOPED` only if source pins and raw payload
reconcile, every seed/arm/arrival is present exactly once, all regenerated data
and 655,360 held-out predictions independently reproduce their recorded
metrics, all routes/schedules/integrity assertions pass, the 95th percentile
is recomputed, and the frozen scientific decision is reproduced. The scientific
disposition remains HOLD if legacy mean exceeds 0.10; audit success cannot turn
that into a sampler-causality claim.

Report `FAIL_INDEPENDENT_AUDIT` for any contradiction in a complete, decodable
evidence bundle. Report `STOP_INPUT_PROVENANCE` if the frozen source or payload
cannot be byte-verified. Preserve the predecessor HOLD and all its files.

## C — Scope and constraints

This is a CPU-only audit of retained synthetic evidence. CUDA is hidden from the
audit process; no CUDA call, model training, optimizer step, new formal seed,
provider/network call, GUI, runtime-authority change, or predecessor edit is
allowed. Inputs are read-only. Only this additive directory is writable.
Container use is preferred when the exact required PyTorch runtime is already
available locally; do not pull images or install packages. The workstation's
existing Python 3.11.9 / PyTorch 2.5.1+cu121 runtime is used strictly on CPU if
no suitable cached container image exists.

## U — Limits

The raw bundle does not include every live tensor object or the optimizer's
internal state. The audit can independently recompute row-level predictions,
metrics, deterministic data/schedule identity and cross-record assertions; it
can only verify the recorded booleans/digests for full tensor snapshot/rollback,
not replay those tensor operations. This does not establish a real-task effect,
causal sampler explanation, generalization, runtime safety, or product value.
