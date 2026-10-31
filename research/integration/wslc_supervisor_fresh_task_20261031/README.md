# Stopped-Xvfb supervisor: retain the fresh task even when the old task fails

The existing stopped-server integration first required `a` to remain down after close, then required the supervisor-mode original-task oracle to pass, which requires `a` up at the earlier horizon. That combination made a successful supervisor outcome impossible. This test-only change compares both key states before and after close instead, and evaluates the **unchanged** original-task expectation after the independent fresh-target recovery. UNKNOWN/no-replay assertions and both task oracles remain in force; an original-task failure still fails the supervisor-mode test.

Two isolated, sequential, single-attempt WSL-backed Docker trials used the same edited test and source subset, pinned image, CPU/memory limits and private Xvfb. They produced the following observations:

| Trial | Supervisor | Old task | Separate fresh task | Overall test |
|---|---|---|---|---|
| b06 | on | FAIL; `a` remained down through horizon | PASS; expected effect and both keys up | FAIL as required |
| b07 | off | FAIL, as expected by the control | PASS; expected effect and both keys up | PASS, 5 tests |

Before the new target is created, **the test harness explicitly sends a key release** and verifies it. The fresh task therefore shows only that a new controlled operation can work after this manual isolated cleanup. It does not demonstrate automatic release, safe shared-display recovery, or a successful old task. Both original cancellation results remained release-unconfirmed and replay-denied. B06's measured fresh-operation recovery interval was 726 ms, excluding the later observation horizon; this is one synthetic observation, not a speed or reliability estimate. Both harnesses ended with the two monitored keys up.

`public.zip` preserves frozen conditions, runners, outputs and full receipts with hashes; `python audit.py` checks both task outcomes. The source subset archive and edited test hashes are in the manifest. Source and image bytes are not included. Earlier failed trials remain in PRs #9972 and #9973. No MAP01 or general completion claim follows.
