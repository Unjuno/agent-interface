# A12 post-run disposition: STOP_AUDIT_CONTRACT_MISMATCH

Run ID: a12-two-key-dual-release-loss-20261008
Pre-run source/candidate freeze: commit 16b7ebae6ee8f706d89b178f487b9ee04f1c920f
Runner addendum: commit f1255818bd4a79435d5ad82e1ed49222748225f7
Candidate SHA-256: bc69c79cdcaee1e1a95c0e3cbbabe10afd4344b3661f3905c1b2e6142759a535
Source-manifest SHA-256: bf7b2d911854cb6fdaabedabdb853bb2fc3bffd5049b3f4c8e5b3c1355a4222a

## First outcome

The frozen candidate was invoked once with the normal arm and the two-key treatment. It produced captured candidate JSON in memory. The source-manifest verifier passed all 21 source blobs. Semantic audit returned FAIL only for case1_shared_sample; its baseline therefore failed, while all six mutation cases were rejected as intended. The audit exception occurred before raw JSON or audit output was committed. Host storage was not writable, and the candidate JSON is not recoverable from the process output. No candidate retry is authorized by this record.

This is an auditor-contract STOP, not a candidate or production failure. Do not promote the missing raw output or claim PASS.

## Why the equality predicate was invalid

In the frozen input_owner_v12.py at source commit 712a71b, release_keys_batch takes the shared post-batch keymap sample at lines 194–201. It then iterates keys at lines 203 onward. For each key it assigns the current sampled_ns to that key's initial attempt at lines 208–210. If that key remains down, the retry loop takes a new keymap sample and overwrites bitmap and sampled_ns at lines 211–231. A later key is then evaluated against those updated values. Thus, when an earlier key retries, the later key's attempt-1 receipt can carry the later retry sample rather than the original shared post-batch timestamp.

The frozen input_transition_owner_v4.py validates each receipt's own KeyRelease/XSync/sample order and ordered attempt chain (lines 52–74); it does not require timestamps to be equal across distinct key receipts. The A12 auditor's cross-key equality condition was too strong for this sequential retry behavior. The condition should not be used to infer a runtime defect.

## Scope and retained disposition

- Candidate treatment: both original KeyReleases were configured to be dropped once in the fake-X server; no real X server, game, model, GUI, physical keyboard, or OS input ran.
- The one candidate invocation and its exact raw JSON were not persisted. Only process-level audit status and immutable source/candidate identities remain.
- Result: STOP_AUDIT_CONTRACT_MISMATCH; no PASS or candidate FAIL claim.
- Issue #59 remains open and unassigned. This does not satisfy its live threat-exposure, useful-feedback, bounded-recovery, per-key live-release, or MAP01 outcome gate.
- Preserve the pre-run freeze and this STOP record. Any future experiment must have a corrected independent auditor frozen before invocation, a writable retained-output destination, and a genuinely distinct question or input condition.
