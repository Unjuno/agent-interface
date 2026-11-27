# Current-main Docker/Linux MCP worker-entry R02

**Disposition: scoped test-candidate pass; no live product gate closed.**

## Baseline and controlled change

- Frozen base: `a9bb375a09a03ca6129844053cc56910ad96efdf`.
- Prior R01 retained a combined optimized failure at the exact 2 s worker-entry wait, while the same case and modules passed in isolation. R01 artifacts remain unchanged; its post-merge diagnostics are copied into this packet.
- Existing Docker image: `issue57-calc-appserver-r88:local`, `sha256:a3b2b4cd54ca731a86f8d2ba16f1eb833220122c60bfafbdb048e5ad39e50056`, CPython 3.11.2.
- Runtime tree is unchanged from baseline. Only `runtime/cli_v1/test_mcp_server.py` differs: async test notifications use `asyncio.Event` and loop-threadsafe callbacks instead of `asyncio.to_thread(event.wait, 2)`. The two-second bound and production code are unchanged.
- Linux Docker, source mounted read-only, `--network none`, ephemeral containers. No model/provider/GUI/game/WSLc actions.

## Results

- Focused worker-entry case: 1/1 normal and 1/1 `-O` passed; raw first run retained.
- Complete `test_mcp_server` + `test_mcp_guarded`: 87/87 normal and 87/87 `-O` passed on an explicit `/usr/bin/python3` entrypoint; both captured container exit codes are 0.
- Initial wrapper-captured full-run logs are preserved as `combined-*`; the later explicit-entrypoint captures are `captured-*`. The latter provide definitive exit status and test summary.

## Interpretation and limits

The candidate removes a test-side wait from the same default executor used by worker dispatch and restores the combined optimized suite in this finite run. This is evidence for the executor-contention hypothesis, not a repeated reliability estimate. Preserve R01's failure. No runtime product code changed; this does not demonstrate real input, task effect, provider accounting, expiry recovery, efficiency, MAP01, Research Preview graduation, or distributable-runtime acceptance.

See `CONDITIONS.md`, `source_hashes.json`, `result.json`, and `SHA256SUMS`; raw output is in `raw/`.
