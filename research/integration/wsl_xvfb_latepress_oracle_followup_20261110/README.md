# Xvfb late-press recovery and custody follow-up (preregistered)

## Status and source freeze

Frozen before any follow-up input trial. It follows the separate
[release/autorepeat frontier](../wsl_xvfb_autorepeat_release_frontier_20261110/README.md),
which is retained unchanged. This successor adds a diagnostic-only mode to the
existing test harness: a nonneutral immediate release readback is recorded as a
failure but does not abort before the already-configured delayed-request horizon
and independent effect oracles. The default test behavior is unchanged. It also
records timestamps and key/button values passed through the owner's input
obligation publisher. Test source is frozen at
`6c049f504b8d0643fb946c4798e8bc3226218f38`; no production runtime behavior changes.

Execution image: cached `agent-interface-xvfb-mcp:late-input-r19`, image ID
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`.
Network disabled; source mounted read-only; `/tmp` is private tmpfs; only the
new per-attempt output mount is writable.

## Question and hypothesis

For the 100/250 ms cells, the previous fresh trials showed `a=true,b=false`
before cancellation, then `a=false,b=true` at the immediate independent
readback for both standard and prestarted cleanup. The integration test stopped
there, so it did not retain old-task horizon counts or fresh-task contamination.
The cancellation result correctly remained UNKNOWN with
`late_server_request_possible=true` and replay denied.

Does the delayed old `b` press remain active through the bounded observation
horizon, change the exact old-task effect count, or contaminate a fresh target
task? Does the child-side prepress publisher actually record `a` before the
XTEST event even when the parent's post-retirement shared-state snapshot is
empty?

## Frozen design

- A = standard guarded caller; B = prestarted cancellation supervisor.
- Delayed XTEST request time values: 100 and 250 ms.
- Two replicates per arm/delay, fixed order:
  `A100, B100, B250, A250, A250r, B250r, B100r, A100r`.
- Fresh private Xvfb and process for every trial, same cached digest-pinned
  image, same source, 1 s cancel-ACK withholding, and same cancel/transaction/
  terminal bounds as the parent study.
- `AGENT_INTERFACE_MCP_XVFB_CONTINUE_AFTER_NONNEUTRAL_RELEASE=1` retains the
  early nonneutral state and continues only through the existing independent
  old-task horizon, fresh-target effect oracle, terminal receipt, and fixture
  cleanup. The independent task oracle still scores nonneutral release as
  failure; runtime receipts remain UNKNOWN. This flag is off by default.
- `AGENT_INTERFACE_MCP_XVFB_OBLIGATION_PUBLISHER_TRACE` points to a new
  per-attempt JSONL file. Each publisher invocation records child PID,
  monotonic start/completion, key map, and buttons. Existing raw input event,
  sync, cancel, shared-state snapshot, and release readback timestamps are
  retained to reconcile order. The trace is observational and does not write
  the parent's RawArray directly.
- Primary endpoints: delayed `b` key state at horizon, old-task independent
  exact effect count, fresh-task exact effect count, and post-cancel publisher
  trace versus the parent's retired-child shared-state receipt.
- Continue all scheduled cells after a counterexample only when the JSON report
  exists, fixture cleanup is neutral, and the owned Xvfb exits. Stop on missing
  report, failed final cleanup, or live Xvfb. No retries or replacement cells.

## Decision and limits

Treat the initial readback mismatch as a failure even when later release or
fixture cleanup succeeds. The publisher trace can locate whether the child
called the publisher; it cannot by itself prove what bytes the parent later
read from shared memory. A persistent `b` at horizon or a changed effect count
is a bounded Xvfb counterexample, not proof of production GUI frequency. The
test injects XTEST delay into one request; it does not establish a general
maximum late-request latency. No WSLc, live GUI, MAP01, model/provider,
efficiency, or project-wide reliability claim is available.

## Execution

The runner uses the existing cached Xvfb/MCP image by digest, network disabled,
read-only source, and a new output directory. It executes each frozen cell
once, retaining raw JSON, publisher JSONL, screenshots, stdout/stderr, exits,
Xvfb logs, and setup records. A SHA-256 manifest is added after execution.
