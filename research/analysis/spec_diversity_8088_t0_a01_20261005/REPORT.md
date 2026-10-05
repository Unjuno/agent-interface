# Issue #8088 — specification-diverse challenge, T0 A01

## Result

**NO_INCREMENTAL_VALUE_SCOPED.** The blinded challenge and third-party contract-only adjudication found zero explicit contract-anchored obligations omitted by the primary decomposition across eight synthetic task contracts. All differences were harmless partition/wording or unresolved ambiguity; none justified an omission mutant. No ambiguity was promoted to a requirement.

The formal candidate emitted 8 baseline cases and 4 ordinary implementation controls. All 8 baselines passed and all 4 controls were rejected. The separately implemented raw-only auditor independently recomputed all 12 rows, reported zero discrepancies, and exited successfully. Candidate and auditor each ran exactly once after freeze; retries: 0. The experiment demonstrates no incremental value for this bounded packet, not that diverse review has no general value.

## Provenance and scope

- Frozen contract packet: `CONTRACTS.json` (8 synthetic requests, exact initial state and explicit reload boundaries).
- Primary and challenge decompositions: `SPEC_A_PRIMARY.json`, `SPEC_B_CHALLENGE.json`; the challenge was published before the primary output was retrieved.
- Blind third role: `ADJUDICATION.json`; it received only contracts and both decompositions, not code or outcomes.
- Predeclared omission generation: one mutant per adjudicated explicit omission in destination, persistence, forbidden-side-effect, or UNKNOWN handling. Adjudicated omission count was zero, so no challenge omission mutant was generated.
- Ordinary controls: lost persistence, wrong destination, forbidden collateral edit, and incorrect missing-target handling. All four were rejected by the primary-spec scorer.
- Independent raw audit: `run_auditor.py` reconstructs clause outcomes from raw state transitions and contract bytes without importing candidate code.
- Formal outputs and invocation custody: `CANDIDATE_FORMAL_OUTPUT.json`, `AUDITOR_FORMAL_OUTPUT.json`, `RUN_RECEIPT.json`.
- Hashes: `SHA256SUMS`; pre-execution source/input freeze: `FREEZE_FINAL.json`.

## Runtime and limitations

OrbStack Docker 29.4.0 (`linux/aarch64`) was reachable, but inspecting `python:3.12-slim` failed with containerd blob `operation not supported`. Per the issue's stdlib-only method scope, execution used native macOS 27.0.1 / Python 3.14.5, CPU-only. This is not container isolation or resource-limit evidence.

The eight contracts and all authorship are synthetic/AI-authored. Separate author/adjudicator contexts used the same configured assistant service; this does not establish human, cognitive, or model-family independence. No real user intent, application behavior, production audit error rate, or general efficacy is measured. C05, C06, C07 and unspecified failure outcomes remain explicitly unresolved where the contract does not decide them.

## Reproduction

From this directory, with Python 3 standard library:

```sh
python3 run_candidate.py
python3 run_auditor.py CANDIDATE_FORMAL_OUTPUT.json
shasum -c SHA256SUMS
```

The commands above describe reproduction only; the formally counted candidate and auditor invocations are the single executions recorded in `RUN_RECEIPT.json`.
