# Matched late-input cancellation comparison (preregistered)

## Status

Preregistered before execution. The completed execution used one
ephemeral Linux container on the user's Docker Desktop engine, using the
already-cached Xvfb test image pinned by its image ID below. The container has
network disabled, a read-only root filesystem, a private tmpfs for Xvfb, a
read-only source bind mount, and this packet's raw directory as the only
writable bind mount. This is not WSLc, a physical desktop, a live game, or a
model/provider run. The source under test is current `main` at
`57573394c4d88988a40b0e57c270c945a3a621cd`.

Container image: `agent-interface-xvfb-mcp:late-input-r19`,
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`.
The existing image contains Python/Xvfb and the exact CI test dependencies;
no image pull or model/provider setup is performed.

## Question and hypothesis

Does the prestarted cancellation supervisor change the independently scored
old-task outcome when the standard caller's cancel acknowledgement is withheld
for one second while an eight-second XTEST request is queued? The working
hypothesis is that the prestarted route will preserve the exact one-effect
oracle more often. This is exploratory; four trials cannot establish general
reliability or causality beyond this fixture.

## Frozen design

- Arms: A = `AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=0`; B = `=1`.
- Fixed order: A1, B1, B2, A2 (ABBA).
- One fresh private Xvfb server and one fresh Python process per trial.
- Every trial: delayed keypress 8,000 ms; child cancel ACK withheld 1.0 s; owner
  process method tracing enabled; server pause 0 ms; cancel bound 3,000 ms;
  terminal bound 5,000 ms; expected old task effect `[1]`; expected fresh-task
  effect `[3]` on a distinct window on the same X server.
- The prestarted-supervisor flag is the only treatment difference. Test source,
  dependency versions, Xvfb geometry, ACK delay, and scoring remain fixed.
- Primary outcome: retained `independent_task_oracle.status` and its exact
  effect-count check. Record cancellation latency, runtime release/cleanup
  receipt, and the fresh-session task oracle as separate outcomes.
- No outcome or threshold may be changed after the first run. Preserve every
  JSON, observation image, stdout/stderr, Xvfb log, exit code, and SHA-256.
- Run all four scheduled trials once. Do not retry a failed or interrupted trial.
  If Xvfb cannot start, stop before input dispatch and retain the setup failure.
  If a trial reports failed final cleanup or a live owned process, stop the
  sequence, preserve evidence, and do not start another input trial.

## Interpretation limits

The synthetic Xvfb application and separate X client provide scoped task-effect
and key-state evidence. Runtime `task_success` remains non-authoritative. Results
do not establish Win32 physical release, user-facing application semantics,
provider efficiency, WSLc, MAP01, or project-wide reliability. Compare matched
arms descriptively; retain failures and do not pool these trials with earlier
CI attempts that used different ACK-delay settings.

## Execution and retained raw data

`run-local-abba.sh` ran inside the pinned container with
`AGENT_INTERFACE_TEST_PYTHON=/usr/bin/python3`. All four fixed attempts
completed once. Results and interpretation are in [`RESULTS.md`](RESULTS.md);
raw reports and logs are retained under `raw/`, with per-file SHA-256 values in
[`SHA256SUMS`](SHA256SUMS).

## Preflight correction (before any input trial)

The first runner invocation stopped at dependency preflight because its venv
had been placed in `/tmp`, which was cleared between WSL command invocations.
It did not start Xvfb or dispatch input and is not counted among A1/B1/B2/A2.
The failed preflight is retained as `raw/initial-preflight-failure.txt`. The
interpreter location was changed to the WSL user's persistent cache; all frozen
trial conditions, order, and outcome rules remain unchanged. The next runner
preflight started a private Xvfb on `:90`, while the integration fixture
intentionally skips unless `DISPLAY=:88`; unittest therefore reported one
skipped test and emitted no result report. No test body or input dispatch ran.
This is also a harness-setup failure, not a scored trial. A WSL preflight then
showed `/tmp/.X11-unix` is read-only and mode 0777; restoring its standard 1777
mode was refused by the filesystem. The test uses only display `:88`, now fixed
in the runner. The already-cached Docker image gives a writable isolated tmpfs
without changing the WSL system directory. The preflight records are retained
in `raw/`; no task input was dispatched in those setup attempts. The four
scored attempts were subsequently run once as preregistered. See
[`RESULTS.md`](RESULTS.md); setup failures remain preserved and are not counted
as scored trials.
