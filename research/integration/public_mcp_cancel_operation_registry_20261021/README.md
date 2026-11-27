# Public MCP cancellation-operation retention and caller-bound probe

Status: local composition regression; source changes are uncommitted in the
`fix/primary-mint-sparse-currentmain-r01` worktree. This packet does not claim
that the prestarted supervisor exists or that a whole cancellation transaction
has a hard bound.

## Question

Can the owned standard MCP caller return a conservative pending receipt while
one cancellation remains in custody, keep the event loop responsive, make
duplicate requests share one operation ID and one cleanup attempt, and retain
the cancellation result separately from the original action result, including
after cancellation of the requesting coroutine?

## Conditions and execution

The frozen test matrix is in `conditions.json`; r01 source fingerprints are in
`source-hashes-at-run.txt`. The packet `SHA256SUMS` binds its retained
conditions and logs. It used local Windows CPython 3.11.9, public `create_server` MCP
composition, the repository Fake X owned-process fixture, and temporary local
directories. It used no WSL/WSLc, Docker, live X server, physical input, model,
or provider. The ordinary and optimized test logs are retained verbatim.

The two relevant tests are:

- `test_cancel_returns_unknown_when_separate_release_worker_blocks`: the
  separate release helper is blocked; the public cancel call must return
  `pending` in under 450 ms. The test also checks a sub-100 ms maximum heartbeat
  gap, stable duplicate operation ID, exactly one helper call, separate
  `interface_results` retention, and UNKNOWN/no-replay semantics.
- `test_cancel_request_cancellation_does_not_drop_owned_operation`: cancel the
  MCP request coroutine while the cancellation worker is held at a test gate;
  the same operation remains retrievable, completes UNKNOWN, and a later
  duplicate returns that operation ID without a second owner call.

## Result

The first run is retained at this directory root; subsequent receipt and
worker-interruption checks are in [`r02/`](r02/README.md),
[`r03/`](r03/README.md), and [`r04/`](r04/README.md). The current r04 focused
`runtime.cli_v1.test_mcp_owned_process` and `runtime.cli_v1.test_mcp_guarded`
suites passed 77/77 in normal Python and 77/77 under `-O`. The original action result remained distinct from the additive
cancellation subrecord; cancellation receipts were also retained as
`cancellation.json`. The blocked-release case observed `release_confirmed=false`,
`cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`.

The 450 ms value is only a local test threshold for this Fake X composition.
The measured release worker and XRes disconnect are fixture-controlled, and
the second case replaces the owner cancellation method with a controlled gate.
No run established a real X11 release, a full transaction deadline, a
prestarted helper process, target-generation fencing inside that helper,
bounded recovery, an independent task effect, MAP01, efficiency, or reliability.
Keep #17 and #57 open. This result does not authorize or consume WSLc allocation.

## Reproduction

From the repository root:

```powershell
python -B -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded
python -B -O -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded
```

Exit codes are in `normal.exit` and `optimized.exit`; stdout/stderr are retained
as separate files. Root `SHA256SUMS` binds the r01 output and conditions;
`source-hashes-at-run.txt` preserves its source fingerprints. The current r04
manifest binds the latest run's exact source and result files.
