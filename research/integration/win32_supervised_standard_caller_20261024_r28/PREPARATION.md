# R28 preparation record

The first input-free preflight stopped because this sparse worktree had not materialized the R25 predecessor packet. It created no fixture, session, or native input. After materializing the already committed R25 evidence, the second preflight passed all checks: frozen source and packet hashes, clean base commit, R27 raw/audit/report hashes and semantic PASS, R25 no-input refusal hashes and semantics, native Windows, and Python compilation. Both preflight outcomes are preserved in `preflight_attempts.json`.

Immediately before the trial, process inspection found no existing `fixture_app.py` or `runtime.cli_v1.mcp_server` process. The run will create one owned fixture and one stdio-MCP session.

The first post-run auditor returned 13/14 because its predecessor-chain predicate used R27-era field names that do not exist in the custom R28 preflight JSON. The full first audit is preserved in `audit_attempt1.json`. The predicate was corrected to read the equivalent R27/R25 integrity booleans emitted by R28 preflight; no experiment criterion or raw result changed. The packet hash was refreshed and input-free preflight plus frozen audit then passed.
