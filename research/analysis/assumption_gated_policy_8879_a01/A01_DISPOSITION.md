# A01 first outcome — audit failed; preserve without retry

Allocation: `8879-assumption-gate-a01-wsl-native-20261012-01`
Frozen source commit: `63864aabb3ac06e77824b902230847fb97c5cb88`
Disposition: **`FAIL_AUDIT_CONSTRUCTION`**. No `PASS_METHOD_SCOPED` or scientific hypothesis result is claimed.

## Execution record

- Runtime: Ubuntu on WSL 2, WSL package 3.0.1.0, Linux `6.18.40.1-microsoft-standard-WSL2`, CPython 3.12.3. Docker was not used. Source copies and output were on `/home/taka/research-runs/8879-assumption-gate-a01-wsl-native-20261012-01/`; no package installation, model, GUI, network, input, or container was used.
- Candidate invocation: `/usr/bin/python3 source/candidate.py result.json`; exit 0, stdout `candidate_written`.
- Independent auditor invocation: `/usr/bin/python3 source/audit.py result.json audit.json`; exit 1. It stopped at `assert len(violations) > 0` in `check()`. No audit JSON was written.
- Candidate result SHA-256: `a4c495506003e02ba0f17ce3c88e596025a82a5d08850f2168b1f8e506d67817`.
- Frozen candidate SHA-256: `681c76f7cf01835545342cc6e9bf3e5f06d87523b55cced1dbfa638d3e642ffa`.
- Frozen auditor SHA-256: `13b4257f61c788b7dda42dbccfe81140da15772c65c798cce79fec5895e9f977`.

The byte-exact candidate JSON is retained as `result.json`. The failed auditor traceback is retained in the execution transcript and summarized above; an exact stderr file was not produced by the first invocation and is not reconstructed or represented as raw bytes here.

## Diagnosis from frozen source and retained rows

The result contains all nine reachable histories. At the empty history, both one-bit observation marginals are `0`; after either value of `left`, the conditional marginal of `right` is `1/2` (and symmetrically). Thus the retained rows contain the intended diminishing-returns counterexample. However, both candidate and auditor use the same reversed history-containment predicate while enumerating violations. They therefore return an empty violation list; the candidate incorrectly selects `greedy`, and the auditor's explicit planted-control assertion fails. The independent raw-row reconstruction was not successfully completed by this implementation.

This is a construction/audit failure, not support for or against adaptive submodularity or policy selection. The frozen A01 source, first output, exit status, and failure remain unchanged. No candidate or auditor retry was made. Any future work must use a separately frozen successor with a genuinely corrected independent oracle and a new allocation identity; it may not overwrite or pool this result.
