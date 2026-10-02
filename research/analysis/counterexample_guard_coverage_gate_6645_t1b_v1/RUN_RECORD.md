# T1b formal run record

- Allocation: `CGCG-6645-T1B-ORB-20261003-01`.
- Frozen base: `52c42c40bb074f46db1dc74afb20508e68bc1282`.
- Candidate container: `dad11994117da104b03f0912dd8d2e06814904b7b44c07573d35fcf7dfb00413`, one invocation, exit 0, `OOMKilled=false`.
- Auditor container: `024e3d08482160273692175679bc258373d81239760548a655f698c7c18b7e0c`, one invocation, exit 0, `OOMKilled=false`.
- Retries: 0. Exact pinned image and all pre/post inspections, IDs, stdout/raw, stderr and exit codes are retained below `results/formal_01/`.
- The candidate container's sole read-only bind mount is `candidate_input/`; it cannot read `oracle.json`. The auditor has the package read-only mount.
- Independent audit: `PASS_COVERAGE_GATE_ISOLATED_SCOPED`, five rows, zero errors.

## Paired outcome

| Candidate-visible case | Gate disabled | Gate enabled | Independent oracle |
|---|---|---|---|
| Complete-coverage valid control | ADMIT | ADMIT | safe |
| Complete-coverage stale-target control | REFUSE | REFUSE | harmful |
| Hidden modal, incomplete coverage | ADMIT | UNKNOWN | harmful |
| Observationally identical hidden-modal control | ADMIT | UNKNOWN | safe |
| Unregistered surface family | ADMIT | UNKNOWN | unknown |

The candidate-visible observations for the hidden harmful and safe rows are
identical; the oracle label and hidden modal truth are not mounted into the
candidate container. The only candidate intervention is the coverage gate
boolean. This is the counterfactual distinction missing from the predecessor
T1 and is an independently frozen allocation, not a rerun of that result.

All limit values are Docker configuration evidence only; host/cgroup memory or
swap enforcement was not measured.
