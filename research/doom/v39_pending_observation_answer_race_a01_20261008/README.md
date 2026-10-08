# V39 pending-observation / planner-completion race

This construction targets a narrow gap in current-main V39. Its control loop checks `while not future.done()` before reading from the observer queue. If the model future is already done while a typed observation is queued, the loop body is skipped and the observation monitor does not run before the answer is considered. The exact frequency of this ordering is not measured.

The patch adds a bounded snapshot drain of events already queued at that boundary. It records the latest frame, retains a matching cover terminal, and surfaces the first monitor invalidation. The existing invalidation path then cancels an active cover and discards the completed answer. Stable/soft observations and empty queues retain the prior path. The drain is bounded by the queue size at entry so continuous observation production cannot hold planner completion indefinitely.

The regression test covers hard invalidation, a matching terminal, soft-change preservation, and an empty queue. The focused local run extracted the exact helper from the PR source and passed 3/3. The complete controller module was not imported in that temporary harness. This does not establish reader-delivery latency, live HUD timing, App Server races, input release, useful feedback, survival, or task success. No live allocation was used.

