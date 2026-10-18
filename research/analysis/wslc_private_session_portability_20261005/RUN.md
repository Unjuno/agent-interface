# Attempt record

- Branch/base: `migration/wslc-isolated-session-smoke-20261005` / `0db00a564daff64e47fd6931954ace0f71ab8f2b`.
- Runtime metadata observed: WSL `3.0.1.0`; Ubuntu WSL2; `wslc.exe` at `C:\Program Files\WSL\wslc.exe`. Docker executable absent.
- Exact command: `wslc.exe system session enter '[REDACTED_USER_TEMP_PATH]' --name ai-wslc-d3484fa5c43d44049228762c850c8257`.
- Result: exit 1 after 1.398 seconds, before session shell. Stderr is retained in `results/session-enter.stderr.txt` as rendered by the terminal tool (terminal control sequences are not stored); stdout had no human-readable text.
- Candidate/container invocations: 0. Image calls/pulls: 0. Auditor invocations: 0.
- Post-check: proposed storage path absent; zero live `wslc.exe` clients; no global/session/container inventory or shared/default-session command was issued.
- CLI help only (non-state-changing) showed `enter <storage-path> --name <name>` and `--session` support. The failed outcome leaves the actual storage/session prerequisite unresolved. No retry.
- **Coordination deviation:** after this invocation, reading the latest Issue #7970 comments revealed an explicit hold on all WSLc management/RPC calls until ownership and exclusive-lane gates across #6389/#6693/#7924/#7970 are cleared. The `session enter` attempt therefore crossed that gate even though it failed and post-checks saw no session path or live client. Disclosed on #7970 and #7924; no further WSLc operation without clearance.

See `PROTOCOL.md` and `STOP.md` for the freeze, exact classification and limitations.
