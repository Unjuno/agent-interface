# Owned guarded-MCP process integration — 2026-10-19

## Scope and disposition

This is a local engineering integration regression on `runtime/cli_v1`, based on
`4e36e47a690621a658515b5107cce020dfe6df82`. It is not a live-X, WSLc, or task
success experiment. The implementation is on branch
`runtime/guarded-mcp-owned-process-20261018` and has not been merged.

The opt-in `--guarded-owned-process` route puts the complete guarded-X11 session
behind one spawned owner process and exposes only allowlisted RPC operations.
The option requires guarded X11, process identity, and the query worker. On
cancellation, if the operation remains blocked beyond a finite retirement grace,
the exact child process is terminated. The caller preserves the original task
call as failed/aborted, does not replay it, and reports release as unconfirmed
with cleanup `UNKNOWN` and late server work possible.

## Local verification

The 110 selected guarded-MCP tests passed in both normal Python and optimized
Python (`-O`), including the six new standard-caller tests for option
validation, CLI forwarding, stable-generation observation/input/close,
changed-generation stale-alias refusal, and blocked-I/O cancellation. The
selection covered
`test_mcp_owned_process`, `test_mcp_process_identity`,
`test_mcp_transport_cancellation`, `test_mcp_wait_budget`,
`test_mcp_target_queries`, `test_mcp_guarded`, and `test_mcp_server`; nested
stdio tests were excluded because their child interpreter could not import the
temporary MCP dependency path in this host setup. The exclusion is not a pass.

The cancellation regression blocks Fake X `sync` after CTRL-down is recorded.
The standard MCP cancellation path retires the exact owner process. The fixture
still records keycode 1 down after retirement; the same call becomes
`runtime_failed`, release remains false/`UNKNOWN`, task success is null, replay
is refused, and `late_server_request_possible` remains true. This is direct
evidence that process retirement bounds future writes from that process but
does not prove release of queued or server-held input.

The clean Fake X control exercised `interface_guarded_observe`, mint, input,
and close through the standard MCP server. Its observation carried a
process-generation digest and ran in the spawned owner. The synthetic query
worker and Fake X backend do not qualify native target incarnation, real X11
ordering, application effect, physical release, or latency.

The owner snapshot now also retains Python-Xlib's X connection
`resource_id_base` when available. The Fake X composition asserts this value
crosses the owner/MCP boundary. This is only an exact-client identity seed for
a possible disconnect-fence experiment; it does not show that X drained that
client's requests or establish cleanup authority.

A separate stale-alias regression changes the query worker's process-generation
digest after observation and mint but before input. The standard caller returns
`refused`; its nested result gives `SCOPE_MISMATCH`, reason
`process_generation_changed_or_missing`, and `input_dispatched=false`. This
verifies that the existing process-generation fence crosses the spawned-owner
RPC boundary. It remains synthetic query-worker evidence, not a live XID reuse
test.

## Queued-DOWN composition counterexample

The new `test_prearmed_cleanup_can_precede_retired_owners_queued_down` composes
the standard MCP owner process with a synthetic per-connection XTEST queue. At
the blocked `sync`, the child connection has one queued `KeyPress(code=1)` while
the modeled server keymap is still empty. Cancellation retires the exact child;
the original call finishes `runtime_failed` with release `UNKNOWN`, no task
success, and replay refused. A fresh cleanup connection invokes the actual
`X11Backend.release_all` method with prearmed `CTRL:1`. Its sync processes only
that connection's `KeyRelease`, so the method returns
`{"keys_down":[],"buttons_down":[],"verified":true}`. The fixture then processes
the old child's still-queued DOWN and the modeled server keymap becomes
`[1]` (down).

This is a falsifiable integration counterexample in a deterministic fake
transport, not an X server ordering claim. It demonstrates that process death
and a prearmed release catalog are insufficient if a prior positive input
request may still be queued. A production caller must establish a queue-drained
or late-send fence before treating any independent release receipt as final;
otherwise retain `UNKNOWN`. The preserved source for this check is the test
itself, and the current run passed as part of the 110-test normal/`-O` suites.

## Remaining boundary

Do not promote or close #17. A current-source reconciliation found the
completed [#7041 successor report](https://github.com/Unjuno/agent-interface/blob/main/research/concurrency/x11_crash_cleanup_scope_a02_17_5ce3_20261003/REPORT.md): its empty-scope arm left F8 down despite a scoped verified receipt, while six prearmed-scope reference cells released F8 only after same-generation owner death and preserved a disjoint F9 bystander. That frozen Xvfb result supports a research-only prearmed cleanup transfer, not a public/production recovery API.

The #7041 positive reference paused only after its F8 press had been synced and
independently observed. It does not qualify cleanup when the task writer is
blocked in `sync` with a DOWN queued but not processed. The retained
[release-order counterexample](../../live_control/fake_x_release_order_a01_20261018/REPORT.md)
shows that independent UP plus an empty readback can precede that queued DOWN,
leaving the key down after the writer resumes. Therefore the next integration
question is whether the standard MCP path can prearm a cleanup-only obligation
for known input, bind it to the exact owner/display generation, and establish a
queue-drained/late-send fence before transferring it after verified owner
death. Test both already-processed DOWN and DOWN queued before server processing;
if the latter cannot be fenced, keep cleanup `UNKNOWN` and the original call
aborted. The current branch does not implement that transfer; process retirement
still left keycode 1 down in Fake X. Native X behavior, hard release deadline,
live task effect, MAP01, and efficiency remain unverified. No WSLc allocation was
used.

One concrete fence candidate is XRes `QueryClients`: its protocol reply lists
currently connected clients as resource-base/resource-mask ranges. The owner
snapshot records the exact Xlib connection resource base. A candidate experiment
can kill the owner with DOWN queued, query that exact base from a new X client
until it disappears, then attempt a fresh-connection release and keymap
readback. The [X-Resource protocol specification](https://www.x.org/releases/current/doc/resourceproto/resproto.txt)
defines `QueryClients` as returning currently connected clients. This repository
has not run that experiment on Xvfb/Xorg/XWayland, established behavior across
those servers, or bounded the query itself. A stuck query remains `UNKNOWN`;
client disappearance alone is not a release receipt. The helper also has a
cooperative poll budget, but an X protocol call can itself block beyond that
budget; an external process supervisor is still required for a hard caller
response bound. The current 110-test normal/`-O` suite verifies only parser,
presence/absence response handling, cooperative polling, resource-base
propagation, and the synthetic late-DOWN counterexample. No live X server was
available in this host, so no XRes disconnect fence or release transfer has
been qualified.

## Reproduction notes

The selected suite was run with Python 3.11.9 on Windows using the task's
temporary MCP dependencies. The exact commands were `python <runner>` and
`python -O <runner>`; the temporary runner selected the module list above and
excluded tests whose IDs contain `stdio`. Full logs were retained in the local
temporary directory, not committed as raw formal-run artifacts. `git diff
--check` passed after recording this note.
