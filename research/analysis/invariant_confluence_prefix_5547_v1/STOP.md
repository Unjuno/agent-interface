# Allocation STOP — Issue #5547

Allocation `ic-prefix-finite-model-5547-20261001-01` stopped before construction tests because the frozen unittest command used a module path that did not expose the sibling `experiment.py` on `sys.path`.

- Exact command and complete captured traceback: `STOP.json`.
- Exit code: 1; test cases started: 0.
- Experiment runner: 0; independent raw auditor: 0; raw rows: 0.
- Docker, GPU, CUDA, model, GUI and external-effect calls: 0.
- Disposition: `STOP_TEST_DISCOVERY_INVOCATION`; scientific hypothesis result: **none**.
- The allocation is consumed. No retry or relabeling was made.

The frozen source package remains intact. This STOP identifies an invocation/harness error only; it is not evidence for or against invariant-confluence classifications.
