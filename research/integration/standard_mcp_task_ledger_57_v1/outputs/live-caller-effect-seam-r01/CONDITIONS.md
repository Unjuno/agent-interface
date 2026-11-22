# R01 run conditions

Commands were run from `research/integration/standard_mcp_task_ledger_57_v1`:

- `python -m unittest test_effect_receipt_handoff_v1 test_recorded_comparison_adapter_v1 test_comparison_measurement_v1 -v`
- `python -O -m unittest test_effect_receipt_handoff_v1 test_recorded_comparison_adapter_v1 test_comparison_measurement_v1 -v`

Interpreter: Windows CPython 3.11.9. `PYTHONPATH` included repository root and this integration package. `TEMP`/`TMP` used `C:\Users\user\AppData\Local\Temp`.

The repository `runtime.cli_v1.mcp_relay.Relay` was exercised with a stub MCP client that returned fixed fixture bodies. The provider, MCP server, owner lifecycle receipt, observations, and scorer remained synthetic. No OS GUI, external provider, MAP01, Docker, or WSLc was used. Captures were regenerated with `capture_raw_local.py`; hashes are in `SHA256SUMS`.
