# Pre-run addendum

The original A12 freeze is commit 16b7ebae6ee8f706d89b178f487b9ee04f1c920f. Before any candidate invocation, this helper was added for an in-memory execution path because local writes fail with ENOSPC. It does not alter candidate.py, source-manifest.json, source_snapshot/, input arms, or decision gates.

runner.py SHA-256: 0d88c2bbb3b95c1f3e58e20d386b275e83446239f77aa93324c022d5df070d3c
candidate.py remains SHA-256 bc69c79cdcaee1e1a95c0e3cbbabe10afd4344b3661f3905c1b2e6142759a535.
Expected source manifest SHA-256: bf7b2d911854cb6fdaabedabdb853bb2fc3bffd5049b3f4c8e5b3c1355a4222a.

No candidate or audit invocation has occurred. The next action is one normal and one dual-first-release-drop arm using the frozen candidate bytes and frozen source snapshot bytes; capture candidate JSON in memory, then run the independent audit and mutation checks before adding result files.
