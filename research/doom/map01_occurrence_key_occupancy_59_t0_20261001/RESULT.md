# First outcome — occurrence-key occupancy ledger

**Disposition: `PASS_METHOD_SCOPED`.** The frozen occurrence-identified implementation independently audited 4/4 valid finite cases and rejected 7/7 invalid cases. It returned one separate interval per stable ID for one, two, or three `W` occurrences in the same action/epoch; an interleaved `W/SPACE/W` case retained all three intervals even though different keys overlapped. Same-key occurrences whose timing brackets did not prove separation, missing or duplicate interval IDs, cross-action evidence, malformed timestamps, missing release acknowledgement, and non-empty terminal evidence all returned `UNKNOWN`.

The candidate ran once and exited 0. The raw-only auditor ran separately once and exited 0; it imports neither candidate nor occurrence ledger. Retries: 0. Raw SHA-256: `d5d13ffbcef09421170b5779aa3900ba18cf52725549c4f02f6e27c9ff044a4d`. The independent audit output and reconstructed intervals are retained in `results/t0-01/audit.json`.

## Interpretation for #59

This is a construction-level successor to the repeated-key boundary recorded in PR #6105. It demonstrates a concrete schema rule: `(action_id, epoch, interval_id)` identifies an occurrence; `key` may repeat; each occurrence gets its own conservative duration bound; ordering uncertainty fails closed. It does not show that the system's current input owner emits stable interval IDs or that XQueryKeymap can prove each interval's physical endpoints. A runtime integration must bind the ID at input admission and matching release and preserve independent keymap receipts before any live occupancy claim.

## Scope and environment

Eleven deterministic synthetic cases; CPython 3.12.10 on Windows, CPU-only. Docker Engine was not available at the bounded preflight; no container ran. No game, model, GUI, physical input, X11, WSL workload, task effect, safety or latency was measured. This does not close Issue #59 or establish a MAP01 outcome.

The frozen source and case hashes are in `FREEZE.json` and `SOURCE_HASHES.json`; raw results and independent audit are in `results/t0-01/`.
