# Run record

- Issue: [#7161](https://github.com/Unjuno/agent-interface/issues/7161)
- Freeze: `main` SHA `8ff7afed76c1d81eabac9d0c37d4191b352045a4` (read-only `git ls-remote` immediately before execution).
- Hypothesis/protocol: see `README.md` (H/T/D/C/U).
- Environment: Windows 11 host, Ubuntu WSL, Linux kernel inherited from WSL, Python 3.12.3, x86_64. Current process saw approximately 4.67 GiB `MemAvailable`; this is an observation only, not a cap or benchmark.
- Container readiness: WSLc 3.0.1 `info` returned. `wslc list` and `wslc run --rm --pull missing --name codex-7161-t0-probe python:3.12-slim python -c ...` produced no result within 30 seconds. The two agent-started CLI requests were interrupted. No container was confirmed created; no unrelated process was touched. Docker CLI was not found in the active PowerShell PATH.
- Execution deviation: because the WSLc operations did not return, the CPU-only synthetic construction was run directly in Ubuntu WSL (not a container). No memory, Docker, WSL, swap, or `.wslconfig` setting was changed.
- Commands, in order, each once:
  1. `python3 generate.py > GENERATOR_STDOUT.txt` — exit 0; 5 cases, 1 distinct final visual state, 9 events.
  2. `python3 candidate.py > CANDIDATE_STDOUT.txt` — exit 0; emitted five typed dispositions.
  3. `python3 audit.py > AUDIT_STDOUT.txt` — exit 0; `PASS_METHOD_SCOPED`, five cases verified, all three mutations rejected.
  4. `python3 -m py_compile generate.py candidate.py audit.py` — exit 0. This does not rerun the candidate or auditor.
- Candidate/auditor invocation count: one each. No retries or edits to the experiment sources after their run.
- Scope: finite synthetic contract only; see `README.md`. No user value, task success, real effect, or efficiency inference.
