# V39 pending-observation / planner-completion race

This construction targets a narrow gap in current-main V39. Its control loop checks `while not future.done()` before reading from the observer queue. If the model future is already done while a typed observation is queued, the loop body is skipped and the observation monitor does not run before the answer is considered. The exact frequency of this ordering is not measured.

The patch adds a bounded snapshot drain of events already queued at that boundary. It records the latest frame, retains a matching cover terminal, and surfaces the first monitor invalidation. The existing invalidation path then cancels an active cover and discards the completed answer. Stable/soft observations and empty queues retain the prior path. The drain is bounded by the queue size at entry so continuous observation production cannot hold planner completion indefinitely.

The regression test covers hard invalidation, a matching terminal, soft-change preservation, an empty queue, and an event arriving after the queue snapshot. The focused local run extracted the exact helper from the PR source and passed 5/5 including an event-arrival-during-drain boundary. After that initial setup failure, the complete controller module was imported with 18 pinned current-main dependencies and the proposed five-test suite passed 5/5. This does not establish reader-delivery latency, live HUD timing, App Server races, input release, useful feedback, survival, or task success. No live allocation was used.



## Current-main retest

The controller and original regression test were fetched from main at commit `a537c80de21ba24d774fb332e34fcd415db51b7d` and matched locally. The PR adds a fifth regression for arrivals after the snapshot (test blob `9136d705f1f2e871c7c0b35ff0a4e3931fd9249a`). The helper-extraction harness passed 5/5. An initial isolated full-module import failed before collection because `map01_stagnation_v1` was missing; after staging 18 current-main dependency files and verifying their Git blob IDs, the complete controller module and proposed test file imported normally and passed 5/5 with unittest. Both runs and the setup failure are retained in `TEST_OUTPUT.txt`. No runtime or game session was started.

