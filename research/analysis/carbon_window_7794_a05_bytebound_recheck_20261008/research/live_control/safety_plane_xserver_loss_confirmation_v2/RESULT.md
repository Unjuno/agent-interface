# X-server loss confirmation A2 result

Decision: **PASS_BACKEND_LOSS_CONFIRMATION_FAIL_CLOSED_SCOPED**.

Frozen task `SAFETY-PLANE-XSERVER-LOSS-CONFIRMATION-20260917-002` executed all 8 fresh cases exactly once from freeze HEAD `4807d1ec8cd19da0d7b18214ad24e9cef61b1e70`. Same-ID reruns, replacements and post-output tuning were 0.

- `SERVER_RUNNING`: 4/4 `RELEASE_CONFIRMED`, `verified_empty=true`, one application press/release lifecycle, terminal key-up.
- `SERVER_SIGKILL`: 4/4 `RELEASE_UNCONFIRMED_BACKEND_LOST`, `verified_empty=false`, `DisplayConnectionError`, application press only, terminal X key state unavailable. False release confirmations: 0/4.
- Frozen audit: 8 rows, errors `[]`.
- Mutation controls rejected 3/3: false confirmation, authority escalation, invented post-loss terminal neutrality.
- Postformal source rehash: 10/10 frozen scientific/runtime files exact. The non-self-referential manifest repair therefore closes A1's metadata-integrity defect without changing science/runtime bytes.
- Frozen source archive: 14,092 bytes, SHA-256 `58da91d59a10495cd2660def704f7069b66d1baa8a9cb9ac294953864116538a`.
- Raw normalized results SHA-256: `a12fa71508d1736a5f2becfa7bcc12190f906e7fe31479ff90725d62bf8b81d9`.

Scope: private Linux Xvfb/XTEST/Tk process-loss fixture only. This establishes the epistemic fail-closed rule at this scope: after the backend capable of confirming release is lost, cleanup remains explicitly unconfirmed instead of inferring neutrality. It does not establish physical-device cleanup, host-crash safety, cross-platform behavior or hard real-time guarantees.
