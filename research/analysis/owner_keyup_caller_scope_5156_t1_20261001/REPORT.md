# Issue #5156 — caller-bracket scope analysis T1

## H / T / D / C / U

- **H:** The original universal condition requiring every owner key-release interval to be nested inside a caller start/return interval is impossible for owner-loop cleanup. The owner thread directly releases on stop, expiry/cancel/focus invalidation, and finalization, while the v3 wrapper only brackets explicit `up`/`button_up` requests and caller-requested release/close operations.
- **T:** Against exact Git blobs from main `666a2b0919199bb11251ceb83a31b23be6d71b34`, run four pre-freeze AST assertions and compile checks; then run the frozen classifier once and independent raw/source auditor once. No repository runtime modifications, formal X11 allocation, Docker, X server, GUI, input, model/provider, or GPU.
- **D:** `PASS_CALLER_BRACKET_SCOPE_CORRECTION_REQUIRED` iff source blobs match, four owner release sites classify as one queued explicit release/close plus three autonomous sites, v3 timestamps explicit key-up around the call, and no wrapper timer encloses autonomous cleanup. **Result: PASS_CALLER_BRACKET_SCOPE_CORRECTION_REQUIRED.** Independent audit: `PASS_INDEPENDENT_AUDIT`, errors empty. Construction tests: 4/4. Classifier: exit 0. Auditor: exit 0.
- **C:** Windows CPython 3.12.10, stdlib AST/hash/JSON. The local copy was restored from GitHub REST blob base64 and exact Git blob IDs were recomputed from raw bytes (not affected by `core.autocrlf`). Owner v10 blob `341b3c01649943ddaad5f28431a792c4889cc36e`; wrapper v3 blob `0ea631abcf6272f0538a9ef9198ad8069b47b464`.
- **U:** This is a source-control-flow result, not timing evidence. It does not prove actual XTest/XSync duration, physical key-up, application delivery/consumption, MAP01 effect, occupancy, safety, latency, or human tempo. It does not consume or pass any formal allocation. Correct future protocol should keep explicit `up` caller nesting as a separate class and classify automatic cleanup with owner-thread-local timing/reason/identity without requiring an enclosing caller bracket.

## Callsite classification

| Owner release site | Classification | Caller bracket implication |
|---|---|---|
| line 205 | stop request | autonomous owner loop |
| line 219 | expiry / cancel / focus or surface change | autonomous owner loop can act after earlier request returned |
| line 261 | queued `release` / `close` | corresponding caller operation can be bracketed |
| line 356 | thread finalizer | cleanup may run during thread exit |

The v3 wrapper has an explicit `up`/`button_up` branch that samples monotonic caller start/return around `_inner.call`. This does not imply its interval encloses autonomous owner cleanup. A universal nesting gate therefore rejects a valid measurement protocol for three of four owner release paths.

## Reproduction

From this directory:

```powershell
python -B -m unittest discover -s tests -v
python -B classify.py
python -B audit.py
```

The classifier and independent auditor were each formally invoked once after the freeze. The test suite and `py_compile` were construction-only, before freeze.
