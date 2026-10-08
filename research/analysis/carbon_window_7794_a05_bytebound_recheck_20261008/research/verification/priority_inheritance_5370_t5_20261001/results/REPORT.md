# Issue #5370 — blocked-waiter deadline-ordering rung (STOP)

This is a separate preregistered waiter-order experiment. It is **not** the claim-binding experiment reported as T5 in merged PR #5568; do not conflate their hypotheses, allocations, or outcomes.

## Outcome

The candidate runner was invoked once and exited 0, producing seven rows. The frozen independent audit-v1 was invoked once against the retained raw and exited 1 with three errors. Disposition: **STOP_AUDIT_V1_FAILURE_NO_ACCEPTED_RESULT**. The output is uncertified; this bundle does not claim the registered PASS or an accepted scientific FAIL. No retry or v2 audit was performed.

Exact stdout bytes (UTF-8, including terminal CRLF) are retained in `results/RAW.json` and `results/AUDIT-01.json`; their SHA-256 hashes are in `SHA256SUMS.txt`. Read-only inspection suggests the frozen auditor's empty-set expectation and schedule reconstruction may be defective, but that diagnosis is unverified and is not a substitute audit.

## Freeze and provenance

- Execution branch/path: `research/priority-inheritance-t5-5370-20261001` / `research/verification/priority_inheritance_5370_t5_20261001/`
- Frozen main: `1b561c2978f020ff784480880ac8e7c908ddadfe`
- Publication branch starts at current main: `bde4e1d8a3bedfa16aefbb993a816fb3b0f65c92`
- Freeze SHA-256: `1fd2784cbb1346302a83fe038a1886a024cf6340ba46cb445a09832ae84b75a7`
- Runner SHA-256: `544072bff7db6441a30052d883d7bee69bb696379a2578e28249cc9232f764e5`
- Frozen auditor-v1 SHA-256: `e680c93939049cca2204fc8dac73273262f510335a71ef1e0566250001c9140a`
- Construction suite: 4/4 passed before freeze; not repeated.
- Host: CPython 3.11.9 CPU. No GPU or container was used. The synthetic runner has no repository source dependency.

A later audit-only successor may inspect this exact raw, but must be separately frozen and must leave this runner, raw, auditor-v1, and STOP unchanged.
