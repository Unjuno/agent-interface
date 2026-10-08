# Issue #5766 T0 — bracketed semantic oracle checks

## H / T / D / C / U

**H.** A fixed reference deck will detect an in-deck semantic change even when the same scorer bytes still return well-formed output; a semantically equivalent scorer version will not trigger HOLD, and drift beyond deck coverage will remain unknown.

**T.** Frozen synthetic fixture, five check-standard cases (positive, wrong target, collateral, unsaved, UNKNOWN), three candidate records, and four scenario variants: nominal, unchanged-meaning scorer version `s2-equivalent`, in-deck semantic drift with scorer `s1` unchanged, and drift outside deck coverage. The independent auditor reconstructs labels, pre/post bracket, candidate row dispositions, and promotion/hold status without importing `run_t0.py` or `scorer_v1.py`.

**D.** `PASS_METHOD_SCOPED`: 6/6 mutation/construction tests passed; audit returned no errors. The in-deck changed meaning produced one would-be false PASS and was held before promotion; equivalent scorer-version change was accepted; outside-deck drift remained `UNKNOWN_COVERAGE`. Five deck rows and four scenarios were reconciled.

**C.** Synthetic categorical scorer only; the scenario's changed artifact semantics are represented by a frozen changed observation while scorer source bytes remain fixed. Host-only CPython run; no Docker/OrbStack allocation for this task was found in #5085, so the preferred isolated-container rung was not attempted. No GUI, model, network, user data, or runtime action.

**U.** This validates only the finite protocol fixture and mutation cases. It does not show that any deployed scorer has drifted, that real check decks are independent or representative, or that an app-version transition is detected outside the enumerated cases. T1 feasibility and human adjudication remain open.

## Exact execution and first failure

Base main: `24864b1e4bb4a6f86c7061876a67a8bd7a1426a1`. Runtime: Windows PowerShell, CPython 3.11.9. Final command sequence is recorded verbatim in `FREEZE.json`. Final unittest: 6 passed in 0.002 s; runner exit 0; independent audit:

```json
{"deck_cases":5,"equivalent_version_rejected":0,"errors":[],"false_promotions_blocked":1,"out_of_deck_disposition":"UNKNOWN_COVERAGE","scenarios":4,"schema":"oracle-bracket-5766-audit-v1","status":"PASS_METHOD_SCOPED"}
```

The first audit attempt failed one test because the scorer SHA comparison was case-sensitive (uppercase frozen hex versus lowercase `hexdigest`). The audit normalized digest case, then all six tests and the audit passed. The first failure is retained here; no candidate or formal/live experiment was retried.

## Reproduction

From this directory, run `python -B -m unittest -v test_audit.py`, `python -B run_t0.py`, then `python -B audit_t0.py`. The runner writes `raw.json`; the independent auditor writes `audit.json`. File identities are recorded in `FREEZE.json` and `SHA256SUMS`.
