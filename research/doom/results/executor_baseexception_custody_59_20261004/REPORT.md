# Executor BaseException custody regression

## Root cause

At #7635 candidate `ddff6ebf8cea186accaae5dca98750ac16bb6a4b` (then based on `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6`), `ExecutorV13._run_with_watcher_cleanup` classified step failures only with `except Exception`. A backend `KeyboardInterrupt` carrying `release_batch_publication` bypassed that handler. The `finally` path then completed verified `release_all()` and emitted the default `status=completed`, without the publication ledger; the process exception escaped afterward.

## Repair

The executor now records a failed terminal and copies publication custody for `BaseException`. For non-`Exception` subclasses it retains the original object and traceback, publishes the terminal after cleanup, then re-raises that same object. The new executor-level regression intercepts `threading.excepthook` and verifies failed status, the exact ledger, and propagation of the original `KeyboardInterrupt`.

The regression was first run against the unmodified candidate and failed because terminal status was `completed` instead of `failed`; see `RED_OUTPUT.txt`.

## Verification

- Five focused backend/session/executor suites: Windows Python 3.11, 31/31; WSLc, 31/31 with no skips.
- Final qualification includes current `main` `0eed302f7c2f821011154ce5d5ad23d6540d215d`, merged in local integration commit `c1305f5c5bf6d0d55ccce0af559c667f94d30adc`. The repair commit is `523039a48ffb0037af41d469cbe34d1225e96362`.
- All four affected Python files compile in both environments; `git diff --check` passes.
- WSLc used cached image `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378`, `--pull never`, network disabled, source read-only and a separate output mount. It warned cgroup/swap enforcement is unavailable; resource limits are requested, not claimed as enforced.
- This is synthetic backend/executor construction evidence. No game, model, GUI, OS input or live allocation ran; no physical-release or task-effect result is claimed.

Outputs: `TEST_OUTPUT.txt`, `COMPILE_OUTPUT.txt`, `test-exit-code.txt`, and `compile-exit-code.txt` are WSLc results; `TEST_OUTPUT_WINDOWS.txt`, `COMPILE_OUTPUT_WINDOWS.txt`, and `windows-exit-codes.txt` are Windows results. `SHA256SUMS` pins the four exercised source and test files.
