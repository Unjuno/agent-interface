# Current-main Calc/Fake X full-discovery recheck — 2026-11-21

## Result

Exact source: main `6f33f6ac2d263d2183b8f730c087115afbf0414c`, after PR #10367. Windows CPython 3.11.9 discovered 117 tests.

| Run | Result | Time |
| --- | ---: | ---: |
| Full discovery R01, normal | 117/117 PASS | 70.137 s |
| Full discovery R01, `-O` | 117/117 PASS | 69.720 s |
| Full discovery R02, normal | 116/117 PASS; one failure | 90.837 s |
| Full discovery R02, `-O` | 117/117 PASS | 78.116 s |
| Isolated partial-input cancellation test, normal | 1/1 PASS | 6.161 s |
| Isolated partial-input cancellation test, `-O` | 1/1 PASS | 6.143 s |

R02 normal failed `PartialInputCancelAccountingTests.test_cancel_after_first_transition_is_joined_without_replay`: its nested Calc fixture did not reach the Save boundary within the test's three-second wait, then the cancellation path did not produce a terminal receipt before the test deadline. The same full-discovery test passed in R01 normal and in both optimized runs; it also passed when run alone in both modes. The earlier stable-menu-anchor failure from the 107-test history did not recur in these runs.

During the R02 full run, other Python/CI and evidence jobs were visible on the host. Their influence is unknown; no causal attribution is made. Preserve the R02 failure. The full discovery is **not repeatably green**; focused normal/optimized passes and the R01 pair do not erase the R02 failure.

## Relation to earlier evidence

The earlier 107-test run on main `551cf28bb3ef3249af66d4c1ea33c2ca0b98882e` had two failures: the public-MCP Calc composition assertion and this cancellation-accounting test. Its source and outputs remain unchanged in [the earlier packet](../current_main_late_usage_port_20261121/RESULT.md). This current-main recheck has 117 discovered tests; it does not rewrite the old result. PR #10367 repaired the Windows Calc effect-clock mismatch, and the same-main composition selector now passes on Windows and pinned Docker. This packet shows the broader cancellation accounting remains host-sensitive under full discovery.

## Scope and next step

No runtime code changed for this recheck. It is offline Fake X/test-suite evidence only: no live provider, GUI input, MAP01, matched efficiency, or recovery-reliability estimate. Next, instrument the failing test's setup-to-Save phases under bounded full-discovery and isolated runs, then fix the fixture only if a specific scheduling race is measured; do not widen its timeouts or weaken release/effect assertions to manufacture a pass. Keep Issue #57 open.
