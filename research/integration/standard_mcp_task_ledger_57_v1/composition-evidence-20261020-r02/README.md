# Public MCP composition evidence r02 — 2026-10-20

## Provenance and conditions

This is one local run of the ledger/composition suite from source commit
`1d4a0c45ac2c25887158698cf85387911a9182e9` on Windows/Python 3.11.9. The
stale-generation cell now holds a fake asynchronous provider response behind
an `asyncio.Event`. After the request is frozen and the provider attempt has
started, the test changes the fake target generation, then releases the
response. The unchanged generated request is dispatched through the standard
public `interface_guarded_compiled` MCP method. This is a deterministic Fake X
composition test, not a real provider/model, GUI, allocation, or efficiency
experiment.

[`SHA256SUMS`](SHA256SUMS) covers all 101 files / 144,977 bytes in both `run/`
trees. Manifest SHA-256:
`2d0e6acaaa8e76eacae2e71515858aa02b59fb027cd0ed6b8db73473c9ed751b`.

## Result

The recorded provider attempt starts at `188335015000000` and ends at
`188335140000000` ns; the public-MCP call starts at `188335218000000` ns. The
journal therefore orders the delayed fake provider completion before the MCP
dispatch. The target generation changes while the provider callback is
explicitly waiting.

The public caller refuses the stale target with zero completed transitions and
no input dispatch. The separate Fake X state oracle reports `false` against
unchanged initial state. The MCP result keeps `task_success: null` and replay is
denied. Since no input was dispatched, this does not demonstrate a release
action or release bound. It does not show physical/native release, blocked
platform-I/O recovery, or live task success.

The 42 input / 12 output token values are supplied by the fake callback; they
are not measured or billed model usage. The event timestamps are recorder
monotonic values for this one synthetic test and do not estimate model latency.

## Reproduction

From repository root, use a new empty evidence destination; the helper refuses
to overwrite an existing run:

```powershell
$env:AGENT_INTERFACE_FAKE_X_EVIDENCE = "research/integration/standard_mcp_task_ledger_57_v1/captures/<new-id>"
python -m unittest discover -s research/integration/standard_mcp_task_ledger_57_v1 -p 'test_*.py'
```

The destination contains separate `provider-mcp-success` and
`provider-mcp-stale-generation` run directories. No real provider or WSLc/Docker
operation is performed.
