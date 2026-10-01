# Construction record — Issue #4479

Source provenance: #3890 merged by PR #3902. Runner and loader are copied from its pinned sources; only allocation/predecessor identity is changed. The same torch model/data schedule is retained. Construction tests exercise schemas, tensor shapes, deterministic seed mapping, data-only package validation, receipt graph transitions and negative controls. Tests do not call `train`, and no model optimizer is created or stepped.

The six #4463 screenshots and image-manifest data are unrelated to this synthetic role-skill allocation; they are deliberately not included.

Formal is one PowerShell orchestration launching ten sequential builders and two fresh read-only-package loader containers per seed, followed by the independent audit container. Any command failure stops the orchestration and preserves prior outputs; no retry is permitted.

The first construction probe ran 8 tests: six passed and two failed. One exposed a seed-allocation defect: candidate seed 3792 overlapped #3890's retained component streams (3792+1 == 3788+5). The second was a test expectation that the public Issue body literally contain its own Issue number. Before any training, the Issue and preregistration were corrected to ten seeds 100000..100900 in steps of 100, and the test was corrected to assert the actual frozen seed clause. Seed 3792 is retired and is used only in excluded, no-training construction fixtures.

The corrected local Docker construction run passed all 8 tests. It still emits inherited PyTorch/no-NumPy and `ResourceWarning` diagnostics from the predecessor loader's temporary-file helpers; those warnings did not fail any test. No optimizer/training path ran.

Final orchestration preflight caught a PowerShell path-normalization typo (`Replace` was passed an empty search string) before any formal container started. The formal allocation remained at zero. The script was corrected to normalize Windows backslashes, then PowerShell parsing and all 8 construction tests passed again. An initial construction-test invocation also passed an extra `python` token to the image whose entrypoint is already Python; it exited before loading the test module and did not invoke training. The corrected entrypoint invocation produced the 8/8 pass above.
