# Next private-Xvfb trial — prepared, not executed

Question: on a fresh owned Linux input domain, does the current public caller
retain bounded cancellation/UNKNOWN custody during a 1,000 ms private-server
pause, then permit a separate fresh-session task effect with independent
readback and no late old-session key through the existing 8,500 ms horizon?
Separately verify that the new pidfd STOP/CONT receipt and cleanup complete.

This is one constructed schedule, one invocation, no model, no comparison and
no retry. It cannot establish physical/MAP01 release or a general deadline.

## Before execution

1. Obtain a specific unconsumed WSLc allocation, its owner/window and approved
   CPU/memory budget. Do not infer ownership from zero clients or distro state.
   Preserve #7924's current STOP until that specific environment is established.
2. Qualify an image containing Linux/Python pidfd APIs, Xvfb, python-xlib 0.33,
   Pillow 10.2.0, numpy 1.26.4, and mcp 1.30.0. Record all installed versions
   and the immutable image digest before the trial. The old plain Python smoke
   digest is insufficient. Construction/qualification is a separate attempt;
   never install packages during the frozen formal run.
3. Freeze a source commit containing this helper fix, source Git blobs, image
   digest, complete command and resource limits in a new packet/run ID. Do not
   reuse any previous run directory or allocation. Mount source read-only and
   only that run's output directory writable; use `--pull never`, no network,
   no host X socket and no developer DISPLAY.
4. The dedicated container's launcher owns its Xvfb child on `:88`, disables
   TCP, records executable hash/PID and retains a process handle for emergency
   cleanup. Abort on an existing listener or missing pidfd support. Never kill
   by display/name or touch another container/process.

## Single trial command inside that owned environment

After the owned Xvfb is ready, supply its actual PID; do not copy an old PID.
The launcher must preserve stdout/stderr, Xvfb logs, source/image identity and
both inner/outer exit codes. The test command is:

```text
DISPLAY=:88
AGENT_INTERFACE_XVFB_PID=<owned live child PID>
AGENT_INTERFACE_MCP_XVFB_TEST=1
AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=0
AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1
AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=1
AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS=1000
AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT=<new writable output>/result.json
timeout --signal=TERM --kill-after=10s 210s python -B -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration
```

These lines are an environment/command specification, not a runnable host-side
WSLc launcher. The host launch command remains dependent on the actual allocation,
qualified image and scoped cleanup interface; placeholders are unresolved.

## Outcomes and stop/cleanup

- Pass only this schedule if the test actually runs (no skip), inner exit is
  zero, the JSON is complete, all original caller/fresh-effect/horizon checks
  pass, and an independent audit reconstructs the timing endpoints and verifies
  neutral state plus unchanged old UNKNOWN/no-replay receipt. Include the
  pidfd resume receipt and task property state before/after the fresh action.
- A test failure/timeout/ambiguous launcher result is terminal for the attempt.
  Keep raw first outcome, partial JSON and process/container identity; do not
  rerun the same allocation. Missing prerequisites before entry are HOLD.
- On every exit, resume only the owned retained Xvfb handle before attempting
  neutral readback; retire only the exact owned test/Xvfb children/container.
  If the container ID/cleanup receipt is missing, classify execution/cleanup
  UNKNOWN and do not issue global runtime inventory, prune, restart or kill.
- Readback and task effect remain independent of the runtime cancellation
  classification. Observing a finite horizon does not prove an old server
  queue is universally empty; keep `late_server_request_possible` conservative.
- No efficiency or reliability conclusion follows. Those require a later
  frozen matched protocol after this environment/path qualification.
