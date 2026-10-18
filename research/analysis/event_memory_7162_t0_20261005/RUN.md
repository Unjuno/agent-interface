# Run record

- Issue: [#7162](https://github.com/Unjuno/agent-interface/issues/7162)
- Freeze: main `1a3d253d7ef5761aecbf28a6092eb5ab8a128df6` (`git ls-remote` immediately before authoring/execution).
- Environment: Windows 11, Ubuntu WSL, CPython 3.12.3, x86_64. CPU-only finite synthetic workload.
- Commands, in order: `python3 generate.py` (exit 0; 7 intentions, 2 eligible, stdout retained from that invocation); `python3 candidate.py > CANDIDATE_STDOUT.txt` (exit 0); `python3 audit.py > AUDIT_STDOUT.txt` (exit 0, PASS_METHOD_SCOPED); `python3 -m py_compile generate.py candidate.py audit.py` (exit 0).
- Candidate and auditor each invoked once. The first post-run checksum command encountered a missing `GENERATOR_STDOUT.txt` and exited nonzero before printing the audit receipt. That file was restored from the exact generator stdout captured in the tool result; no experiment script was rerun. The recovery/checksum verification is recorded separately.
- WSLc was not used for this experiment; prior `wslc list`/`run` calls timed out. No unrelated processes or containers were stopped. No Docker/WSL/memory configuration changed.
- Scope: method behavior only. No live GUI, model, user, task effects, authority to act, efficiency, or resumption benefit established.
