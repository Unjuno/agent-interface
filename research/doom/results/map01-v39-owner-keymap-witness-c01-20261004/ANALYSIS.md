# Post-run analysis

Allocation `MAP01-V39-OWNER-KEYMAP-WITNESS-C01-20261004-01` completed one candidate invocation and one independent audit. Preserve `candidate.started.json`, `candidate.raw.json`, and `audit.json` as the original outcome; do not edit or rerun this frozen allocation.

The candidate failed at the first `backend.raw("w", True)` with `ValueError("another intent owns input")`. The Xvfb server started, the v10 owner cleanup record verified no held key or button, and Xvfb exited with code 0 during cleanup. The candidate did not complete its protocol, so there are no occurrence witnesses or transition telemetry receipts to interpret.

Diagnosis from the frozen source: `doom_typed_release_backend_v3.Backend.raw(key, False)` calls the transition wrapper's `InputOwner.call("up", lease, key)`. `input_owner_v10` removes that key from `held`, but leaves the lease in the owner's `active` slot until an explicit `release` operation. The real executor lifecycle supplies that owner release boundary; this isolated harness invoked `raw()` directly and omitted it. The second newly-created lease therefore hit the guard `active is not None and active is not lease` on key-down. This is a harness lifecycle omission, not evidence that the input key failed to release: owner cleanup reports an empty key set.

The audit correctly returned `FAIL_OR_HOLD_V39_KEYMAP_WITNESS`. Frozen source hashes matched, and the start receipt/environment binding passed. Other audit predicates failed because the candidate record was incomplete and did not contain the protocol's two occurrences. This outcome does not establish physical input, application effect, feedback onset, bounded recovery, latency, task effect, safety, or threat exposure.

A future distinct construction allocation would need to reproduce the actual executor boundary after each key-up (or exercise `Backend.execute()` with the real step path), use new source/freeze/output identities, and retain a no-retry rule. Do not reinterpret this candidate as a pass or rerun it under the same allocation ID.
