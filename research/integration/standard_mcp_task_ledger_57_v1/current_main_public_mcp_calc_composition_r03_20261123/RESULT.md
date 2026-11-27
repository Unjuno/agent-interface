# Issue #57 current-main public MCP/Calc composition R03

## Outcome

**PASS_SYNTHETIC_COMPOSITION_ON_CURRENT_MAIN.** On Windows 11 with CPython
3.11.9, the frozen selector
`ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score`
passed 1/1 in a fresh normal process (22.106 s) and 1/1 under `-O` (29.879 s).
Both exit codes are 0. Raw stdout, stderr, and exit codes are retained.

The first normal and optimized invocations failed before executing the test
because the test directory was absent from `sys.path`. Those setup failures are
retained in `setup-failure-invocation-01/`. The corrected invocation added only
the repository's test directory to `PYTHONPATH`; the frozen selector and pass
condition did not change.

## Interpretation

This recertifies the existing Fake App Server, Fake X, public-MCP, Calc-profile,
and independent FODS-score composition on main `066d70435fe19d0dc2690bc01a114e0912b20f87`.
It is local synthetic coverage only. It does not establish live provider
accounting, a real UI task, eligible caller-attributed task success, recovery
reliability, efficiency, MAP01, or Research Preview graduation. The separate
R06 offline ProspectiveRun packet's pinned source hashes still match this main,
so its 18-assignment synthetic result was reused without rerunning it.

## Reproduction

From the repository root on Windows, set `PYTHONPATH` to
`research/integration/standard_mcp_task_ledger_57_v1` and run:

```text
python -B -m unittest test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score -v
python -B -O -m unittest test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score -v
```

See [CONDITIONS.md](CONDITIONS.md) for the frozen source hashes and setup
failure; `SHA256SUMS` covers the complete retained packet except itself.
