# Multi-channel ascertainment fixture — Issue #5826 A01

**Result: `PASS_METHOD_SCOPED_HOST`; `HOLD_CONTAINER_TRANSFER`.** The oracle-known fixture surfaced an all-channel blind spot and showed that two-list capture–recapture can materially undercount even in this small known frame. This does not estimate live incidents or qualify the Issue's requested container T0.

## Frozen fixture and observed data

The frame contains 18 opportunities: 12 oracle-labelled faults (two each across all six frozen classes) and six no-fault controls. Four ordinary channels each retain one row per opportunity: runtime reject log, event watcher, effect verifier, and post-effect audit. Candidate consumed only [`fixture.json`](fixture.json); the oracle remained in separate auditor-only [`ORACLE.json`](ORACLE.json).

There were 72/72 channel rows with unique opportunity/channel pairs. The union detected 9/12 faults (75%); F02, F04, and F08 were missed by all four channels. Runtime uniquely detected F10; post-effect audit uniquely detected F03, F06, and F12. Runtime also generated one false report on N16. Verifier UNKNOWN on N18 remained UNKNOWN and was not silently counted as a clean result.

Runtime and Watcher share the declared `shared-capture-stream` source group. Their raw report counts are n1=5, n2=3, overlap=2, producing naive two-list estimate 7.5 and Chapman diagnostic 7.0, both below the oracle-known 12 faults. Even after oracle-only removal of the one known false report, the diagnostic would remain 6 vs 12; that is a retrospective fixture comparison, not a deployable estimator. The all-channel miss and estimates are completely enumerable here because truth is known; no unseen production count is inferred.

The fault schedule deliberately includes stale observation as a fault class: a stale observation can remain invisible to an effect-only audit when it causes no downstream difference, illustrating a plausible coverage blind spot. Dependence is specified by the fixture's source groups/alert edges; it is not estimated from this small sample.

## Audit and mutation controls

Independent auditor reconstructed the full table and oracle joins, counts, source IDs, timestamps, delay, linkage, alert edges, UNKNOWN and estimator arithmetic. Five corruption controls were rejected: omitted row, duplicate row, mislinked event, UNKNOWN→negative conversion, and oracle truth flip. Raw candidate data is [`candidate.json`](candidate.json); exact invocation output is in [`EXECUTION.txt`](EXECUTION.txt).

## Environment deviation and limits

The specified container attempt was not possible: Docker/OrbStack `ps` and image inventory failed on an unreadable containerd blob (`operation not supported`). No image was pulled and no container started. Candidate ran once on macOS 27.0.0 arm64 with bundled CPython 3.12.14. Thus the method gate is only a host-process result; container transfer is HOLD.

This proves no live incident rate, channel sensitivity, task safety, or production hidden-failure count. The oracle is synthetic and independent by construction; record linkage is a known opportunity ID. See [`FREEZE.md`](FREEZE.md), the candidate/auditor sources, and [`SHA256SUMS.txt`](SHA256SUMS.txt). Issue #5826 remains open.
