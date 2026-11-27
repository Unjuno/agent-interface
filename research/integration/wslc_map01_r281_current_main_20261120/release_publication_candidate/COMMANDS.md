# Commands and results

All passing commands ran from `research/live_control` against the candidate files in this worktree. `test_cancel_release_publication.py` ran the complete 9-test module each time.

| Runtime | Command | Exit | Result |
|---|---|---:|---|
| CPython 3.11.9 | `python -m unittest -v cancel_release_publication_59.test_cancel_release_publication` | 0 | 9/9 normal |
| CPython 3.11.9 | `python -O -m unittest -v cancel_release_publication_59.test_cancel_release_publication` | 0 | 9/9 optimized |
| CPython 3.13.14 | `python -m unittest -v cancel_release_publication_59.test_cancel_release_publication` | 0 | 9/9 normal |
| CPython 3.13.14 | `python -O -m unittest -v cancel_release_publication_59.test_cancel_release_publication` | 0 | 9/9 optimized |
| CPython 3.13.14 | `python -m py_compile executor_v12.py cancel_release_publication_59/test_cancel_release_publication.py` | 0 | compile passed |

The pre-fix isolated base replay ran the single new test from a temporary copy of base `381a21a` with the new test added and no source change. Exit 1 was expected: assertion `len(release_events) == 1` observed zero events. Full stdout/stderr are in `pre-fix-main-baseline.log`.

Raw logs: `py311-normal.log`, `py311-optimized.log`, `py313-normal.log`, `py313-optimized.log`, and `py313-pycompile.log`. The short `normal.log`/`optimized.log` preserve an earlier harness-shape error and are not passing results.
