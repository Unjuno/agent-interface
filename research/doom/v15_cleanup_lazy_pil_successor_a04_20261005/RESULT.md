# V15 lazy-Pillow import successor A04 — synthetic regression PASS

The exact current-main + PR #8094 virtual-merge source closure was materialized and audited. With only the frozen top-level import relocation applied, the seven-module fake-X regression suite passed all 47 tests in normal and optimized CPython 3.12.14 runs. No candidate behavior or test files were changed. Original stdout/stderr bytes, source manifest, and import-only patch are retained.

This is scoped synthetic regression evidence, not Issue #59 acceptance. Pillow 12.3.0 was installed in the runtime, so this result does not test whether the wrapper chain imports when PIL is absent. A05 separately freezes a process-local PIL import blocker to test that claim; A04 will not be rerun. No native X11, live game, model or physical input was used.
