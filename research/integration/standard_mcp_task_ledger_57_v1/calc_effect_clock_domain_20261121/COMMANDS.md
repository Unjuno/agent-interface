# Reproduction commands

Run from the repository root on Windows CPython 3.11.9. The composition selector runs from `research/integration/standard_mcp_task_ledger_57_v1` with absolute repository and evidence paths in `PYTHONPATH`. The packet-local `.gitattributes` keeps retained raw output bytes unchanged across Git checkouts. Source-code SHA-256 values in `conditions.json` and `SHA256SUMS` normalize source files to UTF-8/LF before hashing.

```powershell
python -m unittest runtime.core_v1.test_compiled_gui -v
python -O -m unittest runtime.core_v1.test_compiled_gui -v
python -m unittest runtime.guarded_x11_v1.test_calc_task_artifact_v1 -v
python -O -m unittest runtime.guarded_x11_v1.test_calc_task_artifact_v1 -v
$repo = (Get-Location).Path
$pkg = Join-Path $repo 'research/integration/standard_mcp_task_ledger_57_v1'
$env:PYTHONPATH = "$repo;$pkg"
Push-Location $pkg
python -m unittest test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score -v
python -O -m unittest test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score -v
Pop-Location
```

The final pinned-Docker command used `docker run --rm --pull=never --network none --cpus 2 --memory 4g --memory-swap 4g --pids-limit 256 --init`, mounted the candidate at `/workspace:ro`, and mounted this packet's `raw/` directory read/write at `/evidence`. It set `PYTHONPATH=/workspace:/workspace/research/integration/standard_mcp_task_ledger_57_v1` and ran from `/workspace/research/integration/standard_mcp_task_ledger_57_v1` in `agent-interface-xvfb-mcp:late-input-r19`.

The final Docker composition selector ran separately in normal and optimized mode; outputs are `raw/final-docker-composition-normal.log` and `raw/final-docker-composition-optimized.log`. The separate nine-selector boundary group was the eight `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_*` selectors listed in `../calc_save_controller_receipt_order_20261121/COMMANDS.md`, plus `test_partial_input_cancel_accounting.PartialInputCancelAccountingTests.test_cancel_after_first_transition_is_joined_without_replay`. It ran with `python3 -m unittest ... -v` and `python3 -O -m unittest ... -v`; outputs are `raw/final-docker-boundaries-normal.log` and `raw/final-docker-boundaries-optimized.log`.

The diagnostic-only pre-fix clock trace used temporary stderr instrumentation at graph verification start/acceptance and profile save-request creation. That instrumentation was removed before fixed runs. Two earlier setup-failure logs remain under `raw/pre-fix` and are excluded from all pass counts.
