# Late usage plus native owner receipt composition R01

This frozen offline experiment joins a post-score, hash-bound late-usage
observation through `RecordedPublicMcpCaller` and `ProviderAttemptRecorder`
with the exact `interface_dispatch` / `interface_results` identity and native
owner release/horizon binding accepted by `recorded_comparison_adapter_v1`.

Two conditions have identical two-attempt structure: one timed-out attempt and
one subsequent successful attempt whose action is tied to the native owner
receipt. The positive has a late-usage row; the control has no row. Both use a
synthetic owner receipt and UNKNOWN eligible effect time. No provider, Relay,
GUI, OS input, Docker, or WSLc call is made.

Run from `research/integration/standard_mcp_task_ledger_57_v1` with Windows
CPython 3.11:

```powershell
py -3.11 -m unittest -v test_recorded_comparison_adapter_v1
py -3.11 -O -m unittest -v test_recorded_comparison_adapter_v1
py -3.11 late_usage_native_owner_composition_20261121_r01/run_experiment.py
py -3.11 late_usage_native_owner_composition_20261121_r01/audit_packet.py
```

The local preflight tests passed 12/12 in both modes before this experiment was
frozen. `run_experiment.py` refuses to overwrite retained runs. The audit
checks exact pinned source blobs, complete raw-reference custody, timeout
non-dispatch, native owner binding, UNKNOWN eligible effect time, positive vs
missing usage outcomes, and the portable SHA256 manifest.

The evidence is synthetic integration only. It does not prove live provider
delivery or hidden-retry exhaustiveness, owner truth, task success, physical
release/effect, matched A/B/C economics, or recovery reliability.
