# Integration plan

Updated 2026-10-15. Promote evidence into one usable computer-control path.
Use [the work map](WORKER_WORK_MAP.md) to choose a finite contribution and
[the current interface guide](../runtime/USING_CURRENT_INTERFACE.md) to identify
the actual supported caller. Versioned research clients are not interchangeable.

## Integration sequence

| Stage | Integrate / verify | Exit evidence |
|---|---|---|
| 1. Source and caller | Trace observation → target binding → admission → input → release in the exact selected source. Reconcile related PRs and dirty candidate work before editing shared paths. | Source identity, actual call chain, focused regression and specific unresolved boundary. |
| 2. Authority and faults | Preserve original deadlines and cancellation, reject stale target evidence, keep release available. Separate a bounded caller response from physical release. | Composed key/button controls and verified/unknown release receipts under the named faults. |
| 3. Observation and effect | Bind fresh observations to each decision; preserve critical events and distinguish selection, local send and model receipt. Check application effect independently. | Raw retained evidence, meaningful effect predicate, failure/unknown classification and a finite recovery path. |
| 4. Live task | Run a fresh permitted allocation through the supported caller, with frozen conditions and bounded cleanup. | Independent task score, per-action/release evidence, raw/audit and retained failures. |
| 5. Efficiency and transfer | Compare matched baseline and integrated arms, then qualify another domain/platform. | Correctness plus calls/tokens, latency, resources, recovery/failure cost and uncertainty for all attempts. |

Offline composition, reference mapping and evidence checks can proceed while a
specific live resource is unavailable. A narrow blocked operation does not stop
all independent work. Do not substitute repeated construction for the eventual
live task and matched comparison.

## Current source-bound findings

- The scoped public Python bridge now has an explicit
  [process-identity option](../runtime/guarded_x11_v1/PROCESS_IDENTITY.md).
  It binds a Linux/XRes process digest to observations/aliases and rechecks it
  before new presses. Fake X composition covers refusal and prefix cleanup.
  Trusted local server/PID-namespace correspondence is a precondition; same-process
  resource reuse, post-read races, live qualification and bounded I/O remain open.
  Scoped MCP can explicitly select this option at startup; ordinary one-shot CLI,
  persistent-x11 and default Python/MCP configurations do not. The public MCP
  Fake X composition checks retained/delivered digest, stale-alias refusal and
  held-prefix cleanup. Live transport qualification is still required.

- [Public guarded X11](../runtime/guarded_x11_v1/README.md) now refuses a new
  key/button press when a returned lookup has consumed the original lease
  ([PR #8927](https://github.com/Unjuno/agent-interface/pull/8927)). It still uses
  cooperative enforcement; a stuck X11 call can delay release.
- [Public-path Fake X A01](../research/live_control/public_guard_blocking_a01_20261015/RESULT.md)
  now reproduces that boundary through actual dispatch/session/backend cleanup:
  blocked focus retains a modifier past expiry; blocked cleanup sync has fake
  empty state without a returned verified result. It adds no physical bound or
  cancellation result. Follow the [safety/evidence agenda](ideas/safety-control-agenda.md)
  toward independent cleanup with one input authority and late-reply fencing.
- The [single-writer Fake X separation spike](../research/live_control/fake_x_single_writer_spike_20261015/REPORT.md)
  now distinguishes observation blockage from stalled release send/readback.
  Separated observation permits cancellation/expiry cleanup in its finite
  schedules, with actual backend primitives and no second writer; input-transport
  blockage still prevents confirmation/progress. The actor/proof/clock are
  probe-owned. No public caller integration or physical bound follows from it.
  The opt-in [active target-query worker](../runtime/guarded_x11_v1/TARGET_QUERIES.md)
  now connects named focus/process reads through the actual Python bridge and
  standard guarded MCP, preserving source/generation/original deadline. Fake X
  checks cancellation/expiry cleanup while either query is blocked, discarded
  late replies, sticky transport failures and abandoned-open closure. This is
  a narrower integration than the probe's full observation loop; no physical
  bound is established.
  The [remaining-boundary characterization](../research/live_control/guarded_sync_boundaries_20261015/RESULT.md)
  confirms that capture, observation persistence and trusted callbacks inside an
  additional Python input guard, with only target-query isolation selected, can
  still hold CTRL after cancellation/expiry. All six fault cells release only after the
  harness resumes the blocked dependency; eventual cleanup is not bounded recovery.
  The further opt-in [active visual-check worker](../runtime/guarded_x11_v1/OBSERVATION_WORKER.md)
  separates those visual checks using its own read-only client. Actual Python
  bridge Fake X tests release the held prefix before the three dependencies
  resume, fence late publication, and reject changed source context/generation.
  Standard guarded MCP explicitly selects the mode; new-window review requests
  carry the current XID and resolve it on the reader's own connection. This is
  not all platform-I/O isolation: input transport/readback/close, idle observation,
  arbitrary caller behavior and physical release remain separate boundaries.
  [Actual stdio composition](../research/live_control/guarded_stdio_cancel_20261015/RESULT.md)
  now carries discovery/input/cancel/results/close through separate client/server
  processes with Fake X. Isolated cancel/expiry returns verified fake cleanup
  before capture resumes; query-only controls stay held/pending. This qualifies
  the named local transport path, not live X or provider/model receipt.
  [Explicit guarded recovery](../runtime/guarded_x11_v1/RECOVERY.md) now exposes
  the existing session's release/readback attempt through Python and standard
  guarded MCP. Fake X tests retain uncertain obligations, fence stale revision
  retries, serialize pending cleanup and require review/fresh aliases after
  verified release. One attempt is a policy bound, not a native-I/O time bound;
  independent task effect and live recovery remain unqualified.
  An explicit [guarded response wait budget](../runtime/cli_v1/WAIT_BUDGET.md)
  now lets that original input/recovery call return pending with one discoverable
  ID while retaining worker/cleanup custody. Fake X tests distinguish held send
  from fake-neutral unconfirmed sync/readback, queued work and executor-handle
  failures; real stdio checks pending-before-sync-resumption. This bounds only a
  cooperative await policy, never physical release or independent task effect.
  Explicit activation now requires a retained source with matching sequence,
  revision, target surface and host capture clock. Recovery-cleared history
  cannot be relabelled with the new revision. The actual Python/MCP Fake X path
  checks a fresh observation succeeds after recovery, while the old one refuses.
  A final local fence checks pinned context, selected process generation and the
  original expiry after WM-request preparation. This does not establish current
  pixels, atomic server acceptance, physical timing or independent task effect.
- [The executed #5 delivery composition](../research/live_control/idea5_delivery_boundary_a01_20261015/RESULT.md)
  separates retained raw, selected output and successful local flush. Its app and
  Executor boundaries are synthetic; it proves neither GUI task effect nor model receipt.
- [The idea execution agenda](ideas/visual-interface-agenda.md) maps #3/#5/#8 to
  existing mechanisms, concrete residuals and next tests. These Issues remain open.

## Completion and history

An archive merge, unit PASS or closed Issue is not integrated task success.
Keep [#57](https://github.com/Unjuno/agent-interface/issues/57),
[#59](https://github.com/Unjuno/agent-interface/issues/59) and
[#2789](https://github.com/Unjuno/agent-interface/issues/2789) scoped to their
unmet objectives; update the relevant parent rather than create management-only successors.

The previous 828-line plan/evidence chronology is preserved verbatim in
[INTEGRATION_HISTORY_20261015.md](INTEGRATION_HISTORY_20261015.md).
Read it for a selected result's provenance, not as a current allocation list.
