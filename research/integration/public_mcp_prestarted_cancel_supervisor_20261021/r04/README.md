# R04 — terminal cancellation archive and custody

## Result

The public-MCP owned-process, guarded, supervisor and XRes-fence suites passed
**106/106 tests in normal Python** and **106/106 under `-O`**. Normal runtime was
44.197 s; optimized runtime was 43.874 s. Exit codes, separate stdout/stderr,
frozen conditions and source hashes are retained in this directory.

The added public-caller check exercises both archive outcomes. After a
successful terminal cancellation, `interface_results` and a duplicate cancel
read the same operation ID/result from `cancellation.json`; the Fake X oracle
records one release. When writing `cancellation.json` is injected to fail, the
terminal receipt remains in memory, duplicate cancel returns the same operation
without starting a second cleanup, and the persistence failure is visible.
Both paths retain `release_confirmed=false`, `task_success=null`, cleanup
`UNKNOWN`, and replay denial.

The server now retains the full cancellation payload in memory only while an
operation is pending, or when its terminal archive failed. The existing
single-worker/one-owner path admits one live operation. A persistence failure
keeps that in-memory custody slot and blocks new cancellation admission. A
successful terminal write records a small archive marker and operation ID on
the call record; result retrieval reloads the durable per-call receipt.

## Reproduction

```powershell
python -B -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_xres_client_fence
python -B -O -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_xres_client_fence
```

## Limits

This is Windows/Python with deterministic Fake X. It does not exercise the
production X11 worker against Xlib or Xvfb, prove late queued-effect exclusion,
or qualify blocked-live-server release, task success, recovery, MAP01, physical
input, efficiency or reliability. Terminal receipt files remain under the
existing per-call artifact retention; this change bounds live in-memory
cancellation custody but does not set a disk-retention limit. No WSLc or Docker
allocation was used.
