# Construction failures retained

These are harness-development failures before the frozen normal/-O pair. They are retained as evidence and are not counted as candidate outcomes.

1. Initial source preflight read the local checkout's `input_transition_owner_v4.py`, whose bytes differed from the frozen `origin/main` blob. The preflight correctly stopped before composition. The harness now materializes the exact blob using `git show <frozen-ref>:<path>` and checks its Git object ID before executing the V15 manifest merger or release producer.
2. The first extracted `_merge_sources` call omitted its `_sha` helper from the AST execution namespace. It stopped before completing the source manifest. The harness now binds the same SHA-256 helper semantics without editing production source.
3. The next run exposed that native Windows `Path.relative_to` emits backslashes in JSON keys. Candidate bytes and hashes were correct. The auditor now canonicalizes path separators for cross-platform comparison while retaining and hashing the raw generated manifest.
4. A clean-checkout replay audit found A01 referenced five candidate files available only in the working tree for open PRs #8519/#8524. A01 evidence remains unchanged. The package now vendors the exact runner, adapter, attribution source, and three component freeze files, hashes every input, and reruns as a new official A02 output.
5. An adversarial result mutation changed one candidate input identity while leaving the frozen vendored bytes intact. The first A02 auditor still accepted the altered result because it checked the vendored file but not the result's recorded candidate identity. The auditor now binds every recorded candidate identity to the freeze; the 9/9 receipt remains preserved and `AUDIT-recheck-02.json` records the corrected 10/10 audit. Candidate raw outputs were not changed or rerun.

All earlier output directories are preserved. A02 uses a fresh destination and is the self-contained reproducibility pair.
