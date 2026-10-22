# Formal execution record

The frozen wrapper was invoked once under network-denial sandbox:

```
/usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' /opt/homebrew/opt/python@3.14/bin/python3.14 research/analysis/chromium_postsubmit_task_cue_1998_t0_a09_20261009/formal_runner.py
```

Wrapper exit: 0. Candidate invocations: 1, exit 0. Independent auditor invocations: 1, exit 0. Tesseract crop calls: 20. Retries: 0. All 20 OCR processes exited 0. The auditor returned `FAIL_NO_CROP_TOKEN` with zero audit errors: no crop contained exact token `t001101`. Exact candidate/auditor stdout, stderr, exit codes, run record, and hashes are preserved under `results/`.

This is a scientific negative for the fixed crop/Tesseract combination on one retained post-submit, pre-public-effect frame. It is not a runner failure or a product claim.
