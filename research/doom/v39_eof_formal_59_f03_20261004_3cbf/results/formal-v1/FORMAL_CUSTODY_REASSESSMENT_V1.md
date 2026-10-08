# F03 custody-gate reassessment — v1

Status: **preserve the observed four-cell result; qualify its custody assurance. Do not repeat the consumed producer or auditor.** This addendum does not alter the original raw output or `FORMAL_RESULT_V1.md`.

## Trigger

Issue [#59 comment 5975510655](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5975510655) reports a negative control against the frozen v6 `native-entry-template.sh`: the mounted eight-file fixture and its manifest were changed together while the archive remained unchanged. The entry gate accepted the altered manifest rows and executed a harmless sentinel (exit 23). This establishes that the gate does not fail closed when a mutable mounted fixture and manifest are jointly replaced.

## Reconciliation with this already-consumed run

Read-only checks performed for this reassessment:

- Reconstructed the eight-file tar from frozen commit `0f8700502ef5778fb2b3f5a37123d5b983422c5a`; its SHA-256 is the frozen `8c04363ba608fd97b79f6a206ab0b7be51ad8098a92e130b53b7ece5f4c961c5`.
- Compared each of the eight `input_sha256` rows printed by the native entry to the frozen `methods/input.SHA256`: exact match.
- Repeated that comparison for the auditor entry: exact match.
- The retained immediate prelaunch record also reports matching host/guest archive SHA, entry-script SHA, and manifest SHA; the native/auditor stdout independently reports the expected archive SHA and eight expected member hashes.

These records support that the bytes checked at each entry matched the frozen inputs. They do **not** prove an atomic binding between the checked files and the subsequent `exec`: the separate source mount remained host-mutable, and the negative control shows the wrapper can accept a jointly substituted fixture/manifest. No evidence found in the retained run shows that substitution occurred, but the gate alone cannot rule out a change between validation and execution. Therefore retain the raw four-cell observations and auditor verdict as historical, scoped results; do not describe the v6 entry gate as tamper-resistant or use this run as proof of fail-closed custody under concurrent mutation.

## Disposition and restart condition

- No producer or auditor rerun is authorized by this reassessment. The original outputs, receipts, failed negative control, and predecessor report remain unchanged.
- Any future launch using this entry pattern is **HOLD** until a versioned correction pins the manifest digest inside the entry boundary and executes from a private snapshot whose bytes are verified against the pinned archive. Add a negative control that jointly mutates fixture and manifest and assert STOP before runner execution; retain its command, output, and independent audit.
- A repaired gate requires a fresh review and a newly versioned allocation. It must not relabel or overwrite this v1 result.

## H/T/D/C/U

- **H:** The retained v1 stdout hashes match the frozen eight source members, while the entry design remains vulnerable to a jointly changed mounted fixture/manifest.
- **T:** Read-only reconstruction and comparison of the frozen archive plus the retained native/auditor entry receipts; no container, producer, auditor, model, GUI, or game was run in this reassessment.
- **D:** Frozen commit/tree and archive digest, frozen manifest, retained prelaunch record, and both retained entry stdout logs.
- **C:** Existing retained Linux/arm64 run receipts only; this reassessment ran locally against immutable Git objects and saved text. It does not add runtime evidence.
- **U:** The TOCTOU interval cannot be ruled out from these receipts; fail-closed behavior under mutable-host interference is disproven by the reported negative control. The pipe result remains narrow and does not establish GUI, gameplay, controller, latency, safety, or production behavior.
