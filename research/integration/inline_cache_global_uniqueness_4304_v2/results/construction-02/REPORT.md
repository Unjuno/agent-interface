# Excluded construction-02 report

Allocation: `inline-cache-uniqueness-4304-20260928-02`, Issue #4304. This is construction-only, not formal evidence and not a hypothesis decision.

## Invocation and environment

Local Arch Linux WSL2 on this PC, CPython 3.14.5, Python-Xlib 0.33, Xvfb 21.1.24. No Docker, GPU/CUDA, model, or external execution. One invocation ran four fixed excluded construction sessions in a private mount namespace. The wrapper hid WSLg's read-only X0 socket mount behind a disposable tmpfs and dropped privileges to uid/gid 1000.

Command:

```text
wsl.exe -d Archlinux -u root -- unshare --mount --propagation private -- /bin/sh /mnt/c/Users/junny/Documents/Codex/unjuno-x11-4304-v2/research/integration/inline_cache_global_uniqueness_4304_v2/src/run_private_x11.sh construct /mnt/c/Users/junny/Documents/Codex/unjuno-x11-4304-v2/research/integration/inline_cache_global_uniqueness_4304_v2/results/construction-02
```

Exit 0; `BATCH.json` is `COMPLETE`, all four cases `COMPLETE`, with no retries or replacement cases. The black moved ROI was returned as `bytes` in this Python-Xlib version. Separately, byte-level unit fixtures cover black all-zero bytes represented as UTF-8 `str`, valid multibyte UTF-8 `str`, binary `bytes`, and bytearray normalization.

| Scenario / policy | Targets after mutation | Proposals / app effects | Warm scan pixels |
|---|---:|---:|---:|
| STABLE / LOCAL_PATCH | 1 | 1 / 1 | 256 |
| MOVED / LOCAL_PATCH | 1 | 1 / 1 | 38,656 |
| DUPLICATE / GLOBAL_UNIQUENESS | 2 | 0 / 0 | 38,400 |
| ABSENT / GLOBAL_UNIQUENESS | 0 | 0 / 0 | 38,400 |

CPU-only source suite: 11/11 passed. Independent raw-only construction audit: `PASS`, 340 checks, zero errors. Deep-copied effective corruption harness: `PASS`, 15/15 rejected (including a diagnostic-stderr mutation). This validates only the construction harness and four synthetic sessions.

## Retained digests

- BATCH.json SHA-256: `8cf4dcc170af3dbd309727982633b36b7b2e53302f9c7e0ea0e37bf56e75f9ba`.
- INVOCATION.json SHA-256: `b5c80586aee7e4f659e48ff9e6f174dee2f27534c77739352f57b196c48d269a`.
- INDEPENDENT_AUDIT.json SHA-256: `6e9bc2b0c14d8ad4e132038d8efcbefd6093e444d008e57995c172d208588e98`.
- CORRUPTION_CONTROLS.json SHA-256: `dbac024ad10f363772823ae82c8d7e70fb13635a67718c2057ef7c5ec6dcbc28`.
- Case RAW.json SHA-256 values are in BATCH.json; each lossless actor journal, image bytes, process receipt, stderr, and cleanup fields are retained beside its RAW.json.
- Xvfb's repeated nonfatal XKB keymap warning is preserved verbatim; exact SHA-256 `12dcabf0449b9ff85d589b86d110c814777977daca56e7ba8ec300c5334fe397`. The independent audit rejects any other Xvfb stderr; actor and policy stderr are empty.

## STOPs and limits

- `construction-01` remains STOP at Xvfb readiness because WSLg's X11 socket path is a read-only mount. No task observation/input occurred. The native X0 socket was not altered. Later runs used a private mount namespace.
- `construction-03` remains STOP because the installed Xvfb does not support the attempted `-kb` option. Xvfb exited before readiness; no task observation/input occurred. Its raw and stderr remain intact. The unsupported option was removed before the candidate freeze.
- These attempts are not formal cases and are not included in the 24-case denominator. Do not reuse their output paths or relabel them as passes.

Formal allocation-02 remains unstarted. No task claim or production/runtime change follows from this construction report.
