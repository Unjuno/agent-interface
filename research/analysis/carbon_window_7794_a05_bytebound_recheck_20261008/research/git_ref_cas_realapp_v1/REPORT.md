# Real Git ref CAS through XTerm/XTEST — discovery v1

## Decision

**RETAIN as real-domain evidence for an effect-owner, plan-bound compare-and-swap boundary.** Git 2.47.3 `update-ref <ref> <new> <old>` rejected a relevant ref change that occurred after a client-side check, while a non-atomic precheck followed by blind update overwrote that change. An unrelated ref change did not block target-ref CAS.

**RETAIN plan-bound provenance:** changing only expected-old to the newest OID while reusing the old planned new OID recreated the stale-plan failure.

**HOLD generic GUI promotion.** XTEST typed only `./go` into real XTerm; the frozen adapter then invoked Git's ref primitive. This is a real application/effect boundary plus explicit adapter, not a claim that arbitrary GUI apps expose equivalent semantics.

Immutable research source base: `21fb50be01e99816eb3a555e2ae131e679723f48`.

## Retained setup/harness outcomes

Five earlier allocation IDs are retained as non-successes rather than rewritten:

- a1: 0 scored rows; default Xauthority absent.
- a2: 0 scored rows; Xauthority fixed, `.` keysym conversion failed.
- a3: harness stopped because it incorrectly required CAS mismatch exit code 1; Git returned 128 while preserving the ref. No partial block promoted.
- a4: 20-repetition allocation exceeded the outer 120 s execution limit; no final scored JSONL promoted.
- a5: 10-repetition allocation also exceeded 120 s; no final scored JSONL promoted.
- a6: repetitions fixed at 3/cell before execution; completed 18/18 rows.

## Rung 1 — non-atomic precheck versus native Git CAS

Private Xvfb 640×480×24; XTerm 398; actual XTEST key events. Both arms receive exactly `./go` + Return. The adapter reads `refs/heads/target=A`, signals the harness, and waits. The harness then either does nothing, changes the target to C, or changes an unrelated ref to C. Only then does the effect execute.

| Case | precheck + blind update | `git update-ref target B A` |
|---|---:|---:|
| stable | correct B 3/3 | correct B 3/3 |
| target A→C after check | **overwrote C with B 3/3** | **rejected 3/3; C preserved** |
| unrelated ref A→C | target B + unrelated C 3/3 | target B + unrelated C 3/3 |

Audit verified check-before-competitor-before-effect ordering, exact XTEST command characters, final refs and return-code class for all 18 rows.

Git-call timing in this GUI block:

- blind/non-atomic median 2.998 ms, range 2.692–5.100 ms, n=9;
- native CAS median 2.963 ms, range 2.412–4.805 ms, n=9.

Return injection → completed initial ref read was ~0.88 s median in both arms; that is XTerm/shell fixture synchronization, not Git CAS latency.

## Rung 2 — expected-OID provenance

Only the expected-old source changes. Planned new B is held fixed.

| Case | plan-bound expected A | refreshed expected-current |
|---|---:|---:|
| stable | correct B 3/3 | correct B 3/3 |
| A→C after plan | **safe reject; C 3/3** | **accepted stale B; overwrote C 3/3** |

A fresh dependency token therefore does not make an old action fresh. It can instead detach the action from the observation that produced it.

## Separate Git primitive microbenchmark

200 randomized repetitions per condition, reset outside the timed region:

| Operation | median | empirical p95 | range |
|---|---:|---:|---:|
| blind update after changed ref | 4.215 ms | 8.354 ms | 2.954–24.963 ms |
| CAS stable A→B expected A | 4.354 ms | 9.287 ms | 3.010–43.179 ms |
| CAS mismatch current C expected A | 2.478 ms | 5.472 ms | 1.976–7.210 ms |

Git 2.47.3; CPython 3.13.5; local filesystem; CPU frequency not pinned. These are local mechanism timings, not a product throughput benchmark.

### Variable table

| Name | Meaning | SI unit | Definition / assumptions | Type |
|---|---|---|---|---|
| A | OID used when plan is formed | 1 | deterministic local Git commit | identifier |
| B | planned new ref value | 1 | fixed planned effect | identifier |
| C | concurrent competing ref value | 1 | distinct from A/B | identifier |
| target ref | resource dependency | 1 | `refs/heads/target` | identifier |
| effect interval | Git update duration | s | same `perf_counter_ns` clock | scalar |
| repetitions | trials per GUI cell | 1 | 3 after retained setup/time-limit failures | integer |

Unit check: elapsed ns differences are divided by 1,000,000 for ms; OIDs/ref names are dimensionless identifiers.

## H / T / D / C / U

**H:** a real effect owner with native versioned CAS can preserve a relevant concurrent update after a client check while permitting unrelated changes; expected version must remain plan-bound.

**T:** 18 completed XTerm/XTEST Rung-1 rows; 12 Rung-2 provenance rows; 600 separate primitive timing rows. Earlier setup/harness/time-limit outcomes remain non-promoted.

**D:** PASS narrow Git mechanism: relevant CAS reject 3/3, unrelated progress 3/3; non-atomic overwrite 3/3. FAIL refreshed-token reuse: wrong overwrite 3/3. General GUI promotion HOLD.

**C:** protection comes from Git's native ref transaction, not screenshot/XID freshness or faster polling.

**U:** small GUI n, one Git version/filesystem, synthetic local commits, adapter-mediated command, no remote refs/network/crash/multi-ref transaction/model/Doom. Empirical ranges reported; no combined `u_c`/coverage factor estimated.

## ERROR CHECK

Independent `audit_all.py` validated **630 retained scored rows**: 18 Rung-1 GUI rows, 12 Rung-2 GUI rows, and 600 primitive benchmark rows, including manifests, causal ordering, typed command evidence, final refs, unrelated-ref preservation and expected-OID provenance.

## Next discriminating test

Use the same real Git/XTerm domain with semantic Git metadata deliberately withheld. If stable and concurrent-change worlds have identical terminal observations, compare blind continuation with dependency-unavailable yield. This directly pairs a real cooperative version boundary with a real non-cooperative observation contract without changing the application domain.
