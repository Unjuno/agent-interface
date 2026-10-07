# Issue #7367 — compiler-style evidence-use liveness, T0 A01

**Frozen disposition: `PASS_METHOD_SCOPED`.** The allocation is a deterministic, no-model method experiment on a finite, fully declared workflow graph. It does not establish a model, runtime, token, GUI, or task-success benefit.

## Question and protocol

The hypothesis was that conservative future-use reachability can prune model-visible context in complete declared workflows without removing any fact needed by an enumerated continuation, while an incomplete or open-world graph must abstain. The allocation compared full retention, a fixed recency budget, a simple task-conditioned selector, and graph-based liveness on one frozen corpus containing current and historical observations, supersession, a delayed recovery loop, an unresolved external-effect obligation, and completed irrelevant notes. Candidate reachability traversed branches and a retry cycle to a fixed point. A separately written auditor enumerated four frozen continuations directly.

The protocol, H/T/D/C/U, main commit, image identity, graph digest, and candidate/auditor/workload hashes are frozen in `PRE-RUN.json`. The source checkout used for repository context was clean `main` at `bbed04b9bf5ad7d94e20fcea212b98d19dfa6395`. The previous #7367 environment STOP remains preserved; this A01 began only after fresh WSLc inventory succeeded and a clean current-main checkout was available.

## Result

Independent path enumeration found no future-use misses for liveness. It retained `obs-v1` for historical comparison, `recovery-state` for delayed recovery, the current observation and task intent, and the unresolved external-effect record. It evicted four records with no future consumer in the declared graph. Serialized context fell from 1,029 bytes under `FULL_CONTEXT` to 561 bytes under liveness (45.5% lower).

| Policy | Serialized bytes | Continuations with at least one missing required record |
|---|---:|---:|
| Full context | 1,029 | 0/4 |
| Recency budget (4 records) | 469 | 2/4 |
| Task-conditioned selector | 347 | 2/4 |
| Conservative use liveness | 561 | 0/4 |

The recency and task-conditioned baselines were smaller, but both missed `obs-v1` on the historical-compare continuation and `recovery-state` on delayed recovery. This exposes the tradeoff: explicit liveness preserved those declared consumers at a higher byte count than the simple selectors. Actual tokenizer costs, model quality, graph-authoring overhead, and end-to-end cost were not measured.

All five frozen mutations abstained as `UNKNOWN_KEEP` and evicted nothing: omitted recovery edge, terminal obligation without a receipt, aliased evidence version, current-use changed to historical, and injected dynamic consumer. The independent auditor passed all source/workload hashes, use coverage, dead-record pruning, canonical-record preservation, and mutation checks.

## Execution and limits

The candidate ran once in WSLc using cached pinned `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, one CPU, 256 MiB configured memory, no network, read-only source, and a separate output mount. WSLc warned that swap-limit/cgroup support was unavailable, so this record makes no memory-enforcement claim. Candidate and independent auditor each exited 0. `POLICY_COVERAGE_POSTHOC.json` is a clearly labeled supplemental accounting pass over the preserved raw result; it did not rerun or alter the candidate.

Canonical evidence was retained in the workload and only model-visible residency selections were varied. All results are synthetic and finite. No conversational inference, open-ended user request, persistent-store deletion, model call, runtime, GUI, live action, or task outcome was tested. A finite PASS cannot establish graph completeness for real workflows; dynamic or unknown consumers remain LIVE/UNKNOWN by design.

## Evidence map

- `PRE-RUN.json`: frozen allocation protocol, decision gate, main commit, image, graph digest, and source hashes.
- `workload.json`, `run_a01.py`, `audit_a01.py`: frozen corpus, candidate, and independent oracle auditor.
- `CANDIDATE_COMMAND.txt`, `CANDIDATE_OUTPUT.txt`, `CANDIDATE_EXIT.txt`, `container-out/RAW.json`: exact candidate run and raw record.
- `AUDIT_COMMAND.txt`, `AUDIT_OUTPUT.txt`, `AUDIT_EXIT.txt`, `container-out/AUDIT.json`: independent audit.
- `POSTHOC_COVERAGE_COMMAND.txt`, `POSTHOC_COVERAGE_OUTPUT.txt`, `POSTHOC_COVERAGE_EXIT.txt`, `posthoc_policy_coverage.py`, `container-out/POLICY_COVERAGE_POSTHOC.json`: supplemental baseline miss accounting.
- `SHA256SUMS.txt`: package hashes, excluding itself.
