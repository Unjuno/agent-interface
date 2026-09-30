# Dependency-aware verifier quorum: finite contract analysis (Issue #5314)

## H / T / D / C / U

**H — hypothesis.** Counting raw verifier responses can admit a PASS when several responses share one failure domain. Crediting distinct, verified dependency domains should reduce false decisions, at the cost of more abstentions. Self-declared independence is only as reliable as its metadata.

**T — test.** Freeze: `b0190453a787102189429e4b8c32032cf60efd17`. Exhaustively enumerate every set partition of five verifier identities (52 partitions), every binary vote assignment constant within each domain (454 partition/assignment structures in total), and both ground-truth values (908 rows). Compare 3-of-5 raw count, 3-distinct-declared-domain count, 3-distinct-verified-domain count, and the same verified-domain rule with fail-closed missing metadata. There are no sampled runs, random seeds, or implicit probability weights.

**D — result.** The first audit (`audit.json`) is retained unchanged but is insufficient on its own: it independently recomputed policies for rows present, yet did not enforce complete-universe coverage. The one-row-deletion regression reproduced v1 returning `PASS_FINITE_CONTRACT_ONLY`; this is a real audit-control failure, not a simulation result. The raw itself has 908 distinct case signatures over all 52 partitions.

An additive raw-only audit v2 independently enumerated partitions via restricted-growth strings (a different algorithm from the candidate enumerator), checked the exact 908-case universe with no missing/extra/duplicate rows, validated dependency labels and policy outputs, and passed 6/6 effective mutations. It found zero discrepancies on the original raw SHA-256; the simulator was not rerun and `raw.json` was not modified. Only v2 supports the scoped disposition below. On the stipulated complete-and-accurate domain universe:

| Policy | False PASS | False FAIL | UNCERTAIN | Correct determinate outcome |
|---|---:|---:|---:|---:|
| COUNT_QUORUM | 227 | 227 | 0 | 454 |
| DECLARED_INDEPENDENT | 91 | 91 | 544 | 182 |
| DEPENDENCY_AWARE | 91 | 91 | 544 | 182 |
| FAIL_CLOSED_UNKNOWN_DEPENDENCY | 91 | 91 | 544 | 182 |

The reduction is a deterministic consequence of counting each shared domain once: dependency-aware PASS/FAIL sets are subsets of raw-count PASS/FAIL sets. The price in this finite universe is abstention on 544/908 cases. These are exhaustive case counts, **not probabilities, error rates, or deployment estimates**. With accurate metadata, declared-domain and verified-domain policies coincide by construction; the enumeration does not establish that metadata can be measured or trusted in a real system.

Four independent probes behaved as preregistered: duplicating one shared-domain PASS could make raw count PASS while dependency-aware returned UNCERTAIN; forging distinct self-declared labels did not change verified-dependency admission; missing one dependency record forced fail-closed UNCERTAIN despite a raw PASS; and accurate declared labels matched verified-domain output.

**C — cost / risk.** This is a standard-library, host-side exact finite analysis, not a Docker run. No OS, application, GUI, model, real verifier, tool, backend, latency, monetary cost, or availability workload was exercised. Docker/OrbStack CLI remains prohibited by #5085 pending an exact coordinator allocation; no Docker command was issued for this study. The simplifying premise—that each verifier has a complete, correct dependency domain and all verifiers within a domain emit the same vote—is deliberately strong and not empirically validated. The preserved v1 audit failure is part of the evidence and must not be silently upgraded or overwritten.

**U — unknowns.** Which domains are observable and independently attestable? How do overlapping dependency sets, partial provenance, stochastic within-domain errors, domain outages, and different costs change the tradeoff? Does any useful threshold preserve availability without overclaiming safety? These require a separately frozen follow-up and, where environment-dependent, a coordinator-authorized isolated container experiment.

## Interpretation and limits

Disposition: `PASS_FINITE_CONTRACT_ONLY`. The result supports a narrow contract point: response count alone does not encode independence, and treating an unverifiable dependency record as independent is unsafe under the explicit probes. It does not establish Byzantine quorum safety, real-world independence, verifier correctness, security efficacy, or that domain-aware quorums should be integrated. No authority, task-success, release, or external-effect claim follows.

## Reproduction and retained audit history

With Python 3.12.10 or compatible standard-library Python, use the retained `raw.json` as the input to `python audit_v2.py`; run `python -m unittest -v test_audit_coverage.py` for coverage regressions. `audit.json` is the original v1 outcome and intentionally remains unchanged. `audit_v2.json` is the corrected independent audit of exactly the same raw SHA. The v1 gap test records the observed false PASS. Do not overwrite either retained audit or the first-run raw to repair a future gate failure; any new simulation belongs in a separately frozen successor allocation.
