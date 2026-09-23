# Golden v3 → CLI adapter contract audit (#2203)

## Result

**PASS_GOLDEN_V3_CLI_ADAPTER_CONTRACT_SCOPED**

Using the frozen `golden-v3-result-v1` schema and current `runtime/cli_v1` status vocabulary, this pure read-only adapter validator maps five statuses:

- success → returned with task_success preserved;
- partial → returned with partial_effects preserved and task_success false;
- refused → returned with explicit refusal;
- stale_invalidated → returned as explicit refusal, never current authority;
- cleanup_failed → runtime_failed with cleanup_error and task_success false.

An authority=true fixture is rejected. Task success remains separate from program completion, partial effects and usage are retained, and cleanup failure cannot be promoted to success.

Container: `python:3.12-slim`, py_compile plus one formal validator run.
Digest: `e9de495d18e241c63e1d5d6d33e40f8e88d070d0e7fdab70f6cab6fe26552408`.
Counters: fixtures=5, model=0, GUI=0, input=0.

## Boundary

This is a contract-only research adapter, not a production runtime adapter. It does not execute `runtime/cli_v1`, golden desktop, model, GUI, network, or input; it does not establish task correctness, latency, token savings, or product readiness. Any production adapter requires a separate implementation successor and integration tests.
