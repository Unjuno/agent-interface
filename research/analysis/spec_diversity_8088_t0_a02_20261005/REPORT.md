# Issue #8088 — specification-diverse challenge, T0 A02

> **Post-run correction:** This preliminary `NO_INCREMENTAL_VALUE_SCOPED` conclusion is superseded. C02 compares flattened Work+Archive sequences, so an existing item moved between lists could pass. A02 is `HOLD_C02_LIST_IDENTITY_COVERAGE`; outputs and one-shot counts remain unchanged. See [POST_RUN_QUALIFICATION.md](POST_RUN_QUALIFICATION.md); no rerun was made.

## Result

**NO_INCREMENTAL_VALUE_SCOPED** for this eight-contract synthetic packet. The reused, pre-execution, blinded adjudication found zero explicit contract-anchored omissions between the primary and challenge decompositions, so no omission mutants were generated. All 8 baselines passed, all 5 ordinary implementation controls were rejected only on their named clause, and the independent raw-only auditor reconstructed 15 explicit obligations across 13 rows with zero errors. Candidate and auditor each ran exactly once; retries: 0.

Crucially, C06 now records both `views.Active` and `views.All` as raw visible-ID snapshots, separate from stored records. The fifth control leaves all records unchanged but keeps the All view filtered to Active IDs; both scorer and independent auditor reject it specifically on `all_visible_exact`. This repairs A01's untested C06 gate; it does not erase or reinterpret A01, whose outputs remain preserved under its `HOLD_BASELINE_ORACLE_COVERAGE` qualification.

## Method custody

- A02 is a fresh allocation/branch/path. It reuses the exact logical contract JSON values and the previously sealed primary/challenge decomposition and blinded adjudication; the contract text transfer normalized one terminal blank line and the A02 byte digest is explicitly recorded in `PREDECESSOR.json` and `COVERAGE_MATRIX.json`.
- `COVERAGE_MATRIX.json` maps all 15 explicit obligations to raw fields and predicates, including separate C06 Active/All snapshots.
- `run_candidate.py` emits raw before/after records, outcome and view snapshots, then scores from the frozen primary-derived coverage matrix.
- `run_auditor.py` independently reconstructs those clauses from raw output; it imports no candidate module and verifies hashes, path coverage, baselines, and each single-clause control.
- Final freeze, exact input/source hashes, construction history, and formal invocation counts are in `FREEZE_FINAL.json`, `SHA256SUMS`, and `RUN_RECEIPT.json`.

## Runtime and limits

OrbStack image inspection had already failed on the same host in A01 with `containerd blob operation not supported`; A02 did not retry that unchanged preflight. This run used native macOS 27.0.1 / Python 3.14.5, standard library, CPU-only. No container isolation or resource-enforcement claim.

All task contracts and authorship are synthetic/AI-authored. Authors/adjudicator were distinct contexts on the same configured assistant service; no human or model-family independence is established. No real app, user intent, production error rate, efficacy, or current repository audit correctness is measured. Unresolved contract ambiguities remain unresolved.

## Reproduction

From this directory: `python3 run_candidate.py`, then `python3 run_auditor.py CANDIDATE_FORMAL_OUTPUT.json`, then `shasum -c SHA256SUMS`. Those are reproduction instructions; the formal invocations counted for A02 are the single executions recorded in `RUN_RECEIPT.json`.
