# T0 A01 protocol — Issue #8040

## H — hypothesis
For a finite three-operation semantic procedure, a hash-bound macro map plus current, operation-bound independent effect receipts can reconstruct the generic continuation at every declared safepoint. It skips only VERIFIED prefix effects, never replays or continues through UNKNOWN, never extends authority, and never reports task success because the specialized program ended. At least one verified-prefix case yields a correct cursor later than unconditional stop.

## T — smallest test
Model semantic operations `prepare_record`, `commit_record`, and `send_receipt`. The specialized sequence includes boundaries after operations and inside one-to-many lowerings. Enumerate a fixed set of initial, verified, known-NO_EFFECT, UNKNOWN, stale-generation, missing/wrong-map, malformed-evidence, and end-of-program cases. The public candidate receives only the macro mapping and typed receipt records; audit truth is in a separate sidecar. It preserves a VERIFIED prefix in the evidence ledger when a later effect is UNKNOWN or partially lowered, but withholds the generic cursor and emits no action. Compare with an independent raw-only reconstruction. Run construction tests before freeze, then one formal candidate CLI and one separate auditor CLI, sequentially, with no retry.

The OrbStack attempt is preserved as a pre-formal environment STOP: exact read-only image inspect returned `operation not supported` for a containerd content blob. Since this finite deterministic method has no environment-dependent behavior or external I/O, A01 is explicitly a native-host substitution (`nice -n 10`, one sequential process), not a container result. Host resource limitations and absence of OS isolation are recorded; no daemon/image/container mutation is allowed in this allocation.

## D — decision
`PASS_METHOD_SCOPED` only if the independent auditor reconstructs every frozen row; all output mutations are rejected; candidate never returns an executable action or authority; UNKNOWN, stale state, invalid maps, and partial lowering yield; NO_EFFECT points at the still-pending operation without authorizing execution; VERIFIED prefixes produce the correct generic cursor; and end-of-procedure is explicitly not task completion. Any false cursor, skipped non-VERIFIED operation, replay/continuation through UNKNOWN, authority extension, or false completion is `FAIL_METHOD`. Incomplete source/runner identity or any pre-formal source change is `STOP`, not a retry.

## C — competing explanation
Full stop/yield may be the preferable general policy because real effect receipts and maps can be incomplete; a generic fallback may suffice before any visible side effect. A positive finite fixture only shows that a correct abstract map can preserve a continuation boundary when its inputs satisfy the contract.

## U — uncertainty
This authored finite model does not establish map completeness, cryptographic or operational receipt authenticity, real GUI effect adjudication, dynamic interruption behavior, authority safety, task success, latency, model/human behavior, or production value. The candidate treats the typed independent receipt classification as an input contract; the raw-only auditor checks it against hidden fixture truth. Host execution has no container or OS-enforced resource/network isolation.

## Frozen environment and commands
- Intended container preflight: OrbStack image inspect failed as recorded in `preflight.json`; no pull/create/start.
- Actual A01 environment: macOS arm64 / CPython version in `FROZEN.json`; one low-priority sequential native-host process, no network calls by the code, no OS isolation.
- Construction: normal and optimized unittest suites, `py_compile`, deterministic fixture generation.
- Formal: exactly `nice -n 10 python3 -B run_formal.py`; candidate CLI at most once and auditor CLI once only if candidate exits 0. Exclusive marker and zero-retry policy. Do not rerun.

## Construction repair history
The first construction suite ran 7 tests: 5 passed and 2 failed because the auditor's `change_cursor` mutation selected a valid cursor-0 row and therefore did not change its value. Independent row reconstruction itself had zero disagreements. This is a construction/mutation-fixture defect, not a formal allocation. The repaired mutation targets a valid row with a positive cursor; its result is recorded in the construction logs.
