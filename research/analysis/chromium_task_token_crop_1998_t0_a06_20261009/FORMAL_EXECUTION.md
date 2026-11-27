# Formal execution record

Disposition: `HOLD_RUNNER_ERROR`.

The frozen `formal_runner.py` was invoked once under `/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' /opt/homebrew/opt/python@3.14/bin/python3.14`. It exited 1 before launching the candidate because construction had already created the empty `results/` directory and the frozen wrapper requires `out.mkdir(exist_ok=False)`. Candidate invocations: 0. Auditor invocations: 0. Tesseract crop calls: 0. Retries: 0. The allocation is consumed; this failure is not repaired and rerun.

The wrapper traceback was emitted to the tool transcript but was not redirected to a raw file at invocation time. `results/formal_runner.stderr` below is a post hoc transcript transcription, not byte-preserved stderr. The exit code was observed as 1. No scientific OCR outcome exists, and the marker question remains unresolved.
