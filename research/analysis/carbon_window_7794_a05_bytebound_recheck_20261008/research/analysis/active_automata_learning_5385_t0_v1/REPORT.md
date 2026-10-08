# Issue #5385 — bounded active lifecycle learning T0

**Disposition: `PASS_ACTIVE_LEARNING_SCOPED`.** One preregistered, deterministic OrbStack experiment learned all four reachable behavioral classes in one bounded-equivalence round. The learned transducer matched the independently implemented reference on all 2,801 words of length 0–4. This is a finite synthetic result, not real-interface evidence or a safety certificate.

## H / T / D / C / U

- **H:** A bounded active observation-table learner identifies all four reachable, safety-distinguishable lifecycle states within a fixed query budget, while a five-trace hand-authored suite identifies fewer; the learned model remains exploratory and non-authoritative.
- **T:** Four hidden lifecycle classes (`fresh`, `stale`, `half_open`, `comp_pending`), seven action symbols, one active learner, and exhaustive bounded equivalence through depth 4. Independently replay every raw input word against a separate implementation. No GUI, model, network, user data, or task effect.
- **D:** PASS requires all four classes, no counterexample in all 2,801 bounded words, exact independent output agreement, no grant outside `fresh`, <=500 membership queries, a weaker manual baseline, and passing mutation controls. Any unsafe grant or missed bounded distinction is FAIL; evidence/provenance gate failure is STOP.
- **C:** The learner received an exhaustive equivalence oracle over a deliberately small deterministic machine; the fixed five-trace baseline is not an optimized suite. Distinguishing actions were designed into the oracle.
- **U:** No nondeterminism, state aliasing, unreachable hidden states, observation noise, non-resettable membership oracle, expensive query, real GUI/API or strategic agent is modeled. Depth-4 equivalence is not unbounded equivalence. Query count is reported by the frozen runner/runtime guard; the raw-only auditor checks the reported budget field but cannot reconstruct the observation-table query transcript because the runner did not emit it.

## Formal outcome

- Allocation: `active-automata-5385-t0-orbstack-20260930-01`; formal invocation count 1, reruns 0.
- Learner: 4 inferred classes; one equivalence round; 2,801 bounded words; 204 uncached membership queries as reported by the frozen runner (budget 500).
- Manual comparison: fixed five traces exposed 2 terminal response classes, fewer than the learner's 4. This is a deliberately small baseline and supports no general sample-efficiency claim.
- Raw-only audit: `PASS_ACTIVE_LEARNING_SCOPED`; 2,801 rows; 0 errors. It independently replayed each input word and verified every learned output; no `GRANTED` occurred outside `fresh`.
- Mutation controls: changed learned output rejected; dropped word rejected; wrong state-count rejected; reported query budget overrun rejected (4/4).
- Raw SHA-256: `2b99073cdceda44599706696d4d2f11297b653c84074763857d69b075a96d421`.
- Audit JSON SHA-256: `d662092da48b99759977373394525a839de750a2e8c5c49929aed9f116574ffd`.
- Frozen source hashes and preregistration: [`SOURCE_MANIFEST.md`](SOURCE_MANIFEST.md), [`PLAN.md`](PLAN.md), and [Issue #5385](https://github.com/Unjuno/agent-interface/issues/5385).

## Execution and provenance

Source freeze at `2026-09-30T10:08:07Z`; base/main `0cf275c05cc4870d17936bfcff0e8b98539c7cf2`. Formal invocation ran `2026-09-30T10:09:32Z`–`10:09:33Z`; separate audit ran `10:09:51Z`–`10:09:52Z` UTC. OrbStack Docker context, Engine 29.4.0, Linux/arm64, pinned Python 3.12 slim digest; network disabled, read-only root/source, 1 CPU, 256 MiB, 64 pids, all capabilities dropped, no-new-privileges. Exact commands and captured stdout are retained in [`EXECUTION.md`](EXECUTION.md). The `--rm` commands did not request a CID file, so individual container IDs were not captured; no ID is inferred.

The pre-freeze construction smoke was source-development evidence only. Its temporary raw output was not retained and is not used for the disposition. Formal source and raw output were not rerun or modified after the allocation.

## Evidence and boundary

- Candidate learner and synthetic oracle: [`experiment.py`](experiment.py).
- Separate raw-only auditor: [`audit.py`](audit.py); it does not import candidate code.
- Immutable formal words and output traces: [`raw/formal.jsonl`](raw/formal.jsonl).
- Audit summary: [`raw/audit.json`](raw/audit.json).

The result shows that this particular bounded learner can distinguish the four specified states under a strong finite equivalence oracle. It does not establish usefulness, cost, completeness, or safety for an actual interface. No runtime behavior was changed.
