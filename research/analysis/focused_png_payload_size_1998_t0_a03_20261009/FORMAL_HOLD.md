# A03 formal first outcome — `HOLD_RUNNER_EXIT_UNCAPTURED`

The frozen candidate was invoked exactly once under the declared macOS network-deny sandbox and wrote `results/candidate_raw.json` (561,847 bytes). The file parses as JSON and contains the declared allocation/schema with 23 rows. `results/candidate.stderr` is empty. Its SHA-256 is `e7d7f1012006fc105c3aa83c6c7311eb41d240bdedfa9acc1bd13d0337b1f3ac`.

The surrounding zsh runner then failed while assigning the process result to the shell's read-only special variable `status`; it emitted `zsh:1: read-only variable: status`. That prevented capture of the candidate process exit code and completion timestamp. The raw bytes and empty candidate stderr are preserved unchanged. Candidate exit status is **unknown**, not inferred from JSON parseability.

The frozen protocol permits one auditor invocation only after candidate exit 0 is confirmed. Therefore formal auditor invocations are 0; the auditor was not run. Candidate invocations are 1, retries 0. No scientific method PASS/FAIL or byte-saving conclusion is claimed from this allocation. The output is retained as unaudited candidate data only. The allocation is consumed and must not be rerun.
