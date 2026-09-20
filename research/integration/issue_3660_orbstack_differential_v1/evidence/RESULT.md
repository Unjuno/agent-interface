# Issue #3660 — allocation result

## Disposition

- Mutation-control gate: **PASS_MUTATION_CONTROLS** — nine altered copies were rejected, including re-sealed reorder, re-sealed extra event, input counts 2/4/bool, role identity mismatch, stale identity accepted, cleanup survivor, and runner booleans changed to all false.
- Raw reconstruction gate: **HOLD_AUDIT_EVIDENCE_INCOMPLETE** — zero structural integrity errors on the untouched raw, but three transition claims cannot be independently reconstructed from retained receipts.
- Predecessor formal outcome remains unchanged: `HOLD_TASK_EFFECT_UNTESTED`, one formal invocation, zero retries. This allocation did not launch apps or emit UI input.

## H/T/D/C/U

- **H:** An independent auditor can reject tampering and will HOLD—not infer PASS—when required raw receipts are missing.
- **T:** Exact frozen #3652 raw and predecessor auditor were downloaded by raw GitHub URL and hash-checked. Both replay and new audit/mutations ran in OrbStack with image `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f` (`linux/arm64`), `--network none`, `--read-only`, raw/source read-only, and only an output mount writable. No GUI/model/network calls or formal allocation.
- **D:** The independent audit requires exact 15-event ordered protocol, valid per-event hashes and sequence, exact integer input count 3, one invocation/no retries, role-to-window binding, transition field consistency, and reconciled cleanup. Missing evidence yields HOLD. Mutants must be rejected as `FAIL_AUDIT_INTEGRITY`.
- **C:** No changes to predecessor raw, source, report, or audit. Only copies of raw were mutated. The raw remains `HOLD_TASK_EFFECT_UNTESTED`; no inference about Agent Interface runtime or task effect.
- **U:** No evidence can be recovered for observations not captured in the historical session. This audit cannot decide whether the actual GUI behaved correctly at those missing points.

## Exact provenance

- Current main at experiment start: `c3abca57cb9d0e5cfea49794e35b33a84337959f`.
- Historical frozen runner source commit: `e8bd0f0dcb29dc194c1235f1f102db5e662dbed4`.
- Frozen result raw SHA-256 (literal bytes): `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883` (7,644 bytes).
- Predecessor readback source SHA-256: `11a01934d168a23aac208ce5bb2bff6ef1287c8ea683b77f9b76a652e8102ab4`.
- Replayed predecessor receipt SHA-256: `01b0e6e108328def4b64dbf9d7133094c13ea89b32ab0a576913ba6913cd04a1`; decision `PASS_POSTHOC_EVENT_RECOMPUTATION`.
- Independent reconstruction receipt SHA-256: `59237d8d04ce7e27dbde38312427c634296ca0ba35665b3f5596622d969d6d2d`.
- Final mutation receipt SHA-256 (includes direct predecessor-auditor differential replay): `c4af881baa48da3041d4a47a4bc9afc0d4fac5271792eac2e2e9b0941b8c095e`.
- Pinned image confirmed locally with `docker image inspect`: exact digest above, Linux/arm64.

The first container invocation used the image's empty entrypoint and attempted `python`, which is absent from PATH; no process started and no data changed. After read-only inspection confirmed `/usr/bin/python3`, the declared audit commands ran successfully. This is retained as a harness invocation correction, not a semantic failure or retry of a formal allocation.

The H/T/D/C/U and mutation scope were stated in the live task commentary before the new audit/mutation code was executed. `PREREGISTRATION.md` is the durable transcription, but was committed to the local experiment tree afterward; its file hash is not presented as proof of a pre-execution freeze. This provenance limitation is explicit.

## Differential mutation result against predecessor auditor

The exact retained predecessor `audit_readback.py` was run against each of the same ten JSON files (untouched plus nine mutations) inside the pinned container. It returned `PASS_POSTHOC_EVENT_RECOMPUTATION` for the untouched file and also incorrectly accepted five re-sealed mutations: event reorder, extra unknown event, and operation counts 2, 4, and boolean `true`. It rejected the other four mutants. The new auditor rejected all nine altered copies. This experimentally confirms the order/cardinality/input-accounting gap without claiming the historical raw itself was tampered with.

## Missing claim-level receipts

1. Modal: raw records an XID after Ctrl+O and repeats it after Escape, but no owner/parent identity proof or observation that the modal disappeared.
2. Chromium replacement: the numeric XID was reused and PID/generation changed; a `refused` disposition is recorded, but the raw does not show the generation-aware admission function being invoked with the old identity or an independently retained old-window disappearance receipt.
3. Calc return: `fresh_validation: true` is a runner-authored boolean; no fresh role resolver output or independently recorded active-window value is present.

## Integration handoff

The new code is standalone and imports no project runtime modules. Reproduce with the command in `README.md`. The exact predecessor bytes are retained under `evidence/`; all mutant inputs and their byte hashes are retained under `evidence/mutants/`. A subsequent GUI allocation, if desired, must be a new issue/allocation that captures the missing receipts; do not alter or replay #3652 formal-01.
