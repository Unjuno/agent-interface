# Fatal V39 cover failure after interrupt acknowledgement

The ordinary repair closes a confirmed remaining wait path in PR #8280.
After a fatal ordinary cover terminal, an interrupt RPC acknowledgement does
not mean that the pending planner turn has completed. The old controller
re-raised the cover failure inside a ThreadPoolExecutor context; its implicit
join could keep the existing failure handler waiting for the planner deadline.
The final controller requests interruption, then uses the existing transport
abort if the future is still pending, regardless of RPC success or failure.
A completion already observed during interruption skips abort. The original
cover error remains primary, and the diagnostic claims an abort only when the
adapter returns outcome=aborted.

## Source and actual validation

Starting PR head: `029064c797768183f63c79bbedbe3aca18f85dbb`, including its
peer interrupt-error follow-ups. Parent PR #8261 remains a separate dependency.
This continuation changes the controller, its existing terminal test module,
and one adapter docstring. It does not change the app-server client or import
the separate #8290 reap fix or #8298 response-admission fix.

Four new regression methods exercise ACK without completion, completion during
interrupt, close failure after waking the waiter, and the already-terminal
abort race. The first three added to the prior suite produce 11 passes and
2 failures on the old production source; the fourth exposes one false abort
diagnostic in repair v1. Both first failures are retained. Final affected
controller/renewal/cleanup/planner tests pass **101/101 normally and 101/101
under -O**, including 14 terminal-validation methods. Workspace-index tests
pass 22/22; the committed-tree checker reports 160 reachable namespaces;
changed Python compilation and diff-whitespace checks pass.

The broader focused suite's first invocation had 89 passing methods and one
loader error because its runner omitted the doom helper search path. It is
retained separately; the corrected command sets PYTHONPATH to the frozen
doom/live_control source directories. This was a test setup correction, not
a production repair.

Nine fresh ordinary real-Popen cells ran sequentially: six cells compared the
old source and repair v1 in ACK-only, ACK-plus-completion and RPC-error modes;
three new cells checked the final diagnostic refinement. No earlier frozen
allocation or prior result was rerun/overwritten. Source/harness snapshots and
actual subprocess exit receipts were recorded before and after each batch.

| Saved case | Old source | Final repaired source |
|---|---|---|
| Interrupt ACK, no completion | Needs one-second construction rescue | Existing abort wakes the pending future; no rescue |
| Interrupt ACK with racing completion | Cancelled, ineligible answer; no abort | Cancelled, ineligible answer; no abort |
| Interrupt RPC error | Existing abort; original failure retained | Same error handling; original failure retained |

All nine wrappers exit 0. Each cell preserves the fatal cover RuntimeError,
makes one synthetic session submit and no final action admission, and retires
its owned inert child, reader, watchdog, future, journal and process group.
The peer return code is -15 (intentional termination), not a natural success.
The baseline rescue is an explicit construction intervention; no full
90-second delay or shutdown worst-case bound was measured.

The independently implemented helper readback passes 42/42 checks on the
original six cells and 26/26 on the final three cells. Its initial three
auditor predicate/schema mistakes, all outputs, and corrected scripts remain
preserved and explained. Root's final saved-data checks pass 25/25. The final
source snapshot binds 82 exported files, including selected test definitions.
Helper review here is coauthor validation, not the required nonauthor quorum.

## Scope and limits

Host: macOS 27.0.1 arm64, CPython 3.12.14. The real client uses its default
Popen, pipes, reader thread and owned process group against an inert local
JSONL peer. No Codex service, provider, model, network, GUI, game, VM, container,
or physical input is used. The application session, observations and failure
cleanup-entry spy are synthetic. This verifies handler reachability and
transport retirement, not production physical-release or recovery behavior.

The code acts only after fatal ordinary-cover validation failure. Normal
policy invalidation/replanning is unchanged. A transport/OS close failure
before waking the waiter can still delay pool joining until the existing
planner deadline; the abort-fault regression deliberately wakes the waiter
before throwing, so it does not cover a stuck close. Interrupt request timeout,
blocked writes, EOF/reaping, provider cancellation, useful feedback, physical
release, threat response, gameplay and the full computer-control goal retain
their independent gates. No main application or external approval is claimed.

## Evidence

`MANIFEST.json` binds every member of `evidence.tar.xz`, with original and
published hashes for explicit local-path projections. The archive retains old
and final exact source snapshots, candidate code, peer/probe/runner source,
wire logs, traces, process identities, execution receipts, all unit logs,
initial failures, fixed-source metadata, and helper auditors/reviews.
Only task-directory and user-home prefixes are projected; original private
bytes are retained locally. Production/source export bytes are unchanged.
