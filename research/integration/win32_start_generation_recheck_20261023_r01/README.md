# Win32 generation recheck before producer authorization — R01

The pre-fix public caller accepted generation A, then opened its producer gate
even if the configured target changed to B or its identity query became
unavailable before start. Admission's earlier check did not cover subsequent
factory, process-start, or process-identity waits.

`OwnedWin32SessionOwner.start_producer` now reads the configured generation
before invoking the producer factory and again after process registration,
before authorizing the child gate. A changed or unavailable generation records
UNKNOWN and denies replay; a created but still-gated child is retired without
requesting compensating UP against the now-unconfirmed target. Queries run
outside custody/journal locks so cancellation can close admission during a
blocked query. A duplicate start retains the same refusal and no new attempt.

## Evidence

Source commit: `d06b5d280011eb27a7f9776e83d7a8614cc9c8f6`.

| Run | Result |
| --- | --- |
| Initial reproduction, four cases | Four expected failures: caller incorrectly reports `running`. Preserved in `raw-red.txt`. |
| Final regression with frozen pre-fix owner from `6ee0c639b40322eff2a5d580cbc549eadb664ac4` | Five expected failures. `reproduce_baseline.py` substitutes the frozen owner class in memory, leaving repository files unchanged. |
| Current focused normal run | 43 tests pass, exit 0. |
| Current focused optimized run | 43 tests pass, exit 0. |

The five refusal cases are generation change after admission, during the
factory, during process identity lookup, identity unavailable before start,
and identity unavailable during process identity lookup. Each checks that the
start gate stays closed, no fake child remains live, no compensating cancel is
requested, and duplicate start cannot replay. A separate concurrency regression
blocks the second generation read, verifies cancel returns before that read is
released, then verifies the child gate never opens. Existing public-route,
actual-backend/fake-API, caller-owner and process-owner tests are included.

The final source commit adds a docstring explaining the rechecks after the
captured runs; no executable statements changed after those runs. The initial
four-case reproduction predates the final five-case test. Use the retained
baseline script and final test for the source-bound negative control.

`conditions.json` preserves commands and environment; `SOURCES.json` hashes
selected canonical Git blobs at the source commit. `SHA256SUMS` covers all
packet files except itself. Prior packets remain unchanged.

## Limits

These are synthetic generation readers and fake process refusals, plus the
existing inert spawned-process composition checks. Point-in-time rechecks are
not atomic with target replacement after the final read. They do not qualify
native generation fencing, generation changes during recovery, queued input
effects, physical release, live task/MAP01 effect, matched efficiency, or
reliability. A concurrent cancellation already in progress retains its own
separate receipt; this fix does not qualify its target authority. No native
desktop input, WSLc allocation, or Docker was used.
