# Reproduction commands

All commands ran inside this base container invocation:

```sh
docker run --rm --pull=never --network none --cpus 2 --memory 4g \
  --memory-swap 4g --pids-limit 256 --init \
  --mount type=bind,source=<candidate-worktree>,target=/workspace,readonly \
  --workdir /workspace/research/integration/standard_mcp_task_ledger_57_v1 \
  -e PYTHONPATH=/workspace:/workspace/research/integration/standard_mcp_task_ledger_57_v1 \
  agent-interface-xvfb-mcp:late-input-r19 \
  python3 [-O] -m unittest <test-selector> -v
```

The `[-O]` portion is omitted for normal mode and supplied as `-O` for
optimized mode. The image was locally present and was not pulled. The source
mount was read-only; logs were written on a separate evidence mount.

Selectors:

- `runtime.guarded_x11_v1.test_calc_task_artifact_v1`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_runs_through_owned_mcp_and_releases`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_requires_window_lifecycle_at_startup`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_settles_once_after_low_confidence`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_stops_on_wrong_unknown_no_match_or_ambiguous_ocr`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_rejects_stale_review_after_model_wait`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_cancel_during_ocr_keeps_release_and_effect_unknown`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_cancel_after_first_transition_keeps_effect_unknown`
- `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_registered_calc_profile_refuses_changed_process_generation`
- `test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score`
- `test_partial_input_cancel_accounting.PartialInputCancelAccountingTests.test_cancel_after_first_transition_is_joined_without_replay`

Each selector or group ran once normally and once under `-O`. Exact raw logs
are in `raw/`.
