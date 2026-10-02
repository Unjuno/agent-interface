# Issue #5941 successor T0 — allocation-02

## H / T / D / C / U

- **H:** A count-only 2-of-3 quorum can falsely PASS when V2 repeats a wrong V1 first-pass verdict after peer exposure. An exposure-aware rule that counts only valid, unexposed first-pass receipts should refuse that copied-vote witness as `UNKNOWN_INDEPENDENCE`, while shared raw observation alone remains eligible under this dynamic-edge rule.
- **T:** Enumerate all 8 PASS/FAIL triples × 4 V2 exposure classes (`none`, `peer_verdict`, `raw_observation`, `unknown`) × 2 commitment states = 64 rows, plus 2 explicit omitted/forged-edge controls. Independently preassign balanced truth by verdict-triple index parity; truth is not computed from the vote count. Candidate emits both raw and scoped outcomes. A separate auditor reconstructs each decision from raw fields and runs six mutation controls.
- **D:** `PASS_METHOD_SCOPED` only if 66 ordered rows reconcile; independent raw audit has no errors; the planted peer-exposed copied-vote case is raw-quorum PASS but scoped UNKNOWN; shared-raw exposure is not treated as peer exposure; unknown/invalid commitments get no credit; and all six mutation controls are effective and rejected, especially exposure promotion and commitment invalidation. Otherwise retain HOLD/FAIL without retry.
- **C:** Static failure-domain filters, independently captured call-boundary commitments, or non-voting cross-review may prevent double-credit without this dynamic edge rule. Two independent but correlated errors can still produce a false scoped quorum.
- **U:** Fully synthetic three-verifier/one-receiver finite model. Exposure/commitment capture is trusted. No LLM conformity, runtime integration, call-boundary attestation, GUI/task effect, performance, human, or production claim.

## Freeze and execution boundary

Main at start gate: `b54ec8fac5d005d510a5787d98b9ad7a24d96923`. Distinct successor allocation/path from allocation-01 and PR #5954. Windows CPython standard-library host CPU. Candidate `python runner.py` once; raw-only auditor `python audit.py raw-candidate.json` once after exit 0; zero retries. No Docker/GPU/model/GUI/network/input. The desktop-linux Docker context is visible but daemon API timed out in a 10-second read-only probe; no shared resource is touched. Construction tests must show an independent truth factor, an actual raw false-quorum witness, and decision-changing exposure/commit controls before source freeze.
