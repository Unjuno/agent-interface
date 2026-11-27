# Issue #57 Calc public-MCP composition evidence — r02

## Scope and source

Offline synthetic Fake X composition only. Base is current `origin/main` commit `5c862168fc4aaec47a42e5dfadcf9490881e87a8`. Run 01's exact working diff and file hashes are preserved as `source-diff-run-01.patch` and `source-freeze-run-01.json`. Run 02 uses `source-diff.patch` and `source-freeze.json`. No G10 raw artifact was edited or replayed.

## Run

Pinned test environment: Python 3.11.9 slim, `mcp==1.30.0`, `Pillow==10.2.0`, `numpy==1.26.4`, `python-xlib==0.33`; Docker network was used only to fetch test dependencies. Source was bind-mounted read-only; evidence output was mounted separately.

Command executed:

```sh
PYTHONPATH=/workspace python research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score
```

Both retained runs passed, 1 composed test each. The whole composition module also passed 12/12 in normal Python and 12/12 under `python -O` on the run-02 source state.

## Retained result

- Four provider attempts: one schema-preflight timeout retaining partial response bytes with unavailable usage, then three completed synthetic generations.
- Twenty-four public MCP tool-call receipts joined in the local ledger. The timeout generated no MCP tool call.
- Successful registered Calc profile run: neutral close verified release; independent FODS parser read A1=731 and A2=864. Graph `task_success` remains separate from independent task score.
- Wrong-result OCR and unknown-result OCR each preserved the one completed input transition, verified its release, stopped before Save with `SAFE_YIELD`, retained `task_success=null`, and denied replay.
- The all-attempt ledger is complete, but token totals and detailed usage totals are null with `usage_status=incomplete` because the timeout usage is unavailable.

See each run's `joined-ledger-summary.json`, `boundary-results.json`, provider request/response receipts, App Server protocol journal, and `raw-runtime/` for retained raw material. Run 02 includes explicit summaries of each negative OCR path and every provider attempt.

## Limits

The injected Fake Planner echoes supplied arguments and reports synthetic usage. The owner and application state are Fake X; there was no live Calc, actual provider, external provider-log reconciliation, WSLc, MAP01, latency/efficiency comparison, or allocation. This is a composed-path regression contract, not live product validation or Issue #57 completion.

`SHA256SUMS.json` covers this README, both source diffs/freezes and every file in `run-01/` and `run-02/`.
