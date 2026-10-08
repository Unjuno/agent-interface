# Generation-scoped staged publication v2

Decision: **RETAIN scoped generation-gated publication candidate.** This is the separately frozen successor to Issue #271 v1, whose first allocation remains incomplete 14/16 because its worker incorrectly required every stopped predecessor to produce a stage. No v1 ID was rerun.

## Question

The prior producer-quiescence experiment showed that retry B can complete and then be overwritten by predecessor A unless B waits roughly for A to reap. This experiment changes the effect architecture rather than tuning that wait: A and B always write separate stage files. B becomes controller-current generation 2 immediately after A receives SIGTERM. B may publish its verified stage to a canonical path without waiting for A. When generation-1 A later completes, the only experimental factor is whether its completion is naively published or rejected as stale.

A missing A stage is explicitly `NO_EFFECT`, not a harness failure and not task success. Active processes are still reaped for final evidence; this gate controls publication, not cancellation.

## Frozen conditions

Publication base `82572e80f81e19fb7129218fb5af4386795d8d8d`; GitHub freeze commit `b2639fc114ec3fe3d4817477f237fb500566443a` precedes all measured cases. Eight paired blocks / sixteen first outcomes, alternating order. A SIGTERM at 800 ms. Native FFmpeg inputs and RGB identities are byte-identical to the prior race study. Each private xterm worker is started by a real XTEST Return; a separate X11 connection verifies down, release and final empty state.

The measured controller owns generation `{A:1,B:2}` and uses same-filesystem `os.replace` for eligible publication. This is an explicit capability/assumption, not inferred application semantics.

## First outcome

All sixteen cases completed once; no measured ID was rerun. A stage happened to exist in all sixteen, although v2 would retain an absent stage as `NO_EFFECT`.

| Publication rule | B published before A reap | Late A callback | Final canonical |
|---|---:|---|---:|
| naive | 8/8 | `PUBLISHED` 8/8 | **A 8/8** |
| generation gate | 8/8 | `STALE_GENERATION` 8/8 | **B 8/8** |

Every case independently verifies actual `B reaped < A reaped`, exact B/A stage identities, B canonical publication, and empty physical Return input. A exits 255 after SIGTERM and B exits 0.

From completed stop request, B canonical publication has median **68.781 ms** in naive and **71.096 ms** in the gate arm; all observed values are 68.354–120.018 ms. Paired gate-minus-naive median is 2.510 ms, range -0.957–51.261 ms. A reap median is 363.281/361.882 ms. These samples do **not** establish a general performance improvement or stable gate overhead; host scheduling is uncontrolled.

For context only, the prior separately frozen direct-path reap-gated study observed B reap median 478.764 ms. The current and prior studies differ in output architecture and batch, so their difference is descriptive rather than a matched causal speedup. The present result establishes that this candidate need not wait for predecessor reap before publishing B under this fixture.

## v1 failure retained

The predecessor v1 frozen allocation remains `INCOMPLETE_14_OF_16_HARNESS_ASSUMPTION`: `r3-naive` and `r5-generation_gate` had exact B publication and verified Return release but no A stage after A reap; the frozen worker stopped before finalization. Complete v1 cases were naive final A 7/7 and gate final B 7/7. V2 changes only the handling of predecessor-stage absence. It does not relabel v1.

## Verification

The frozen v2 auditor passes 16/16 and independently decodes PNG bytes with stdlib CRC/unfilter logic. Three prefreeze contract tests passed. Five post-hoc retained-evidence mutation tests plus unchanged control pass; these are verification only and are not part of the frozen decision gate. Separate extraction verifies 471 manifest entries, reproduces the result byte-identically and passes all 8 current tests.

Raw evidence archive: `staged_promotion_evidence.tar.xz`, 131200 bytes, SHA-256 `88ed2d6df735868c36ae597ac5f6622489a936d831b198a9a7afb73449649b6a`, retained in the originating conversation rather than byte-completely in GitHub. User ZIP SHA-256 is `b3ac5ffa8d04813f61b7d10c2e0dbf2a49264450e077dd8da8e61f8919374d95`.

## Interpretation

The experiment distinguishes *attempt completion* from *publication authority*. Unique stages prevent attempts from writing the canonical target directly; generation identity prevents a stale completion from being promoted. Under the tested local single-controller model this avoids the observed same-target predecessor overwrite without delaying B publication until A reap.

This mechanism is not equivalent to rollback or exactly-once. The generation counter is controller-owned but not durably recovered here. `os.replace` atomicity is same-filesystem local namespace behavior; directory durability under power loss is untested. Descendants, external services, multiple independent publishers, malicious generation claims, and non-stageable effects remain outside scope. The outbox/idempotency studies address different boundaries.

## H / T / D / C / U

**H:** unique staging plus current-generation publication prevents stale predecessor publication while allowing B publication before predecessor reap.

**T:** 8 paired real-XTEST blocks, native FFmpeg, exact source/fixture hashes frozen before measurement; only publication eligibility differs.

**D:** scoped PASS: naive final A 8/8; generation gate final B 8/8; actual B-reap-before-A-reap 16/16; release/integrity gates pass.

**C:** unique namespace isolation plus a trusted single publisher, not generation metadata alone, is essential. File locks, transactional storage or external idempotency may be preferable elsewhere.

**U:** one host, one FFmpeg pair/path, n=8/arm, unpinned host scheduling; no crash/restart/power-loss or multi-writer experiment. No calibrated population confidence or hard-real-time bound.
