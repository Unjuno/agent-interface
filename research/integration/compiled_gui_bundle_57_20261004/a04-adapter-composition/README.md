# A04: caller-v3 form adapter composition

Issue: [#57](https://github.com/Unjuno/agent-interface/issues/57). This is a test-double integration check for the missing form-method-to-compiled-graph adapter seam. It is not a live run or an efficiency allocation.

`research/live_control/integrated_efficiency_compiled_adapter_v1.py` converts the existing validated two-action form method plus distinct minted target references into the existing `compiled-gui-interface-v1` graph. The runner invokes the real `adaptive_acquisition_caller_v3.run` and `runtime.core_v1.compiled_gui.run` with synthetic observations, admissions, action receipts, release receipts and effect verdicts.

The saved raw record is `RUN.json`; `audit.py` independently checks the source hashes and outcomes. The positive case reaches two distinct released actions, with the observed field change selecting the Submit transition. The changed-target case stops with `unknown_state` after one transition. When the caller's outer effect verifier returns unavailable, the compiled graph has completed two transitions and delivery remains confirmed, but current main returns `execution_progress=null`. All three cases have zero attempted model calls and empty attempt ledgers.

Reproduce from the repository root with Python 3:

```sh
PYTHONPATH=research/live_control:. python3 -B research/integration/compiled_gui_bundle_57_20261004/a04-adapter-composition/run.py /tmp/a04-run.json
python3 -B research/integration/compiled_gui_bundle_57_20261004/a04-adapter-composition/audit.py
python3 -B -m unittest -v research/integration/compiled_gui_bundle_57_20261004/a04-adapter-composition/test_runner.py research/integration/compiled_gui_bundle_57_20261004/a04-adapter-composition/test_audit_coverage.py research/live_control/test_integrated_efficiency_compiled_adapter_v1.py
```

The adapter unit test rejects a method that skips the intermediate observed-effect condition. The composition tests assert two distinct action IDs, typed one-action yield on changed state, and zero model attempts; the saved-audit coverage test corrupts each case's attempt count/ledger and confirms rejection.

Scope limits: no RuntimeClient/Chromium session, model/provider call, target minting, independent task scorer, six-task schedule, invalidation/repair cost, GUI/input/release signal, or end-to-end token/latency measurement is exercised. A04 proves the adapter seam only and is not the prospective composed #56 runner required by the current #57 gate.
