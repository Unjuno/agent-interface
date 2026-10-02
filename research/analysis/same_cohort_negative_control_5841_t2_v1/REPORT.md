# Issue #5841 T2 — fixture-derived truth-label audit

## Result

Disposition: **PASS_METHOD_SCOPED** for the fixture-derived audit question.

The one-shot raw-only audit returned `PASS_FIXTURE_DERIVED_RAW`: 7/7 cases, all
56 assignment rows, and 56 reconstructed truth-label sets matched the frozen
fixture; errors=0. The five preregistered in-memory corruption tests all
rejected their mutations (6/6 construction/audit tests passed overall),
including a two-label swap that preserves the aggregate primary count.

This supports the narrow conclusion that the retained T1 candidate bytes agree
with truth labels independently reconstructed from the frozen fixture, and
that this auditor detects these five specified label corruptions. It does not
retroactively repair or rerun T1. The candidate, its original auditor, fixture,
raw output, and allocation were not modified or invoked.

## Frozen inputs and execution

- Base main: `4d3c8d3612e3c57f354f5e1be553ae4f5a7801e0`.
- Historical T1 source commit: `4251a270480dbcbfbb019d3d383c22fa9c78a7b2`.
- Copied fixture Git blob: `92b67710be0ed89727536c19e2bef91142812019`; SHA-256:
  `4045621cc774f2f42a0016676cf49f37c78ac392bc6d83d019bddbcc7e733ac7`.
- Retained T1 raw Git blob: `fde80c5c09db5e2f3c571b80df0217166e08117b`; SHA-256:
  `0673f01a93d77d8aa8b940e22006e7af56a8421a87bfbb0e25e4d0269d735a02`.
- Formal command, run once: `python -B research/analysis/same_cohort_negative_control_5841_t2_v1/audit_once.py`.
- Auditor candidate invocations: 0; raw auditor runner: 1; retries: 0; GPU,
  model, GUI, container and service invocations: 0.

The construction suite was run before the raw audit and passed 6/6, including
the five mutation controls (a sequence deviation from the planned post-audit
mutation order; the controls and audit source were frozen before either ran).
The raw-only runner then checked both input hashes before reading either JSON
input. Its original Windows-CRLF output bytes are preserved exactly, base64-
encoded in `AUDIT.raw.json.b64`; the readable `AUDIT.json` is their LF-normalized
view. Original output-byte SHA-256:
`344f3aee830052f3b84367fe753aa4b1ff43f20f1fb6bfaaa05d873ab62fbb03`. No T1
implementation is imported by the raw auditor.

## Scope and limitations

This is a finite, self-authored synthetic design with seven cases and 56 rows.
The fixture and candidate encode the same intended design, so independent
reconstruction does not validate a production benchmark, scorer, route effect,
or the causal validity of a real negative-control endpoint. It only addresses
the specific T1 auditor limitation recorded in #5841 comment 5926505824.

## Reproduction

From the repository root, run the construction tests and then the frozen raw
auditor using the commands above. `FREEZE.json` pins the base commit, input
hashes/blob identities, and source hashes; `SHA256SUMS.txt` records retained
artifact checksums. The raw auditor is one-shot; do not rerun it to replace its
result.
