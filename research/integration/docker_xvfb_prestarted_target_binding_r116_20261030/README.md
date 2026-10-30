# Prestarted XRes target identity: R115 failure and R116 follow-up

R115 was a single frozen public MCP Xvfb cell. It failed before mint or input: first observe returned `runtime_failed`, `target_identity_unavailable`. The retained raw packet is [raw/r115](raw/r115); it was not retried. The receipt did not expose the inner reason, so its exact failure cause is inferred, not directly observed.

The parent creates the one-shot identity supervisor using its initial session ID, then the child owner returns a different session ID and `_apply_snapshot` replaces the parent ID. A focused regression reproduced this mismatch (red: parent-session versus child-session). The fix does not pre-bind the worker to the provisional parent ID; the supervisor continues to require the worker receipt to match the actual request operation and child session IDs. The focused test and 19 other target/owner tests passed in the pinned Linux image.

R116 is a new, separately frozen one-cell follow-up, with the change and an explicit receipt gate declared before execution. Docker exit 0; result PASS, 15/15 gates. With a 650 ms Xvfb stop and an 8 s delayed request, the owned old target was retired before resume, old result remained UNKNOWN with no replay, the runtime release had readback, and the distinct fresh target received B exactly once and no old A through the 8.5 s observation horizon. The target identity receipt matched the child session and the identity worker exited cleanly. Server creation was 528.39 ms and first observation after creation 1165.32 ms in this one cell; these are not a paired speed comparison. Raw, source hashes, preregistration, runner and post-trial checksums are in [raw/r116](raw/r116). These artifacts came from the private synthetic Xvfb environment; the original local packets are also preserved.

This is an experimental opt-in overlay on main d534, not a merged feature. It does not establish general reliability, WSLc or MAP01 success, or end-to-end agent speed. The R115 diagnosis remains an inference because its nested rejection was not retained.

## Follow-up regression: stopped server

On 2026-10-30 the opt-in private-Xvfb regression was extended to construct the prestarted identity worker while the server was healthy, stop that exact Xvfb, and request binding with a 200 ms transaction deadline. It requires `target_identity_unavailable`, `transaction_deadline`, confirmed worker retirement and return within 1 s while the server remains stopped. The same test retains the fresh-worker timeout and bound-target retirement checks, with a resume watchdog and explicit cleanup. In the pinned Docker image with network disabled, read-only root and source, and `AGENT_INTERFACE_OWNED_TARGET_XVFB_TEST=1`, the Xvfb and related target/session suites passed 20 tests in 0.895 s. This is a regression check, not a new formal reliability allocation or a task-level benchmark.

## Independent regression reproduction

Use a new, empty output directory; do not write into `raw/r115` or `raw/r116` or call a later run either historical allocation. From this repository root on a Linux host with Docker and the pinned image available locally, the following runs the preserved R116 runner as a new local regression (the image is not pulled by this command):

```sh
mkdir -p /tmp/owned-target-regression-new
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --mount type=bind,source="$PWD",target=/workspace,readonly \
  --mount type=bind,source=/tmp/owned-target-regression-new,target=/evidence \
  --workdir /workspace -e TARGET_RETIRE_MODE=retire \
  sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425 \
  python3 -B /workspace/research/integration/docker_xvfb_prestarted_target_binding_r116_20261030/raw/r116/pilot.py
```

Read `/tmp/owned-target-regression-new/result.json` and inspect the individual checks and cleanup. The runner creates private Xvfb and disposable child processes inside the isolated container. Startup, timing and scheduling vary by host. It is not a matched performance comparison and a later run does not replace the frozen historical results. The `raw/.gitattributes` rule preserves the exact bytes covered by the recorded checksums.

The source manifest hashes the bytes actually mounted during R116. Eight tracked baseline/overlay Python files were checked out with CRLF line endings on the Windows host; their Git blobs use LF and therefore hash differently. Converting the corresponding Git blob LF line endings to CRLF reproduces each of those eight manifest hashes. The two newly added Python source files in the manifest match their Git blobs directly at PR commit `38715d930a15f43c926e350cc049fad38ec2e494`; `owned_target_session.py` changed later to recheck an unconfirmed retirement on explicit close, so the current file no longer has the R116 hash. The preserved runner hash is checked against `raw/r116/pilot.py`. This reproduction command exercises the same code with the checkout's line endings; it is not a byte-identical replay unless the listed hashes are matched first.

## Post-R116 cleanup regression

The first candidate cached an UNKNOWN target-retirement receipt permanently. If independent input release had been readback-verified, the base close path reused the release receipt and never called target cleanup again. A focused mocked regression reproduced the missing target recheck. The later patch allows one bounded target retirement attempt on each explicit later close when the previous attempt is UNKNOWN and the control owner is confirmed retired; it retains the previous receipt and does not change old task UNKNOWN or allow replay. It does not retry a refused identity or operate while owner retirement remains unconfirmed. With that patch, the pinned Docker image passed 84 target, Xvfb, existing MCP-owner and cancellation-supervisor tests. This is local regression evidence, not a repeat of R116 and not an application-level effect proof.

A later Linux regression injects a pidfd signal error for a real disposable child, then calls the experimental session close and verifies that the same pidfd retires that child while an unrelated witness child remains alive. A private Xvfb variant additionally binds the actual XRes window to the child before stopping Xvfb; while it remains stopped, it injects the first signal failure and verifies a successful bounded recheck and retained UNKNOWN/no replay. Both tests mock the base close report/control-owner retirement, and the witness test mocks XRes identity, so neither demonstrates full public MCP fault recovery or real application effects. The target/session/Xvfb suites passed 24 tests in the pinned Docker image (0.676 s).

## R118: public MCP injected retirement failure

R118 is a separately frozen, one-cell, no-retry experiment against PR source 24ab4707719c22469161df733cbb925b594539d6, with a single injected `PermissionError` on the owned target pidfd signal. See [raw/r118](raw/r118) for the runner, preregistration, source hashes, output and checksums. Its 16 predeclared gates passed: cancel recorded the initial target exit as UNKNOWN with `pidfd_signal_failed`; the exact old target was alive before Xvfb resumed; explicit public close then confirmed target retirement while retaining the failed receipt; the old call and close remained UNKNOWN with replay denied; runtime release had readback; and the fresh target recorded B once and no old A through an 8.5 s horizon. The Xvfb stop lasted 651.15 ms.

**Counterevidence:** the old target recorded one A press before the stop and three A presses by its final recorded state. The additional two press events occurred approximately 4.5 ms and 43.3 ms after Xvfb resumed, while the old target was still alive; a release readback occurred between the two. The trial had autorepeat enabled, and this data does not identify whether the additional presses were autorepeat or queued input. Thus the PASS applies only to the preregistered recheck and fresh-target gates; it is not a pass for preventing extra old-target effects. Keeping the target alive until explicit close leaves a consequential exposure window. The historical runner's `old_process_retired` timing field is misleading in this cell: it records a checkpoint before resume while the target was alive, not retirement; use `alive_before_resume`, `exitcode_after_close`, and the target receipts instead.
