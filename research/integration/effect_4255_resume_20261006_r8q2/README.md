# #4255 original effect allocation: retained audit-control failure

**FAIL_FROZEN_AUDIT_CONTROL_GATE**, not a runtime patch or qualified PASS.
Four matching XTEST app effects and eight no-input refusals were observed across
12 sessions, but the unchanged mandatory mutation suite rejects only11/12.
The surviving source-position mutation is retained and diagnosed in REPORT.md.
Keep Issue #4255 open. The original allocation is now consumed; do not rerun it.

Read-only reproduction (CPython3.13 standard library; no X11/model/network):

```sh
python -B -S verify.py
python -B -S -m unittest -v test_verify
```

The verifier restores101 exact files, checks100 manifest entries and16 frozen
members, and reproduces the original audit exit0, mutation-suite exit1 and
posthoc diagnosis byte-for-byte. Its verification success means the **FAILURE**
was preserved, not that the experiment passes. It never starts runner.py/app.py.

Six base64 parts retain the complete26,068-byte XZ /142,652 member-byte archive.
The full original source, construction, formal raw, stdout/stderr and actual
process receipts are included, not replaced by a summary. Extraction assumes
trusted publication and a private quiescent temporary parent, not an adversarial
filesystem. All original source paths and other workers remain unchanged.
