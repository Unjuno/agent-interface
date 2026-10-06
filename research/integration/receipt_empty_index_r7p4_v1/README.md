# Empty-event compaction current-source qualification

Issue #8244: [result, scope and reproduction](REPORT.md).

PASS_CURRENT_MODULE_COMPATIBILITY on96 source-frozen inputs; not a new speed or product claim. The runtime proposal is four added lines plus a focused regression test. Main adoption still needs current-head checks and nonauthor review.

SOURCE_MANIFEST.json and RESULT_MANIFEST.json bind seven binary pieces of two literal TAR.XZ archives containing32 complete source/input/result files. Frozen protocol, exact inputs, old/new modules, tests, actual executions and first outcomes are included.

Read-only verification: `python -S -B verify.py`. Packaging-only controls: `python -S -B test_restore.py`. Neither invokes the consumed differential runner. The original prospective README is preserved in source-publication commit ce22783a43887a8a0110f6f2e61399e7161a8b84.
