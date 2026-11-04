# File-spool to public-MCP Calc composition (2026-11-04)

## Purpose and result

This offline integration check replaces the successful Calc generation's in-process planner with the existing `FileSpoolPlanner` request/receipt boundary. A synthetic host worker claims the image-bound spool request, records `started` and `completed` receipts plus a matching App Server protocol slice, and returns the supplied registered Calc arguments. The `RecordedPublicMcpCaller` then dispatches through the public MCP Relay into the existing Fake X Calc owner and independent FODS verifier.

All four runs passed: Windows Python 3.11.9 and pinned Docker, each in normal and optimized mode. Each run retained one completed spool request, eight total model attempts (five synthetic completed, one timeout, one malformed, one cancelled), 38 public MCP calls, and an independent FODS score of A1=24680 / A2=13579. The joined ledger correctly reports usage `incomplete` and token totals null because failed/partial attempts do not provide full usage. No usage is treated as zero.

The compiled Calc call itself ends `SAFE_YIELD/effect_unavailable` after two transitions, with verified releases. The separate parent verifier then joins the registered Save, exact artifact, and exit evidence and returns `task_success=true`. This distinction remains intact. Wrong, unknown, no-match and ambiguous post-input cases each stop after one transition, verify release, keep task success unknown, and deny replay.

## Conditions and evidence

- Base main: `76e5369f974484682da4d7699ca11637a60b40c9`.
- Test source SHA-256: `67ee60121dd6eb3415fa353b9bdc2844ab0d843713c477998382e2883bf95698`.
- Test: `test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score`.
- Windows: Python 3.11.9; no external provider/API call.
- Docker: Engine 29.8.1; `agent-interface-xvfb-mcp:late-input-r19`, image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, Linux/amd64; network disabled; source mounted read-only; 2 CPUs, 4 GiB memory and swap, 256 PIDs; writable evidence mount.
- `windows-output.txt`, `windows-opt-output.txt`, `docker-output.txt`, and `docker-opt-output.txt` retain exact test output. The four `<run>.zip` archives contain each full run directory: provider ledger, provider-call bytes, App Server protocol, spool request and terminal receipts, Fake X runtime receipts, score, and boundary summary. Each archive contains a `SHA256SUMS.txt` for its members. The packet-level `SHA256SUMS.txt` hashes the README, commands, attempt disposition, test output files, and archives.
- Test durations: Windows 24.153 s normal / 22.886 s optimized; Docker 10.593 s normal / 10.551 s optimized. These are test-process durations only; do not interpret as model or route speed comparisons.

## Failure during construction

The first Windows invocation before evidence capture failed before planner start because `file-spool/` was created without its missing parent directory. The outer test's final release assertion then saw `release_confirmed=null` because no input had been dispatched. The fixture now creates the spool root with `parents=True`. The corrected executions above all pass; the initial setup failure is excluded from pass counts. No safety assertion was weakened.

## Limits and disposition

The planner and host worker are synthetic: the worker echoes supplied arguments. The Fake X owner and FODS scorer are deterministic fixtures. This verifies composition of the existing file-spool, App Server protocol journal, attempt recorder, allowed-method public caller, public MCP Calc profile, release receipts and independent scorer for this fixture. It does not establish a real provider turn, provider-side retry accounting, live Calc GUI behavior, an efficiency comparison, WSLc, MAP01, or long-duration Docker stability. Keep Issue #57 open.
