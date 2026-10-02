# Audit-only construction history

- Attempt 1: Docker build check stopped on a Python syntax error in the independent evaluator; no formal auditor invocation.
- Attempt 2: after syntax correction, the build check used the candidate package's cases.json path instead of the frozen raw.json; no formal auditor invocation.
- Correction: point the build check at the frozen raw.json and scope safety invariants to the RESTORE_PLUS_DIFF policy while requiring every policy's adverse outcomes to be reported accurately.
- Attempt 3: `BUILD_PASS rows=32 downstream_success_gate=present mutations=4` in OrbStack Docker. The one-shot posthoc audit had not run at the time of this record.
