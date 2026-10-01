# X-server release-confirmation generation binding result

Decision: **PASS_RELEASE_CONFIRMATION_GENERATION_BINDING_SCOPED**.

Frozen task `XSERVER-RELEASE-CONFIRMATION-GENERATION-20260918-001` executed one primary construction invocation over 250,000 seeded traces / 1,075,477 event transitions; reruns0.

- candidate/oracle mismatches: 0
- retro-confirmation escapes: 0
- valid same-generation confirmations: 7,375
- malformed traces failing closed: 14,315
- authority grants: 0
- task-input grants: 0
- primary digest: `3700c1f5d2d4db3d33403e85b14925b6bae1409e94ab8ed0864b9075ead5afb0`
- independent audit: PASS, errors `[]`
- copied-result corruption controls: 4/4 rejected
- post-result frozen science-source rehash: all matched

Scoped conclusion: after cleanup has become `RELEASE_UNCONFIRMED_BACKEND_LOST`, later observations from another X-server generation cannot truthfully retro-confirm that old cleanup. Confirmation must remain bound to the same server generation and cleanup-attempt lineage. This is receipt-lifecycle semantics only; it does not establish real restart/reconnect behavior, physical-device cleanup, host-crash safety, or a production generation-token API.
