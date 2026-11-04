# Matched late-input cancellation comparison (preregistered)

## Status

Preregistered before execution. This is a local Ubuntu WSL 2 / private Xvfb
comparison, not WSLc, a physical desktop, a live game, or a model/provider run.
The source under test is the current `main` checkout at the SHA recorded in
`run-metadata.txt`.

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

Run `run-local-abba.sh` from this checkout with the pinned test interpreter
created in `/home/user/.cache/agent-interface-xvfb-pr10226-20261105/venv`. Raw
reports and logs are retained under `raw/`; the summary and hashes are added
only after the four fixed attempts finish.

## Preflight correction (before any input trial)

The first runner invocation stopped at dependency preflight because its venv
had been placed in `/tmp`, which was cleared between WSL command invocations.
It did not start Xvfb or dispatch input and is not counted among A1/B1/B2/A2.
The failed preflight is retained as `raw/initial-preflight-failure.txt`. The
interpreter location was changed to the WSL user's persistent cache; all frozen
trial conditions, order, and outcome rules remain unchanged.
