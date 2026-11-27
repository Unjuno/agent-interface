# Cross-generation recovery admission boundary (Xvfb, current main)

## Finding

The isolated Docker/Xvfb experiment finds a concrete recovery admission boundary. In XG06, the fresh target was focused and its new guarded session admitted before old-generation cleanup. Two old A presses reached that fresh target in each of three arms, contaminating it before its new C task. In XG07, the old target remained focused until an independent supervisor release/readback observed A/B up; only then was the fresh target focused and a session admitted. No old A/B event reached that target through the full horizon in three arms. Each C task produced exactly one independently read-back effect from a clean zero baseline.

The old operation remained `UNKNOWN`, with `release_confirmed=false` and `replay_allowed=false` in every arm. The separate supervisor receipt is an admission-policy signal in this test; it does not establish the old operation's task outcome or strengthen its API result. A product integration should therefore keep old and new generations distinct and gate new-target focus/admission on a verified neutral boundary without converting old UNKNOWN into success.

## Efficiency context

A separate current-main Docker/VizDoom route comparison across two frozen batches (12 matched pairs) measured compiled GUI plus the JSONL receipt journal at 101.22 on an inverse-latency index normalized to direct control = 100. Mean route latency was 864.119 ms compiled+JSONL versus 874.628 ms direct, a descriptive 1.20% reduction; the journal route won 10/12 pairs. Compiled GUI with per-receipt JSON files scored 95.07 and was slower in all 12 pairs. This measures a narrow one-action bridge/receipt-retention route, not end-to-end task completion, provider/model latency, token use, or general computer-control speed. See `../../../../../../../private-packets/docker_vizdoom_currentmain_retention_replication_20261029_r02/RESULT_R02_AND_COMBINED.md` for the paired breakdown.

## Evidence and limits

The frozen experiment packet is outside the source worktree at `../../../../../../../private-packets/docker_xvfb_crossgen_stale_input_currentmain_20261029_r07/`. Its `RESULT_XG07.md`, `ANALYSIS_XG07.json`, raw arm results, conditions, preregistration, invocation records and hash audits preserve the run. XG06 is in the adjacent `_r06` packet; the R05 harness-order failure is retained in `_r05`.

This was synthetic Linux/Xvfb, using the standard MCP caller, explicit cancellation and test-injected blocked X I/O. Three arms support a narrow within-setup finding. The run does not test production implementation of the admission barrier, lease-expiry-only recovery, native Win32/WSLc, GZDoom/MAP01, broad reliability or provider/model efficiency. Treat this as an integration requirement and a next-step design input, not as completion of live computer control.


## Product-path follow-up: orphan-recovery admission fence

A current-main source audit found a mismatch between the orphan-recovery contract and the new session's actual admission gate. `interface_recover_orphaned_input` returned `next_action_requires_fresh_generation=true`, but a fresh `OwnedWin32SessionOwner` had no prior local operation row, so its `OperationOwner` could admit the original target generation. An unsuccessful native recovery could likewise leave the fresh owner able to admit a different generation. The per-session active-operation check does not cover either case after restart.

The implementation now keeps a local recovery fence in `OwnedWin32SessionOwner`:

- once a valid orphan-recovery call reaches the supervisor, no action is admitted while its result is unresolved or unknown;
- after verified recovery, the source target generation remains fenced for the lifetime of that session;
- a new action may be admitted only after the caller binds a different current target generation;
- the source action remains UNKNOWN and replay stays denied.

The public MCP regression calls `interface_recover_orphaned_input` and then attempts `interface_dispatch` against the same generation. The dispatch is refused before producer start (`operation_invoked=false`, `input_dispatched=false`). The adapter tests also verify that verified recovery allows a different generation and unknown recovery blocks it.

Validation was run on the current worktree based on `568393122b2a7345e223d44b9f28f1d3a19bf76c` (base runtime tree `07f77dfd9c6a17e84bffda6f0753fed6635e3ccb`): 56 tests passed in normal Python and 56 passed with `python -O`; `git diff --check` passed. Commands and raw console output are retained in `VALIDATION_R01.txt`.

This is a **session-local implementation fix**. It does not coordinate separate MCP server processes that never call `interface_recover_orphaned_input`; such a process can still create an independent empty owner. Therefore it does not yet implement the cross-session admission barrier supported by the XG06/XG07 contrast. A host-shared, resource-side fence is still needed before claiming that stale input cannot contaminate a new session across independent server processes. No native Win32 live recovery run was performed in this implementation pass.
