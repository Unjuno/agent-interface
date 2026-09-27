# Audit attempt 01 — environment STOP

Allocation: `w2-draft2020-12-meta-audit-20260928-01`.

**Disposition: `STOP_NATIVE_EXTENSION_TMPFS_MOUNT`.** Docker image and wheelhouse identities matched the freeze; `pip install --no-index` installed jsonschema 4.25.1 plus all five pinned dependencies. Before `meta_audit.py` began, Python failed importing the rpds native extension:

```text
ImportError: /tmp/site/rpds/rpds.cpython-312-x86_64-linux-gnu.so: failed to map segment from shared object
```

No schema meta-validation, trace validation, mutation checks, runner output, or scientific conclusion occurred. The raw output directory remains empty. Do not rerun allocation 01. A separate construction-only tmpfs loader preflight and, if it passes, a new uniquely named audit allocation are required. Initial command omitted the explicit `exec` tmpfs flag; the successor command must pin it and test import before any registered audit is launched.

The failed attempt is retained as infrastructure evidence, not a schema failure. No old W2 result is changed.
