# Current-main late queued operation recheck

Date: 2026-11-21  
Frozen HEAD: `3db800fe9de4f08660f1832f6d790ff4a2ea43b2` (PR #10369 merged into main)  
Host: Windows, CPython 3.11.9  
Scope: one existing synthetic public guarded-X11 cancellation regression, rerun in normal and optimized Python. No runtime behavior changed.

## Experiment and result

The exact existing test is `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_standard_cancel_keeps_unknown_after_release_readback_then_late_down`. It blocks owner I/O after an old-owner `KeyPress` has entered its connection queue. A supervised disconnect receipt identifies the retired owner PID; a separate cleanup client reports a verified empty key/button state. The test then applies the queued old-owner press and observes keycode 1 down.

Both normal and `-O` runs pass 1/1 (1.058 s and 2.093 s). The caller retains `cleanup_status=UNKNOWN`, `release_confirmed=false`, `late_server_request_possible=true`, `task_success=null`, and `replay_allowed=false`. This is a positive adversarial control for the UNKNOWN contract: empty post-retirement readback can precede a delayed queued input. It does **not** pass late-operation exclusion or recovery reliability.

## Reproduction

```powershell
$env:PYTHONPATH='runtime/cli_v1;runtime/provider'
python -m unittest -v runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_standard_cancel_keeps_unknown_after_release_readback_then_late_down
python -O -m unittest -v runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_standard_cancel_keeps_unknown_after_release_readback_then_late_down
```

The frozen source hash, exact conditions, raw output logs, and log hashes are in `conditions.json` and `SHA256SUMS.txt`. This is a synthetic Fake-X sequence; it proves the regression behavior and caller accounting, not native X server timing or arbitrary application task effects. The next gate needs a separate old-generation delayed-operation horizon and a fresh-generation positive control.
