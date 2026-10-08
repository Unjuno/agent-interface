# One-shot STOP record — Issue #5260 r0

Allocation: `tk-first-char-focus-order-5260-r0-20260928-01`  
Frozen main: `c45e1947e498dce08abfb27e459e610054a0602e`  
Source branch: `research/tk-firstchar-focus-5260-r0-20260930-j7q2`  
Source checkpoint before input: `3f85701f312c930a75f6a60454b667c2eb408512`  
Source path: `research/integration/tk_focus_readiness_5260_r0_20260928/`

## Disposition

**STOP_PROVENANCE_OR_RUNNER.** One registered invocation produced 32 raw rows, but it did not expose the intended focus/readiness behavior. Do not interpret it as a scientific FAIL or PASS and do not retry/reuse this allocation.

The raw records show all 32 click coordinates as `(0,0)`; the target Entry geometry had not been resolved when the runner scheduled input. Across the 32 app records, no target KeyPress was observed and every final Entry value was empty. The raw audit reports 32 mismatched values and `checks=FAIL`. The runner source audit identifies the geometry capture in `click_and_type` before the Tk main loop has completed map/configure processing as the immediate harness defect. This is sufficient to explain why the intended target was not hit; causal claims about Tk focus ordering are not supported.

There is a second independent gate mismatch: the runner intentionally terminates each busy worker after a case, yielding process exit `-15`; the frozen auditor requires exit `0` for busy workers and therefore rejects all 16 loaded rows. No evidence was altered to make those checks pass.

The retained Xvfb log also records failure to bind its Unix socket listener and warns that `/tmp/.X11-unix` is not mode 1777. This prevents asserting private-display provenance. The Xvfb/Openbox setup logs are retained as a lossless archive.

## Execution record

Command: `wsl -d Ubuntu -- sh /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/.cache-memory-lab/focus5260/run_private.sh`

Environment: Ubuntu 24.04.4 on WSL2 x86_64; CPython 3.12.3; Tk 8.6; Xvfb `2:21.1.12-1ubuntu1.6`; Openbox `3.6.1-12build5`. Four auditor corruption controls passed before Xvfb startup. The 32 app processes exited 0. No Docker, user desktop, model/provider, network, or GPU was used.

After termination a read-only process listing showed a separate Xvfb on display :151 and Openbox. They were not this run's frozen display :196 and were left untouched; no cleanup or signal was sent to them.

## Preserved evidence

- `raw.json.zip.b64`: base64-encoded ZIP containing the exact original `raw.json`; decoded ZIP SHA-256 `9cc9b7b3ad24d903ba23b280653faf9c6d33b2e41a3aeb873f99d825662071e3`. The uncompressed raw JSON is 60,935 bytes, SHA-256 `ae934766d424bd5617fd0f1de22b9a285d265b60f6381bc44a7dada24e39b6d6`.
- `audit.json`: exact independent audit output, 4,988 bytes, SHA-256 `13a3782e0b9dc59426e821204a7254c430557388095f71678d807c1774175474`. It contains 16 worker-exit errors, 32 mismatched input rows, and decision `STOP_PROVENANCE_OR_RUNNER`.
- `setup_logs.zip.b64`: base64-encoded Xvfb/Openbox logs; decoded ZIP SHA-256 `3e2f8c5ae012a8719a434fd51ec65563cac0df0c7224178a743289e6d4b0b372`.

## Next research step

Keep this allocation and its raw/audit records immutable. A successor may first correct the geometry/map barrier and worker-exit contract, then add a no-input Xvfb construction gate proving the display socket is private and cleanup is scoped. It must receive a new allocation/source freeze and fresh rows; this STOP is not to be replayed or relabeled. The independent #5134 OrbStack experiment remains separately gated by exact current-main owner and coordinator slot assignments.
