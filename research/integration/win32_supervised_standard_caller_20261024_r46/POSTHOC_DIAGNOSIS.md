# R46 posthoc harness diagnosis

The phase-2 harness called `subprocess.Popen([sys.executable, "-m", str(PACKET / "fixture_app_timed.py"), ...])`. Python `-m` expects an importable module name; the captured `fixture.stderr.bin` contains CPython's `ModuleNotFoundError` for the supplied Windows `.py` path. The fixture never wrote `fixture-meta.json`, so the harness stopped at `fixture failed to become ready` before CUA activation, observation, or task dispatch.

This finding is based on the retained phase-2 stderr and `task_probe.py` source. It is a deterministic invocation mismatch. A new attempt must use a direct script invocation (remove `-m`) or an importable module name, then freeze fresh IDs, conditions, hashes, and evidence paths. R46 itself remains `FAIL_OR_UNKNOWN`; no replay is authorized by its one-shot policy.

Phase 1 independently passed its 11 strict release checks, including the preregistered 1400 ms same-clock post-cancel callback hold, 89 same-call polls, same-generation Q-up observation during hold, and bounded cleanup. This does not establish task completion or any WSLc/MAP01/efficiency/reliability claim.
