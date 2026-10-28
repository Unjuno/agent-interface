# Docker/Xvfb owned-MCP journal recovery — R24

## Result

One standard public MCP cancellation/recovery integration test passed in a
pinned Linux/amd64 container, using the current worktree's guarded-X11 runtime
with opt-in JSONL retention. The harness exited 0 and wrote the full raw result
to the task-local packet at
`private-packets/docker_xvfb_owned_mcp_journal_recovery_20261029_r24/`.

After the exact owned process was retired during blocked `Display.sync`, the
parent reopened and verified its journal. The journal retained the public and
internal observations, `mint-field`, and the attempted program record. It had
no completed execution receipt and no `session-close` record, as expected for a
forcibly retired owner. The public API retained the old call as
`runtime_failed`, `cleanup_status=UNKNOWN`, `release_confirmed=false`,
`task_success=null`, and `replay_allowed=false`.

The old synthetic application task **failed** its exact effect-count oracle:
the expected single A effect became three. The separate fresh C task passed its
effect-count, generation/fence, and all-up checks. A physical supervisor
readback observed no held keys, but it did not upgrade the old API result from
UNKNOWN. The test also recorded no late old B press after the fresh session.

## Conditions and measurements

- Pinned image: `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`.
- Private Xvfb 2:21.1.7-3+deb12u13; network disabled; read-only container root;
  runtime source mounted read-only.
- Public MCP owned-process path, journal retention, prestarted cancel
  supervisor, 4,000 ms Xvfb pause, 8,000 ms delayed keypress, and a test-only
  12 s cancellation transaction budget.
- Test duration: 9.262 s. Cancel response: 308.315 ms. Fresh C input invocation to
  independent effect readback: 44.623 ms.
- The C interval is one recovery-task sample. It is not an efficiency score
  and is not comparable to R23's one-action route benchmark.

## Custody and scope

`PRETRIAL.json` pins SHA-256 for all 331 runtime files before launch; all matched
immediately after the run. Subsequent local normal/`-O` checks changed only the
CLI-forwarding assertion in `test_mcp_owned_process.py` and its two generated
Python bytecode files; production runtime sources remain unchanged. The exact
posttrial hashes are in `POSTTRIAL_SOURCE_SHA256.json`. `RUN_INVOCATION.json`
records the Docker command, image, mounts and environment.
`POSTTRIAL_EVIDENCE_SHA256.json` indexes the raw result, observation image,
command output, Xvfb log/PID, and Docker/unittest exit codes. The result itself
contains the exact verified journal references and task-oracle reports.

This is one synthetic Xvfb recovery integration sample. It shows that journal
prefix custody composes with the public MCP cancellation path while preserving
UNKNOWN after forced owner retirement. It does not show a successful old task,
WSLc/native-Windows behavior, MAP01 completion, provider-loop efficiency,
general reliability, or a broad speed advantage. It does not satisfy Issue
#2789's six-task matched integration gate.
