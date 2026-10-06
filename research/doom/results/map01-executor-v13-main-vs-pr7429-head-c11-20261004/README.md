# C11 — current-main executor source versus PR #7429 current head

PR #7429 advanced after C10 froze head `5f3e24d`. This comparison uses its current head at freeze, `b30fd755e68d470799e6c26f12296a97cf027df8`, whose v12/v13 sources add three reentrant-close cases to the existing sink-error, cancellation, and terminal-publication tests.

The exact same seven-test file is run against (1) current-main executor v12/v13 and (2) current PR #7429 executor v12/v13. Both runs use the same frozen support modules, whose blobs are byte-identical across the two refs. This distinguishes an actual source conflict from a test-environment difference.

Run from this worktree root:

```powershell
$env:PYTHONPATH = 'research/doom/results/map01-executor-v13-main-vs-pr7429-head-c11-20261004/FROZEN/common-support'
python -B research/doom/results/map01-executor-v13-main-vs-pr7429-head-c11-20261004/test_executor_v13_against_main.py -v
python -B research/doom/results/map01-executor-v13-main-vs-pr7429-head-c11-20261004/FROZEN/pr7429/test_executor_v13.py -v
```

The first test redirects only its module path to `FROZEN/main`; the second loads `FROZEN/pr7429`. `audit_c11.py` checks source pins, test counts, the missing current-main sink-error receipt, and the full PR-head pass. No container or formal/live allocation is used. This is a software publication/state-machine result only; it does not satisfy the #59 real-time control gate.

Current-main applicability was checked after the run: origin/main was 75c6d18888da68033ef4b07cffefb3622568ed19, and the v12/v13 executor and executor-test paths are unchanged from the pinned 911e7b6 base. The frozen experiment therefore tests the executor implementation still present on current main.
