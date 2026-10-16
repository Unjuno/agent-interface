# #5156 key-identity audit correction — T0 plan

## Question and H/T/D/C/U

**H.** The retained v2 independent completeness auditor fails open on the logical `key` field: because `key` is absent from its identity tuple, changing a raw explicit-release key or autonomous-cleanup key can leave its result at `errors=[]`. A separately frozen inventory-key comparison should accept the pristine retained joined trace and reject corruption, omission, and type substitution for both release classes.

**T.** This is a bounded, CPU-only audit-integrity experiment over immutable synthetic evidence; it does not execute the owner, X11, or a container allocation. Pin current main at intake, the exact PR #5415 v2 auditor blob, and PR #5467's retained expected inventory, owner source rows, and joined raw bytes. First replay the original auditor on pristine and single-field mutated copies to reproduce the reported false-accept. Then use a new read-only auditor that independently checks exact inventory-to-record key equality by unique `release_id`, including string-only explicit keys and null-only autonomous cleanup keys. Freeze the candidate, runner, test vectors, and source hashes before execution. Execute one deterministic candidate runner, retain its full raw decisions, and invoke a distinct raw-only audit process once on that exact output. Do not rerun any source producer or owner runner.

Directed mutations: explicit key changed to another string; explicit key changed to null; cleanup null changed to a string; cleanup null changed to boolean false; key field omitted; wrong release identity; duplicate/removed row. Include expected-inventory contract mutations (explicit null key and non-null cleanup key) as verifier controls. The original v2 decision is retained as a comparator and is never edited.

**D.** `PASS_KEY_IDENTITY_AUDIT_T0_SYNTHETIC_ONLY` requires: upstream v2 accepts the exact pristine retained trace and false-accepts the preregistered key mutations; the candidate audit accepts pristine and rejects every frozen key/identity/cardinality mutation; the separately executed raw-only auditor agrees with the runner's complete decision object; all source hashes match; all focused tests pass; and terminal JSON records preserve the original bytes and hashes. Any missed directed mutation is `FAIL_AUDIT_FALSE_ACCEPT`; input/hash/process/audit mismatch is `STOP_INTEGRITY`.

**C.** One fixed three-row synthetic joined trace (two repeated explicit releases of key `a`, one autonomous cleanup with key `null`), CPython standard library, deterministic mutation matrix. The upstream auditor and candidate run in separate processes for the final audit; tests share the same interpreter as the test runner only.

**U.** This only tests copied-evidence audit integrity for one frozen synthetic trace. It does not verify producer authenticity, owner emission completeness in a live runtime, caller nesting, X11/server/physical key state, occupancy, task effect, MAP01 behavior, recovery efficacy, or safety. No formal #5156 X11 allocation is consumed; no Docker/OrbStack, GUI, game, model, GPU, network experiment, or input is used.

## Frozen intake

- GitHub `refs/heads/main` at freeze preparation: `55c467786b3b98e5f8d1746f9c2970b7ada8b47c` (fast-forwarded before any experiment execution).
- PR #5415 head: `2b01248ff319a70ca7ddb19131f2f6cc4d7a2360`.
- PR #5467 head: `1675b2e3b3deb4ffbd2651098ccfc819aa53d123`.
- Upstream v2 auditor Git blob: `c37b6372f4e5a7306b98049c834559fdd60cadee`.
- Expected inventory Git blob: `affa71e53457bb903353ce67b3477ef20b1d488c`.
- Owner rows Git blob: `0ba30b5f30d57045af4ca54c3eec9893fa1bce05`.
- Joined raw Git blob: `451247a5180348b8c29d09994dc0264f822585d1`.

Exact repository paths and frozen object identities are repeated in `FREEZE.json`. The inputs will be copied byte-for-byte from those pinned public blobs into this additive evidence directory. No file in either predecessor PR is modified.

## Execution order

1. Verify current-main and source object identities; materialize the exact upstream auditor and three input blobs.
2. Add only the new key-identity auditor, deterministic runner, tests, and separate auditor. Record their SHA-256 values in `FREEZE.json` before running them.
3. Run focused unit/mutation tests once; run the experiment runner once; if and only if it exits zero, invoke the separate raw-only audit once.
4. Recompute all frozen input/source/output hashes, run syntax and diff checks, and preserve the full command/exit record.
5. Record the scoped outcome in Issue #5156 / PR evidence. Do not merge without required review and exact-head checks.
