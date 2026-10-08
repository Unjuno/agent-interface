# A05 formal execution custody

The one-shot command was:

```text
sandbox-exec -p '(version 1) (allow default) (deny network*)' /opt/homebrew/opt/python@3.14/bin/python3.14 /tmp/agent-interface-1998-inkscape-a05/research/analysis/inkscape_task_marker_crop_1998_t0_a05_20261009/formal_runner.py
```

The sandbox smoke check exited 0. The formal wrapper exited 1. It invoked the
candidate exactly once; the candidate exited 1 with an `UnboundLocalError` before
any Tesseract process was created. The candidate stdout is empty. Per the frozen
conditional, the auditor was not invoked. No retry occurred. The wrapper's
first-run artifacts are retained under `results/`.

The formal runner did not record its process start/end time or write `RUN.json`
on the candidate-failure branch. Therefore those times remain unknown. The
post-run custody record was observed at 2026-10-08 22:32:42 UTC; this is not
represented as the process completion time. No timestamp is reconstructed from
the later observation.
