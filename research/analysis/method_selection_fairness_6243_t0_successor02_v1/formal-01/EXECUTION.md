# Formal execution receipt — allocation 02

- Allocation: METHOD-SELECTION-FAIRNESS-6243-T0-SUCCESSOR-02-20261002
- Issue: #6243; predecessor allocation remains preserved as FAIL_AUDIT_GATE.
- Date: 2026-10-02 local session; UTC clock reported 2026-10-01T21:28:15Z.
- Runtime: OrbStack Docker context orbstack; image python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b, linux/arm64.
- Isolation: --network none, 1 CPU, 512 MiB memory, 64 PIDs, read-only root filesystem, 64 MiB /tmp tmpfs; only the frozen package bind-mounted.
- Formal candidate invocation: 1, exit 0. Formal auditor invocation: 1, exit 0. Retries: 0.
- Auditor decision: METHOD_PASS_SCOPED; attempts=24; scenarios=4; errors=0; mutation controls rejected=4/4.
- No existing containers or OrbStack VMs were inspected, stopped, signalled, or modified by the run.

Exact command (workspace mount path shortened here; execution used the task's outputs/method_selection_fairness_6243_t0_successor02_v1 directory):

```sh
docker run --rm --name method-selection-6243-t0-s02-formal01 --network none --cpus=1 --memory=512m --pids-limit=64 --read-only --tmpfs /tmp:rw,size=64m --mount type=bind,source=<workspace>/outputs/method_selection_fairness_6243_t0_successor02_v1,target=/work -e PYTHONDONTWRITEBYTECODE=1 -w /work python:3.12-alpine@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b sh -c 'cd /work && python3 candidate.py > formal-01/candidate_stdout.txt 2>&1 && python3 auditor.py > formal-01/auditor_stdout.txt 2>&1 && cp candidate_result.json formal-01/candidate_result.json && cp audit_result.json formal-01/audit_result.json'
```

SOURCE_SHA256SUMS identifies the candidate, auditor, fixture, coders, plan,
construction failure record, and construction outputs mounted for this run.
Stdout files are captured raw process outputs; JSON files are copied verbatim
from the mounted execution directory after successful process exit.

Scope: this confirms the frozen synthetic accounting fixture and auditor
gates. It is not a human or GUI experiment and cannot estimate real task
performance or establish a causal method effect.
