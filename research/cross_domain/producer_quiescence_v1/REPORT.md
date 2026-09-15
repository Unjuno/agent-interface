# Producer quiescence before same-target retry

Decision: **RETAIN scoped reap-before-retry gate for this local single-producer path.** Issue #253. Publication base `87c50f9492e88421584dd1832195d828ea1d35e5`; premeasurement GitHub freeze commits `92a3e00d...`, `b11ae7a1...`, and exact-plan byte alignment `38175c42...` precede every measured case. No shared runtime, workflow or historical result is modified.

## Question

Prior native FFmpeg evidence showed that SIGTERM can be followed by a real output effect. This experiment asks the next smaller question: if a retry B targets the **same output path** before predecessor A has actually reaped, can A overwrite B after B already completed? The comparison changes only retry admission time:

- `immediate`: start B immediately after sending SIGTERM to A;
- `wait_reap`: wait until A has reaped, then start identical B.

Both use the same A source, B source, output path, signal time (800 ms), binaries and output predicate. The worker is launched by one real XTEST Return inside private xterm/Xvfb; a separate X11 connection verifies physical Return down and empty release. This is not production Executor/InputOwner integration.

## Development evidence excluded from formal estimates

A direct-subprocess calibration first found final A in 4/5 immediate retries and final B in 5/5 reap-gated retries. One coding failure occurred before starting FFmpeg because a `Path + str` expression was invalid. A subsequent two-case real-XTEST preflight reproduced immediate `B -> A` and gated `B -> B`. These are retained but excluded. The formal source and fixtures were not changed afterward.

## Frozen measured result

Eight paired blocks, 16 first outcomes, alternating arm order. No measured ID was rerun.

| Arm | B exact immediately after B reap | Final B | Final A (late predecessor overwrite) |
|---|---:|---:|---:|
| Immediate retry | 8/8 | 2/8 | **6/8** |
| Wait for predecessor reap | 8/8 | **8/8** | 0/8 |

The direct discriminator is not merely the final file: in every immediate case B had already reaped and `after_b.png` independently decodes to B. In six cases the later final snapshot decodes to A. Thus the new correct result was visible and complete before being replaced by the old producer.

Immediate final B in two cases does not make stop-request retry safe; it demonstrates scheduling dependence. These are repeated known-fixture trials, not independent estimates of a general overwrite probability.

All A processes returned 255 after SIGTERM and all B processes returned 0. All 16 XTEST starts recorded physical Return down and verified empty release/final input.

## Timing trade-off

From completed SIGTERM request:

- immediate A reap: median **382.721 ms**, range 282.821-386.209;
- immediate B reap: median **114.280 ms**, range 64.293-117.055;
- gated B reap: median **478.764 ms**, range 428.668-528.711.

Within paired blocks, waiting for predecessor reap delays B completion by median **364.552 ms**, range 362.086-414.442. This is a correctness/latency trade-off, not a speed improvement. Timing uses same-host `perf_counter_ns`; observed ranges are not hard-real-time bounds.

## Interpretation

A stop request is a request, not quiescence. A successful retry receipt is also insufficient when the old producer can still write the same target. Under this fixture, waiting for the tracked predecessor process to reap creates a sufficient local sequencing boundary before same-target retry.

The general interface implication is to distinguish at least:

1. cancellation/stop **requested**;
2. producer **quiescent** under the relevant effect scope;
3. retry admitted;
4. retry effect verified.

Quiescence is scoped evidence, not a synonym for rollback. Reaping one local process does not prove that descendants, asynchronous kernel work, remote services, or independently owned writers have stopped. The outbox/idempotency experiments in #228 address a different distributed-effect boundary and are not pooled here.

A potentially better next mechanism is generation-scoped staging: write each attempt to a unique target and promote a verified current generation atomically, which may avoid waiting on an obsolete producer. That has not been tested here.

## Verification

The source-hash-pinned auditor was frozen before measurement and passes all 16 cases. It independently parses PNG bytes with stdlib CRC/filter logic rather than candidate Pillow decoding, verifies source/fixture pins, process ordering, B-complete and final snapshots, and X11 release records. A full archive was extracted to a separate directory; the retained manifest verified with no mismatches and the replayed result was byte-identical.

Two prefrozen contract tests pass. Six additional post-hoc corruption tests run on copies of retained evidence and reject mutated final input, process ordering, B snapshot, final snapshot and pinned source, while the unchanged control passes. Post-hoc tests are verification only and are not part of the frozen decision gate.

## H / T / D / C / U

**H:** stop-request receipt alone permits unsafe same-target retry; tracked-producer reap is sufficient to prevent the observed late overwrite.

**T:** one fixed local FFmpeg pair, eight paired real-XTEST blocks, exact source/fixture hashes and schedule frozen before measurement, first outcomes retained.

**D:** scoped PASS: immediate exposes six late overwrites; reap-gated ends in B 8/8; all hard input/integrity gates pass.

**C:** extra waiting—not a better output algorithm—explains the difference. Unique staging, file locking, atomic publication or application-provided transaction semantics may provide stronger or faster boundaries.

**U:** one FFmpeg build/host, one output format/path, n=8/arm, scheduler jitter. Reap covers only the tracked process. No network, child writer, power loss, actual agent retry policy, generic exactly-once, or production performance claim.
