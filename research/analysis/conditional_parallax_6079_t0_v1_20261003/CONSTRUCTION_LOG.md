# Construction and freeze record

Formal candidate/auditor counts remain zero until the one-shot commands in `FREEZE.json` are run.

1. Initial construction command `python3 -m unittest -v test_method.py` failed during fixture construction because the renderer retained `CY` as a float; no test body completed and no formal corpus was written. The fixture now rounds the pixel row before indexing.
2. Next construction suite ran five tests successfully but exposed that the independent mutation suite did not reject a changed truth assignment and did not bind every image to its sidecar digest. The auditor was strengthened with explicit truth contracts and per-frame SHA-256 receipts; the one-frame mutation now flips a pixel in a copied frame and must fail the digest gate. No frozen inputs or candidate output existed then.
3. A repository-root unittest invocation failed to import the sibling modules because the test is intentionally standalone; no tests ran in that attempt. The supported command is `python3 -m unittest discover -s research/analysis/conditional_parallax_6079_t0_v1_20261003 -p 'test_*.py' -v`.
4. Final pre-freeze construction on main `664f61e24b52fa2f955c486a6c714ca59629f6d9`: 6/6 tests PASS; `py_compile` passed for fixture, candidate, auditor and test. The 9-pair visible corpus and auditor-only sidecar were generated once and hashed in `FREEZE.json`.

These are construction-gate diagnostics, not formal candidate outcomes. All fixes preceded the source/input freeze.
