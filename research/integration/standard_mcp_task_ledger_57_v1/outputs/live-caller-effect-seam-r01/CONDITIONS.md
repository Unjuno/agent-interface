# R01 run conditions

Commands were run from `research/integration/standard_mcp_task_ledger_57_v1`:

- `python -m unittest test_effect_receipt_handoff_v1 -v`
- `python -O -m unittest test_effect_receipt_handoff_v1 -v`
- `python -m unittest test_effect_receipt_handoff_v1 test_recorded_comparison_adapter_v1 test_comparison_measurement_v1 -v`
- `python -O -m unittest test_effect_receipt_handoff_v1 test_recorded_comparison_adapter_v1 test_comparison_measurement_v1 -v`

Interpreter: Windows CPython 3.11.9. `PYTHONPATH` included repository root and this integration package. `TEMP`/`TMP` used `C:\Users\user\AppData\Local\Temp`.
