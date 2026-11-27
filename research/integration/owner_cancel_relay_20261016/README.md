# Independent cancellation and original-lease release cause

2026-10-16; parent [#59](https://github.com/Unjuno/agent-interface/issues/59).
Adopt the explicit [cancellation lane API](../../live_control/INPUT_OWNER_CANCEL_V4.md)
at immutable code96a774e64ad9cdf20e435b606055d047a6496c95. It repairs the
[metadata-only composition counterexample](../owned_owner_executor_boundary_20261016/README.md)
without claiming standard backend selection or completing computer control.

## Conditions and result

Windows, Python3.13.14; Pillow12.2.0, numpy2.3.4, python-xlib0.33, MCP1.30.0.
Only Fake X display/query/capture/input, real private sockets, owned Python
threads and spawned Python processes. No WSL/container, game, provider/model or
real display/input. These are ordinary local construction regressions, not a
formal allocation or replay. No physical release-time bound is inferred.

`final-normal.*` and `final-optimized.*` are original final-r3 output from the
guarded `check_owner_cancel_v4.py.txt`: each70 methods, zero failures/errors/skips,
11 cancellation rows,3 original counterexample rows,13 process rows and26 RPC
regression rows. Each parent pins51 loaded source paths; accepted child startup
pins its loaded subset and mode0/1. `source-index.json` plus54 LF-normalized
source paths in nonexecuting content-addressed text preserve their union. Original
file/export bytes remain separately preserved; normalization applies only to
source pins. Future current-source changes do not silently reinterpret this run.

| Cell | Discriminating result |
|---|---|
| actual selected backend/Executor, worker paused after down | Separate cancel lane releases while worker is still paused; exact source/intent-bound cause is recorded on original parent Lease and emitted as input_released before resume. |
| actual ordinary down RPC in flight | Test fixture pauses after native down, before ordinary reply; separate control still returns verified/applied release cause and telemetry before reply resumes. This pauses service reply, not a native X11 call. |
| blocked Fake release | First bounded control result says accepted but release unverified; service remains alive and press-only. Later release does not rewrite that first result or attach a new parent cause. Eventual teardown is a separate result. |
| control EOF / wrong service generation | Known lease is cancelled, key released, future down refused; saved control error yields unverified service recovery and nonzero owned-process exit. |
| cancel before ordinary registration | Registry retains cancellation; later stale sender cannot clear it or create a press. No release of a never-admitted press is invented. |
| registry / cause validation | Original source change and retired registry refuse; wrong token/deadline/source/reason and contradictory release state refuse. Valid unverified cause remains false. |
| parent binding changes while reply gated | Source/deadline/token changes refuse cause application, remain unverified and do not write old-source cause on changed parent Lease. |
| cleanup / interrupted watcher start | All channels close despite secondary shutdown interruption. A real owned local thread started immediately before KeyboardInterrupt remains tracked, stopped and joined; primary exception survives. |
| same-suite metadata-only baseline | Local owner releases during paused worker; remote owner has press-only trace/no parent cause during250ms diagnostic window and only releases after resume. Normal remote completion still succeeds. |

The new positive composition installs `watch(original_lease)` explicitly before
actual backend input in the test; it still uses a test owner_id metadata shim.
No production backend adapter or default selection is hidden in that fixture.
Fake edge callback logging includes fsync and is not production latency evidence.
Original ten-second deadlines and saved edge/cancel/observation times distinguish
the positive release from expiry; the baseline250ms is diagnostic, not a relaxed
deadline or performance claim. Native blocked I/O can still prevent a physical
release-time guarantee; a second channel cannot unblock the native owner thread.

The first control outcome is deliberately immutable. A missing/unverified cause
can coexist with later verified service cleanup. The upcoming backend custody
adapter must preserve the first unresolved obligation and refuse replacement
authority; later service cleanup alone must not clear it.

## Saved readback and first failures

`read_saved.py` imports no runtime/process tools. It reads saved bytes and frozen
sources, verifies row inventory, service/owner/startup lineage, request ordering,
original source/deadline, cancellation cause/parent application, release before
worker resume, control-to-recovery-to-finish hashes, owned exit and the same-suite
negative baseline. Thirteen altered records per mode are rejected. Selected old
regression rows are retained and inventoried; this reader does not replace their
complete semantic audits. `readback.json` is its original saved output.
`pid-absence.json` checks the36 named owned child PIDs from the final suite only,
all absent at that time. No broad process scan/kill or PID-reuse proof.

`exploratory/` preserves first red/source/outcomes and earlier passing revisions:
absent implementation; one initial expectation error (a valid unverified cause
must remain false rather than be rejected); paired-channel cleanup assertion;
three gated parent-binding assertions; and interrupted watcher-start assertion.
Earlier68/69-method final revisions have older pins and are not promoted to final
code qualification. First failures are not deleted or counted as passing. Expected
injected child exit1 tracebacks in final stderr are not unittest failures.
`review.txt` records bounded review and the repaired findings. CPython Thread._started
is an explicit interrupted-start dependency; other interpreter support is unknown.
SHA256SUMS.txt covers all packet members except itself.

## Adoption and next finite work

Use explicit cancellation-enabled service only where caller owns the target and
installs watch before input. Cancellation acceptance is not release confirmation,
new authority or task success. Next under#59, implement the selected backend/
Executor adapter owning both clients, source binding, first-result failure custody,
cause/publication errors and finite shutdown. Qualify standard controller/session
death after that integration. Real display/input, platform transfer, independent
task effects and matched efficiency/reliability remain open. Continue existing
Issues and retain ideas/failed evidence; no new coordination Issue, allocation or
reviewer count is introduced.
