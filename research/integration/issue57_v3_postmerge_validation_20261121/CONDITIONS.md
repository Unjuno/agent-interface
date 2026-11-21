# Conditions — post-merge Issue #57 v3 journal verification

- Source: `Unjuno/agent-interface` main at `9734c7f907b49799c134483d6011d092f190740d` (PR #10340 squash merge).
- Run time: 2026-11-21 11:57–11:58 UTC.
- Host interpreter: Windows CPython 3.11.9. Each Python invocation set `PYTHONPATH` to the current worktree root.
- Commands: `python research/integration/test_issue57_v3_prospective_run_v1.py -v`; same with `python -O`; and the single `CompiledGuiEdgeIntegrationTests.test_profile_cleanup_retries_transient_lock_and_rejects_other_roots` unit test in normal and `-O` modes.
- The four complete stdout/stderr streams and exit codes are retained under `raw/`.
- No Edge process, GUI action, model/provider call, Docker/WSLc operation, or experiment allocation was invoked. The Edge test's actual browser task method was not run.
- This is post-merge local regression validation, not a preregistered live allocation or an efficiency/reliability result.