# Historical route source bundle for #2813

This additive artifact preserves the route source that existed in the retained
PR #2730 head but is absent from current main. It is provenance only; it does
not alter or rerun the retained v5 allocation.

- source commit: `01349d7bc76e5635f5568c53ffeec4d9ff49abb1`
- original path: `runtime/golden_desktop_demo.py`
- SHA-256: `9b3fd4e88498394b36128d42a716ed12646734ea0090bf2472d51239656dcd44`

The current-main runner must not import this file implicitly. A future #2813
allocation must declare every additional dependency and hash before using it.
