# Issue #8622 T0 A02 — three-arm common-cause degradation comparison

**Fixture/auditor result:** `PASS_METHOD_SCOPED`.  
**Evidence-custody disposition:** `HOLD_RESULT_CUSTODY`; do not promote the result pending a separately authorized successor.

The frozen independence-assuming lookup, dependency-aware contract, and unknown-dependency fail-closed policy were each evaluated in the one candidate process, and the independent raw-spec auditor exited 0 after reconstructing all ten cases. Its result was PASS: the independence arm admitted six unsupported operations across four cases; the dependency-aware arm had zero unsupported operations and preserved supported raw-only outcomes under shared semantic failures; the unknown-dependency fail-closed arm admitted zero operations in its one unknown-dependency case; mandatory release-obligation labels were present in 10/10 cases; dispatches were zero. Six semantic mutations were rejected by the 3/3 in-memory construction tests.

The formal candidate and auditor each ran once, with zero retries, on CPython 3.12.10 / Windows 11 AMD64. Candidate stdout (12,546 bytes) was passed directly in memory to the auditor; auditor stdout was 4,116 bytes. No output files or temporary files were written, and no Docker/WSLc command was issued.

## Custody qualification

The outer runner computed both stdout SHA-256 digests and emitted a compact formal record, but the terminal-rendered output wrapped/truncated that record before both full digest strings could be recovered. The raw streams were memory-only and are no longer available. This PR records the byte counts and the auditor's structured metrics, but intentionally records both exact stdout digests as null. No digest is reconstructed or guessed, and the formal candidate/auditor are not rerun. Thus the fixture/audit criteria pass, while exact-output custody remains on HOLD.

## Scope

This is a deterministic, hand-authored finite method fixture. It does not validate any production dependency graph or establish a real failure rate, runtime reliability, human benefit, latency, deployed safety, resource enforcement, or product readiness. WSLc remains gated by shared ownership HOLD in #7924; host execution here required no container boundary. Earlier #8610 A01's distinct `HOLD_PROTOCOL_ARM_MISMATCH` remains unchanged. See [PROTOCOL.md](PROTOCOL.md), [FREEZE.json](FREEZE.json), [CONSTRUCTION.json](CONSTRUCTION.json), and [RUN.json](RUN.json).
