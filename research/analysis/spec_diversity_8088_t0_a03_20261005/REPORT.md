# Issue #8088 — specification-diverse challenge, T0 A03

## Result

**NO_INCREMENTAL_VALUE_SCOPED** for this eight-contract synthetic packet. Reused blinded adjudication found zero explicit contract-anchored omissions between the primary and challenge decompositions, so no specification-omission mutants were generated. Eight baselines passed; six ordinary controls were rejected, each only on its predeclared clause. The independent raw-only auditor reconstructed 15 explicit obligations over 14 rows with zero disagreements. Formal candidate/auditor invocations: 1/1; retries: 0.

The two corrections prompted by predecessor review are directly covered: C06 records Active and All visible-ID sets separately from stored task state, and its control leaves records unchanged while All remains filtered; C02 binds existing item records to Work and Archive separately, and its control moves a pre-existing Archive record to Work while still adding Pack kit correctly. Both controls fail only the intended clause. Views are compared as ID sets, so no display-order requirement is invented where the contract is silent.

A01 `HOLD_BASELINE_ORACLE_COVERAGE` and A02 `HOLD_C02_LIST_IDENTITY_COVERAGE` remain intact on their distinct PR branches (#8191 and #8198); A03 is a fresh corrected successor, not a rewrite of those one-shot outcomes.

## Method custody

- `COVERAGE_MATRIX.json` maps all 15 obligations to raw fields and predicates. Input contract and primary-decomposition bytes are bound by SHA-256.
- Raw output binds before/after records separately by list and stable item ID, terminal status, and distinct `views.Active` / `views.All` visible-ID snapshots.
- Six frozen ordinary controls: lost persistence; wrong destination; existing Archive→Work relocation; collateral edit; All filter stays Active; success/state change on absent target.
- The candidate and raw-only auditor have separate predicate code; the auditor imports no candidate module and checks each control fails only its declared clause.
- Freeze, run counts, outputs, and hashes: `FREEZE_FINAL.json`, `RUN_RECEIPT.json`, `SHA256SUMS`.

## Runtime and limits

The same-host OrbStack image-inspection failure (`python:3.12-slim`, containerd blob `operation not supported`) was already recorded in A01/A02; no identical retry was made. A03 used native macOS 27.0.1 / Python 3.14.5, standard library, CPU-only. No container isolation or resource-enforcement claim.

All contracts and authorship are synthetic/AI-authored. Distinct contexts used the same configured assistant service; this does not establish human, cognitive, or model-family independence. No live application, user intent, production error rate, efficacy, or current repository audit correctness was tested. This result supports only the finite authored method packet.

## Reproduction

From this directory: `python3 run_candidate.py`, then `python3 run_auditor.py CANDIDATE_FORMAL_OUTPUT.json`, then `shasum -c SHA256SUMS`. These are reproduction instructions; counted formal invocations are the single executions recorded in `RUN_RECEIPT.json`.
