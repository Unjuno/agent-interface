# Reversibility horizon #6695 — T0

Protocol frozen before formal execution. The executed outcome is recorded in [REPORT.md](REPORT.md); the frozen source identities and invocation record are in [RUN_RECORD.md](RUN_RECORD.md).

## H / T / D / C / U

**H.** Holding proposals, signal streams, deadlines, and simulator states fixed, a reversible prepare followed by commit after informative GUI feedback reduces wrong-target/content irreversible commits versus immediate commit. The extra observation arm should add value only when its second signal changes information; it must remain within the frozen deadline tolerance.

**T.** A deterministic finite state machine compares `IMMEDIATE`, `STAGE_1`, and `STAGE_2` on four authored trace strata: informative correction available at signal 1; uninformative signals; informative second signal only; and informative signal with no correction route. Each frozen trace is crossed with all policies. The candidate emits every transition and classification. An independent standard-library auditor reconstructs expected outcomes without importing candidate code. Fixed exhaustive schedule: 4 strata × 3 policies = 12 first outcomes. No repeated pseudo-replicates or statistical-rate inference. One candidate invocation, one audit invocation, zero retries. Construction tests are separate and occur before freeze.

**D.** `PASS_SCOPED` only if STAGE_1 has strictly fewer wrong irreversible effects than IMMEDIATE in the signal-1-informative/route-available stratum; STAGE_2 has strictly fewer than STAGE_1 in the delayed-information stratum; neither stage policy exceeds the preregistered 5% deadline-miss margin overall; and uninformative/no-route controls show zero error reduction from staging. Otherwise `FAIL_SCOPED`; malformed/missing traces, unverified informativeness, or audit disagreement are `HOLD/STOP`, never silently recoded.

**C.** Freshness/VOI policy, ordinary transaction verification, deadline enforcement, and the authored correction-route semantics can explain the same outcomes. This deliberately does not compare broad utility or option-value policies from #5428.

**U.** Hand-authored deterministic simulator only; no GUI, model, user data, real effect reversibility, calibrated signal, natural failure rate, or product/runtime claim. Signal and route semantics are stipulated, not empirically inferred.

## Frozen protocol

- Parent main at intake: `8c06589df` (full SHA recorded in RUN_RECORD after launch).
- Runtime: WSL 3 / Arch Linux / native WSLc, local pinned `python:3.12-slim` image; pull never, network none, CPU 1. No GPU required for this CPU-bound finite enumeration. Record any cgroup/swap enforcement warning; do not infer effective limits.
- Formal IDs: one fixed trace per stratum/policy; no replacements, retries, or tuning after freeze.
- Output: newline-delimited immutable candidate raw plus independent audit JSON and SHA-256/byte counts in RUN_RECORD.
- No live GUI follow-up is authorized by this T0 result.

## Reproduction

From this directory in WSLc, with the frozen Python image mounted read-only:

```sh
python -m unittest -v test_reversibility_horizon.py
python experiment.py --out results/formal_01/candidate/raw.jsonl
python audit.py results/formal_01/candidate/raw.jsonl --out results/formal_01/auditor/audit.json
```

The formal candidate and audit invocations were each run once after the GitHub freeze comment. These commands document reproducibility; they are not permission to replace or rerun the retained allocation. Construction tests do not consume formal IDs.
