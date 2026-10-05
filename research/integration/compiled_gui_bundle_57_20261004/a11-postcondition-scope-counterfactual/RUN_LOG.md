# Run log

- Frozen checkout source: `88372bed99266ddfade7dedca9630555e18c8960`.
- Run: `python3 run.py > RAW.json`; exit 0. Four deterministic mock paths: authored contract `SAFE_YIELD/effect_failed`; scoped target-check removal with saved=true `TASK_SUCCEEDED/method_complete`; saved=false `SAFE_YIELD/effect_failed`; saved=unknown `SAFE_YIELD/effect_unavailable`.
- Audit: `python3 audit.py RAW.json > AUDIT.json`; exit 0.
- Optimized audit: `python3 -O audit.py RAW.json`; byte-identical to `AUDIT.json`.
- Tamper check: changed the saved=false receipt to claim `TASK_SUCCEEDED`; normal and optimized auditors both rejected it.
- Scope: retained-data construction only; no browser, provider, model, network, container, GUI input, or formal allocation.
- Pre-run harness failure: the first invocation failed during module import because the archived schema path was not on `sys.path`. Added that frozen source directory, then ran the valid trial once. No output raw was produced by the failed import.
