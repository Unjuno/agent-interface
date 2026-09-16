# Safety-plane release receipt recovery — formal result

Task `SAFETY-PLANE-RECEIPT-RECOVERY-20260917-001`, Issue #816.

## Decision

**`PASS_SAFETY_RECEIPT_RECOVERY_SCOPED`**.

The frozen eight blocked-data first cases completed in two four-case outer dispatches, with no same-ID rerun, replacement, extension or tuning. Physical release semantics were fixed; only post-release receipt retention differed.

## Main discriminator

- `PIPE_ONLY`: ordinary nonblocking receipt write was blocked **4/4**; ordinary receipt absent **4/4**; no fabricated recovery **4/4**.
- `OWNER_LOCAL_JOURNAL`: the same ordinary write was blocked **4/4**, but one exact compact receipt was appended+fsynced owner-locally after verified key-up and recovered once after data-plane recovery **4/4**.
- App-observed F8 KeyPress/KeyRelease exactly one each **8/8**; owner physical release count one **8/8**; parent terminal F8 state up **8/8**.
- Verified-empty preceded ordinary data-plane recovery **8/8**, by 174.275..174.894 ms.
- Candidate journal work began only after verified physical release, by 0.005398..0.007331 ms.

Descriptive cancel-send -> release-injected latency was 0.107381 ms median for PIPE_ONLY and 0.098040 ms for OWNER_LOCAL_JOURNAL. This is not a hard-real-time or performance promotion gate. Recovered publication occurred after journal fsync and after the blocked data path recovered; journal-write -> recovered-publish was 308.039..361.897 ms.

## Integrity

- frozen audit decision: `PASS_SAFETY_RECEIPT_RECOVERY_SCOPED`, errors `[]`;
- frozen source rehash: **14/14 exact**, deterministic source archive exact;
- actual formal evidence corruptions rejected **8/8**;
- source-first remote freeze blobs: `FREEZE.json` `294497982d9bd06e38f61bf97cb79230ba88e8fb`, `source.tar.xz` `a10b77d71b89baf74b6d74c4335d4ab4667072ce`.

A separate worker's later #816 construction/freeze attempt explicitly stopped at formal 0/8 after recognizing this session's earlier ownership claim; none of that material is pooled.

## Boundary

This establishes only a local Linux/Xvfb/XTEST/Tk/pipe/filesystem pattern: physical safety release can remain independent of a blocked ordinary data path while compact post-release evidence is retained owner-locally for later read-only recovery. `fsync()` here is not power-loss proof, not distributed durability, and not a model/game/cross-platform/product claim. No shared runtime is changed by this evidence.
