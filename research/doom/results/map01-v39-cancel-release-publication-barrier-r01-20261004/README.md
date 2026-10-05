# Cancellation receipt / terminal race replay — R01

## H — Hypothesis

Even after InputOwnerV12 records a verified `owner_release(reason=cancelled)`, ExecutorV12's asynchronous release watcher can lose the race to terminal cleanup. If the worker emits `terminal` and clears `active` before the watcher acquires the executor lock, the watcher sees no matching active job and returns without publishing the standalone `input_released` receipt.

## T — Test

Ran the exact same deterministic post-sample/pre-fake-KeyRelease integration test in fresh Python processes, first against current `main` + #7440 + #7468 without the terminal barrier, then with only the ExecutorV12 terminal-publication barrier from #7429 layered onto the same combined tree.

- Current-main baseline: `main=48405df03913bbe94f29b2e576f7fe5532972095` + #7440 `99b7d130742b4e884709a862bc074d15e6b42ac9` + #7468 `06df46e496b31a15694d5f5ca5532405af358d8f`; merged index tree `135c161c842880f4fcba9ba890d06f4ff84f5b44`.
- Barrier candidate: same inputs plus #7429 head `6ebf04bc00a88c5707814dce26b7d9022a921311`; merged index tree `3c429aa6b05844089d6532056a8a46b4f64e994c`.
- Test source SHA-256 is identical in both: `6195b0469dccbf48fa3ab204e54b401dacd27ffd9dcf7f1657d45e64ff641f3d`.
- The v12 owner source remains identical in both: `7cc6b3bcac201624992657203cbb9459120956ad65c1fb6e56e4ac85aafad8f2`.
- ExecutorV12 source SHA-256 changes from `b81ad839318e3a53edfde4425f61947fbbc6e142a85348e0a1fe730b754fc74d` to `11ed8e63fffa45bba52d8be2a926a1b5a09b20cfcbb0be0b02defc4b8a1e038b`.

## D — Data

- Without terminal barrier: **18/20 PASS, 2/20 FAIL** (fresh-process runs 15 and 16). Both failures emitted a cancelled terminal carrying the verified-empty owner release/interruption record but omitted standalone `input_released`.
- With #7429 terminal barrier: **20/20 PASS**; every run asserted `input_released` publication timestamp precedes the cancelled terminal timestamp.
- On the barrier candidate tree, #7429's focused cancellation-publication suite passed 6/6, V13 executor integration passed 4/4, running-action guard passed 4/4, and `py_compile` passed.
- `git diff --check` on the combined #7429 candidate tree reported trailing blank lines at EOF in `research/live_control/cancel_release_publication_59/test_cancel_release_publication.py:366` and `research/live_control/executor_v12.py:164`. These are in the parallel PR's files and were not edited here.
- All 40 per-run stdout/stderr logs are preserved in `REPLAY_LOGS.tar.gz`.

## C — Claim boundary

The controlled comparison supports the specific race mechanism: the owner cleanup can be correct while consumer publication is lost to terminal teardown, and the synchronous terminal barrier prevents that outcome in these 20 forced-schedule trials. This is not a natural race-frequency estimate, a proof of zero residual probability, or evidence that an unverified physical release occurred in the failed trials; the terminal event still contained a verified-empty owner record.

## U — Unresolved / STOP

- #7429 is an open, unmerged parallel PR. Its last observed head was `6ebf04bc00a88c5707814dce26b7d9022a921311`; two Native MCP workflow checks were still in progress at 05:26 UTC. Do not adopt it as integrated until reviewed and its checks settle.
- This comparison was host-only on macOS arm64 / Python 3.14.5. OrbStack's Docker context had no running containers, but `docker image ls` failed on a missing content-store blob (`operation not supported`) and `python:3.14` was not locally available. No container was started, pulled, or built.
- Fake Xlib/XTest only: no real X server, physical device, application/game, model, useful-effect scorer, bounded recovery, matched performance, or live MAP01 allocation. #59 remains open.

## Reproduction

From repository root, run the exact test with `python3 -m unittest -q research/live_control/test_executor_owner_cancel_cause_postsample_v1.py` in each source tree. The two trees and all repeated-run output are identified in `FREEZE.json` and `REPLAY_LOGS.tar.gz`.
