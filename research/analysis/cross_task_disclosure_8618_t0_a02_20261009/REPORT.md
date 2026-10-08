# Issue #8618 — recipient-bound cross-task disclosure gate, T0 A02

**Disposition: `PASS_METHOD_SCOPED`.** On 14 finite synthetic recipient-effect cases, the gate emitted zero unauthorized secret-specific effects, while the instruction-only comparison emitted seven. The independent auditor reconstructed the recipient-visible requests and task outcomes from the saved raw output and a separate oracle fixture.

The gate allowed exactly two secret-specific disclosures, for the distinct values `red` and `blue`, each with a matching source, recipient, purpose, task, and verified lineage. Seven non-release cases with an independently certified equivalent general action completed through that action. The public/no-secret control passed. The action-capability denial control emitted no effect. The gate returned ASK/UNKNOWN for missing authority, invalid equivalence, forged lineage, or absent action capability.

The separate construction mutation suite rejected all four source-binding, recipient-binding, dependency-binding, and payload-effect mutations. It is construction evidence, not part of the formal candidate run. A01's separate runner preflight STOP is preserved at [A01 report](../cross_task_disclosure_8618_t0_a01_20261009/REPORT.md); A01 had zero candidate/auditor invocations and was not retried.

## Frozen scope and execution

A02 is allocation `8618-T0-A02-20261009`, frozen at `1da256503e76e133f8af598a452fe8532a4ed004` on base main `3dc1f09a8bb3bd5498bba2936f5965ce3024b2ce`. Main later advanced to `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`; the experiment remained on its fixed source because it is an authored fixture contract and imports no repository runtime. The branch incorporated that later main commit only after the formal run for evidence-index integration; the recorded freeze and run source remain unchanged.

The candidate and the separate auditor each ran once under macOS `sandbox-exec` with `(deny network*)`; candidate and auditor both exited 0. The candidate ran 56.455 ms and the auditor 59.510 ms by the wrapper's monotonic clock. Their UTC start/end times, exact argv, stdout/stderr hashes, raw hash, audit hash, and freeze commit are in [execution receipt](raw/execution_receipt.json). The raw candidate file is [candidate.jsonl](raw/candidate.jsonl); the independent result is [audit.json](audit/audit.json). No container, model, GUI, user, or external service was used. OrbStack's read-only Docker inventory failed before any launch; see the retained [probe](../cross_task_disclosure_8618_t0_a01_20261009/construction/orbstack_probe.txt).

Formal source and input hashes are fixed in [FREEZE.json](FREEZE.json). The candidate did not read the oracle. The independent audit used the recipient request recorded in raw output and the separately frozen oracle's release authorization, task-correct action set, and equivalent-general truth.

## H / T / D / C / U

- **H:** A recipient-bound declassification gate can prevent unauthorized secret-specific recipient-visible effects while retaining task completion through a secret-independent equivalent action and allowing an exact explicit grant.
- **T:** Exhaustively evaluate 14 authored cases spanning no secret/public control, two secret values, absent and matching grants, wrong source/recipient/purpose, missing or forged lineage/dependency, absent or forged equivalence, no equivalent route, and missing action capability. Compare instruction-only and gated admissions over the same proposed actions; the independent auditor evaluates actual recipient-visible requests.
- **D:** PASS_METHOD_SCOPED required zero unauthorized gated secret effects, a positive baseline leakage control, exactly two valid releases across `red` and `blue`, seven equivalent non-release completions, public and capability controls, and fail-closed invalid/no-equivalence cases. These conditions all passed. The predeclared FAIL/HOLD/stop rules remain in [FREEZE.json](FREEZE.json).
- **C:** Prompt-only choice or public information may already suppress disclosure; the general path may explain successful completion; the gate can overblock. Authority and signatures are represented by fixture fields rather than real cryptographic verification.
- **U:** This establishes only the declared finite synthetic source-to-effect contract. It does not show opaque-model causal influence, real cryptographic verification, GUI/browser/user behavior, production privacy, comprehensive noninterference, or general covert-channel coverage. The semantic equivalence and recipient oracle are authored fixture truths.

## Reproduction boundary

Reviewers can rerun the audit against the retained raw output (without invoking the candidate) using the frozen command recorded in `FREEZE.json`. Do not rerun the candidate allocation. The complete package, including construction history and formal raw, is checksummed in [SHA256SUMS](SHA256SUMS).
