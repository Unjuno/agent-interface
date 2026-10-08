# Native Windows broker-path candidate diagnostic

Issue: #4882; successor scope to Linux-only construction evidence in #4876.

The exact candidate resolver blob is identified in STOP_RECORD.json. The local pre-execution runner and raw-only auditor were frozen in the Issue before invocation. CPython 3.11.9 / win32 AST-parsed all three Python files.

## Frozen hypothesis and limits

The #4876 candidate resolver should preserve canonical /repo and /workspace mappings while rejecting host-absolute/device namespace, traversal, missing-target and symlink-escape inputs on native Windows. The broker and subprocess are never invoked; no model/provider is called.

## Outcome

STOP_SYMLINK_UNAVAILABLE before formal cases. The single permitted runner command returned exit 2 because Windows returned WinError 1314 when creating the fixture symlink. Zero path cases ran, no formal raw output was created, and the separate auditor was not run. This STOP is preserved; no retry or altered case set.

## Reproduction record

The one attempted command was `python run_windows_probe.py --out outputs/formal-01/RAW.json`. Had symlink setup succeeded, the runner would have captured 28 fixed cases and the separate command would have been `python audit_windows_probe.py outputs/formal-01/RAW.json outputs/formal-01/AUDIT.json`.

The full pre-frozen runner/auditor are retained here for a future independently authorized Windows allocation. Linux Docker is not substituted because this question is specifically native Windows path behavior. The exact error's machine-local filesystem path is intentionally omitted.
