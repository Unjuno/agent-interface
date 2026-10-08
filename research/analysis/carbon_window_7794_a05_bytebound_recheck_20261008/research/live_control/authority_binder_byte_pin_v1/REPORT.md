# Identity binder byte pin v1

Task: `O3-AUTHORITY-BINDER-BYTE-PIN-FIX-20260916-008`  
Issue: #209  
Immutable base: `7bea48e69cfb62b2993e7d7ea18a1688d527b70b`

## H

#203 encoded the correct call order, and #208 then showed a restart counterexample because only receipt-validator bytes were durably pinned. The minimum successor tested here is an independent byte pin for the identity binder, without changing the retained binder, validator, or durable-token semantics.

The candidate reads binder source once, hashes those exact bytes, compiles/executes the same in-memory bytes, persists strict binder metadata before inner validator/token-state initialization, and requires the exact binder identity on every reopen.

## Frozen sources

- candidate `binder_byte_pinned_bound_issue_v1.py`: SHA-256 `c725ca222920acf7dde9e5e0950a7178da92dbac41b49f65452acd0939241060`
- separate-process worker: `0cdc84b6089779096b51d0e983be9cf724bb9640d13b7b48aa7bce39b3cb8fee`
- formal runner: `54596e8a8412321f473696626bfd114592126cee2ef412e1c41642772f663243`
- retained identity binder: `a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730`
- #208 diagnostic drift binder: `e75b6851f37525e6230cde448392a248edf78d10c3e38dc2aeba4a518384ad26`
- byte-bound validator ledger v3: `a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5`
- bridge-v2 semantic validator: `f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9`
- durable token state v2: `72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4`

Candidate, worker, and formal runner were committed before formal execution.

## T / first outcome

Result ID: `authority-binder-byte-pin-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **8/8 PASS**  
Decision: **`RETAIN_BINDER_BYTE_PIN_V1`**

1. Exact-binder initialization persisted the expected binder SHA and issued only `runtime-intent-token` at sequence 11.
2. Replacing the binder source file after construction did not alter the already-loaded binder; the forged caller ID still failed with `caller authority_end_id mismatch` and token state was unchanged.
3. A fresh process under the drifted binder source failed closed with `binder pin mismatch`; existing token state and both sidecars were unchanged.
4. Restoring the exact binder bytes allowed a fresh process to reopen and recover the pending runtime token.
5. An injected crash immediately after binder-sidecar durability left no token state and no validator sidecar; retry with exact binder bytes initialized and issued normally.
6. The same binder-sidecar crash followed by drifted binder bytes failed at the binder pin before validator/token-state creation.
7. Deleting the binder sidecar from an existing token state caused a fresh process to fail closed with `existing token state missing binder pin`; retained token state and validator pin were unchanged.
8. The existing durable issue `after_replace_fsync` crash behavior remained intact: the caller saw an injected crash, but a fresh process recovered the durably pending runtime token.

Formal-result SHA-256: `1601b4054fd7396268f4aed802bcff7a9f7eea65ab23efa0ad50c3c2be090bc9`. Independent audit: PASS with zero errors.

## D

Retain the independent binder byte pin. It closes the exact #208 restart-drift counterexample while preserving the existing validator byte pin and durable-token crash semantics.

The retained project-facing order is now:

`load + byte-pin runtime identity binder -> bind runtime identity -> byte-pinned receipt validation -> durable token issue`

No composite manifest is justified merely because two sidecars exist. A composite representation should only be added if a concrete split-sidecar crash or version-association counterexample survives the current fail-closed initialization rules.

## C

This mechanism proves binder provenance consistency across restart, not semantic approval of whichever binder is first initialized. A deployment that initializes with the wrong but internally valid binder can consistently pin the wrong policy. Choosing/authorizing the allowed binder identity remains a separate configuration or trust-root question.

Binder and validator identities are also persisted in separate sidecars. This experiment covered binder-sidecar crash windows and delegated durable-token crash behavior, but it did not exhaust every possible two-sidecar corruption or association attack.

## U

Offline separate-process evidence only. No live GUI, model, network, durable-submit, or external exactly-once claim. PR #168 executed-source provenance remains independently unresolved and still blocks the downstream live crash-after-send allocation.
