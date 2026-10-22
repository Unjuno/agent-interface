# Public MCP composition evidence — 2026-10-20

## Scope and provenance

This packet preserves one local run of both tests in
`test_mcp_endpoint_composition.py` at source commit
`34a875dbc21bc808359c81f57d0704cc15e2518c` on Windows with Python 3.11.9.
The tests use a deterministic Fake X owner, a fake asynchronous provider
callback, and the public `interface_guarded_compiled` FastMCP tool. They are
reproducible integration tests, not a formal or live GUI experiment. No real
provider, model call, WSLc/Docker allocation, or physical input was used.

The retained tree contains 101 files / 144,977 bytes from the two run roots.
[`SHA256SUMS`](SHA256SUMS) hashes every captured file. The SHA-256 of that
manifest is `4ae81f93619d0cd65d5b50d3ac08cdb16bdd280e06d87267132aa65f1266de08`.
The exact request/response bytes, event journals, owner receipts, PNGs, and
scorer-state bytes are kept below each `provider-mcp-*/run/` directory.

## Success cell

`provider-mcp-success/run/ledger/attempts.jsonl` records one completed fake
provider attempt, one joined public-MCP tool call, and one terminal pixel score.
The fake usage is supplied by the test callback (42 input, 12 output tokens); it
is not billed or measured model usage. The method receipt records one completed
transition and a verified neutral release in this Fake X fixture. The public
MCP result still has `task_success: null` and replay is denied.

The separate test oracle decodes the child-written initial and final BGRX
state. Pixel (1,1) changes from non-red to red. The retained initial raw state
hash is `fd07dbd471407c82423fad55d608df20b0cc3ee96d37d3473ef2cb6adde87af3`;
the final/score state hash is
`8d3e061570e62d5bc4055cc37a7e08e87f9ed47bf41ae8c01dd38b7467e95e45`.
The score is independent of the MCP result field, but this test cannot prove
independence from a production scorer or external provider logs.

## Stale-generation refusal cell

`provider-mcp-stale-generation/run/ledger/attempts.jsonl` records one completed
fake provider attempt, one joined public-MCP call, and a terminal false score.
The test changes the observed process generation after the provider response
and before the compiled MCP call. The public owner retains `SAFE_YIELD` /
`execution_refused`, zero completed transitions, `input_dispatched: false`,
and no replay. No final-state side-channel file was written; the score uses the
unchanged initial state bytes (SHA-256
`fd07dbd471407c82423fad55d608df20b0cc3ee96d37d3473ef2cb6adde87af3`). The MCP
result keeps `task_success: null`. This is evidence for this synthetic
provider-to-caller generation race only.

The failed cell does not prove any release action or cleanup bound: no input
was dispatched, and the method receipt's release field is not affirmative.
The successful cell's Fake X release receipt does not establish native or
physical release.

## Reproduction

Run from the repository root with a new, empty evidence destination. The
preservation helper refuses to overwrite an existing run directory.

```powershell
$runId = [guid]::NewGuid().ToString('N')
$env:AGENT_INTERFACE_FAKE_X_EVIDENCE = "research/integration/standard_mcp_task_ledger_57_v1/captures/$runId"
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p test_mcp_endpoint_composition.py -v
```

This capture was run in normal Python once to save both raw trees. The full
29-test ledger/recorder/composition suite passes in normal and optimized Python;
the 33-test owned-process suite also passes in both modes. Tests verify local
contracts only. This packet does not establish provider-log completeness,
blocked-I/O release, finite post-fault recovery, live task success, or matched
efficiency/reliability.
