# Real-App-Server Chromium public-caller packet (2026-10-21)

This packet contains one-shot runs r01-r08. The authoritative conditions and
source hashes remain per-run; raw first outcomes are immutable. `source-sha256-r08.txt`
contains 179 frozen source entries and was checked with `sha256sum -c` before
the launch. The r08 launcher was syntax-checked and the Python runner compiled
before it launched. Run ID: `chromium-public-compiled-standard-caller-live-r08-20261021`.

## r08 outcome

Status: **`HOLD_WAIT_NOT_EXERCISED`** for the specific polling hypothesis. The
one real App Server turn (`01a15b80-ef46-7ed1-9812-62c70371c8e8`, gpt-6.1-sol,
medium) supplied one screenshot and retained usage of 13,335 input / 113 output
tokens. The standard public compiled method returned `TASK_SUCCEEDED` after two
actions; both action transitions report `release_verified=true`. The independent
localhost fixture scorer found exactly one `/submit` POST with the frozen token
`uictrl-20261021-b8e4`. Replay was denied, runtime `task_success` remained null,
close confirmed release, the session closed, Chromium exited 0, App Server and
fixture server closed, and the exact Xvfb process (PID 420) was reaped with exit
status 0.

The fixture was configured for a 400 ms delay and recorded 402.361 ms between
POST receipt (`474587447046`) and response-ready (`474989808283`). The compiled
method was configured with a 1,000 ms effect-observation timeout and 50 ms
interval. Its first post-submit effect capture (`475005848843`) occurred 418.402
ms after POST receipt, after the response was ready. The method therefore
recorded `effect_checked/succeeded` without `effect_observation_pending`. This
run shows a delayed response can finish through the public live caller; it does
not exercise the new pending/poll/reobserve branch. The run ID is consumed and
must not be repeated.

Raw evidence is under `raw/r08/`, including `run.json`, the provider-call and
protocol receipts, public compiled invocation/terminal/close receipts, source
and fresh screenshots, the fixture POST, independent score, and cleanup logs.
The frozen conditions are `CONDITIONS-r08.json`; pre-run inputs are pinned in
`source-sha256-r08.txt`. Host: native Ubuntu WSL2 with private Xvfb `:101`,
Chrome for Testing 156.0.8078.4, and localhost-only fixture. This is not WSLc,
physical desktop, MAP01, stopped-platform-I/O release proof, a reliability
population, or matched-efficiency evidence.

## r09 outcome

Status: PASS_POLLING_BRANCH_SCOPED_SINGLE_TRIAL by the independent
[audit-r09.json](audit-r09.json). A fresh one-shot run used one real local
Codex App Server turn (01a15b95-c3ef-7ec3-a259-6954a906a2f7, gpt-6.1-sol,
medium; 13,336 input / 143 output tokens) and the public guarded compiled
caller against a private Chromium window on native Ubuntu WSL2, display :102.
The fixture received exactly one /submit with the frozen token
uictrl-20261021-9f3c; its measured response delay was 1,602.360 ms.

The public method retained 19 effect_observation_pending events. The first
pending observation was 9.171 ms after POST receipt and 1,593.189 ms before the
fixture response became ready. A later successful effect observation occurred
64.124 ms after response-ready. The method returned TASK_SUCCEEDED; both
compiled actions retained release_verified=true; the independent fixture
scorer passed the exact POST; runtime task_success remained null and replay
was denied. Session close verified all keys/buttons up, the owner process
exited with code 0, and Chromium, App Server, fixture server and Xvfb were
closed/reaped.

Frozen conditions and the 179-entry source manifest are
[CONDITIONS-r09.json](CONDITIONS-r09.json) and
[source-sha256-r09.txt](source-sha256-r09.txt); the result artifacts are checked by [artifact-sha256-r09.txt](artifact-sha256-r09.txt); the exact runner and launcher
are run_public_caller_r09.py and launch-xvfb-r09.sh. Raw provider, public-call,
screenshots, event receipts, independent score and cleanup records are under
raw/r09/. This is one localhost-fixture sample on a dirty worktree based at
ef768ac; it proves the polling branch was exercised for this scoped bundle,
not a general reliability rate, physical desktop, MAP01, WSLc, or matched
efficiency. WSLc was not used.

## Next gate

The pending/poll/reobserve mechanics gate now has one qualifying scoped
Chromium/App Server sample. The next milestone is the matched three-arm,
six-position comparison already specified above: plain/current control,
optimized non-symbolic, and the integrated candidate, with cold acquisition,
warm reuse, invalidation/repair and post-repair reuse. First reconcile the
exact r09 source snapshot with the code intended for integration; do not
present a dirty-worktree result as a main-branch result. Freeze comparison
conditions, all-attempt accounting and the independent scoring protocol before
starting. Keep WSLc on HOLD until a fresh owned, unused allocation is verified.
The matched comparison and reliability objective remain open.

A 2026-10-21 read-only recheck recomputed the independent audit in a temporary copy and verified all 317 artifact-hash entries; see [audit-recheck-r09.json](audit-recheck-r09.json). It did not rerun Chromium or call the provider.
