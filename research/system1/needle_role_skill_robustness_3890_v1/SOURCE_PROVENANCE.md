# Source provenance

Issue #3890 was merged by PR #3902. Source is read from the immutable merged main tree, commit `5dd2b9b18fc5f3e73e8ff9adf808806a49a121ce`, not copied from the local role-skill worktree, which contains unrelated untracked audit scratch.

| File | SHA-256 in merged #3890 FREEZE.json |
|---|---|
| runner.py | `a0e99b991a8a3ab9b2f4b6f4f22f7c705989447ce64a14738026fcd763b55abb` |
| loader.py | `5ff6df91ea3929f68fe77ccd6156bdb1310d0fec86088489d8b99905a7c5854f` |
| audit.py (post-correction auditor) | `4e53e241aa115202ce9ca2ce3a5b3df76599b80ad03290a61594bd6b0e35c3a0` |
| PREREGISTRATION.md | `b2ccbac02e0d759c662b955fb34127310ea87d2cbdfe72d91b356a750ffd3c7a` |

The robustness successor keeps the task family, network shape, LoRA rank, optimizer, training rows/steps, evaluation sample size, graph, and qualitative negative controls. It changes only the fresh seed allocation and strengthens source/package/raw-evidence auditing required by Issue #4479. The predecessor's files, seed outcomes, and audit chronology are not modified.

