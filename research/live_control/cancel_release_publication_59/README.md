# Cancel release publication regression (Issue #59)

The v39 cancellation path had two adjacent handoff failures. The owner could classify ExecutorV12's synchronous cleanup release as ordinary `release`, leaving the lease with no cancellation interruption. After correcting that reason, the asynchronous publication watcher could still lose a race with terminal cleanup: ExecutorV12 cleared its active intent before the watcher acquired the executor lock.

The source change fixes both boundaries. Owner release requests use reason `cancelled` when their lease cancel flag is set. ExecutorV12's terminal emitter publishes an already-recorded eligible owner receipt before forwarding the terminal event; its async watcher remains available for earlier publication, with the existing ID deduplication shared by both paths.

Run the deterministic regression from the repository root:

```text
python -B research/live_control/cancel_release_publication_59/test_cancel_release_publication.py
```

The test executes the real v10 owner queue, the v12 executor worker/cancel path, and the real lease stack. It replaces only Xlib/XTest with an in-memory fake keymap. Its small backend reproduces the pinned `session_v5.Backend.release_all` method exactly. It asserts exactly one verified `input_released` event, before terminal, with a matching intent token and identical owner receipt.

Test-first evidence: the regression was added on a branch based on main `8094af4631fc7bc5d92990e5151d5e89477ee39f` and failed on the exact current sources before either implementation change. On 30 repeated cancel-while-W-held cycles, the exact baseline missed publication in 30/30; the owner-reason change alone still missed publication in 30/30 because the terminal event beat the watcher; the combined candidate passed 30/30. Current main source identities were owner blob `341b3c01649943ddaad5f28431a792c4889cc36e` and ExecutorV12 blob `a51358a771810207ac031ebf56b3e63a4fda5a5d`.

This is a focused event-handoff repair. The fake server does not prove physical input, application receipt/useful feedback, bounded recovery, or MAP01 progress. No game, model, formal allocation, or main merge was involved.

## Delivery ambiguity and terminal-sink follow-up

On PR head `7c702769c7b8db36290391d115cae63f3f9a1770`, two additional test-first controls failed: an accept-then-raise release sink was invoked twice (the current client guard rejects a repeated early release for the same intent), and a throwing terminal sink left `executor.active` pointing to a stopped worker. The candidate marks each eligible release-event attempt before calling the sink. A sink exception is retained as `delivery_unknown` and is not retried because the event may already have been accepted. Terminal cleanup now clears the matching completed worker in `finally`, including when forwarding terminal raises. The terminal timestamp remains refreshed after the release barrier.

The focused regression command is:

```text
python -B research/live_control/cancel_release_publication_59/test_cancel_release_publication.py
```

All five cases pass on the candidate; `research/live_control/test_running_action_guard_v3.py` passes 3/3. `py_compile` and `git diff --check` pass. Scope remains deterministic fake-Xlib event-path construction only: it does not establish delivery over a production transport, physical key-up, application effect, useful task feedback, bounded recovery, or MAP01 success.

Repeated validation on Windows CPython 3.11.9: 30/30 focused process runs passed (150 test executions total), plus the 3/3 client-guard tests, `py_compile`, and `git diff --check`. Candidate SHA-256: `research/live_control/executor_v12.py` `8390b9c1f31a489638ab8b0e0116f029b2ee5d6bfcac6a6d1aea0f4b8e16faf4`; `research/live_control/cancel_release_publication_59/test_cancel_release_publication.py` `b6b74a9181dc025d42525502dc41e43b515b945d8080119026aefce5040eb04e`.
