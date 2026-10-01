# Evidence target authority contract v2

## Problem

The OpenTTD expanded-receipt selector v1/v2 requires `target_reference` and one
receipt point. It cannot decline all observed receipts without breaking its
schema. The Mindustry matched block later demonstrated the inverse problem: two
coordinate-free stops both withheld placement correctly, but a diagnostic label
mismatch made the complete block false.

## Candidate

`evidence_target_contract_schema_v3.json` is one flat endpoint-compatible
object. A positive result cites exactly one verified receipt and its printed
point. A negative result uses receipt index zero, an empty points array and
`not_applicable` coordinate semantics. The validator returns one of two
operational authority classes:

- `TARGET_REFERENCE_ONLY`: the selected receipt/point may proceed to ordinary
  focus, surface, freshness, lease and input admission;
- `NO_TARGET_AUTHORITY`: the caller must not issue target button input.

Negative diagnostics remain explicit as `no_match_in_observed_set`,
`ambiguous_evidence`, `unavailable_evidence` or `search_budget_exhausted`.
They do not change the authority class. Eventual task failure also remains
separate from a correct bounded stop.

## Fixed evidence

The local block uses the five retained OpenTTD wrong-anchor recovery receipts.
The known finance receipt produces `TARGET_REFERENCE_ONLY`. All four negative
diagnostics produce `NO_TARGET_AUTHORITY`. Four malformed controls—coordinates
on a negative, a receipt on a negative, a mismatched positive point and positive
receipt zero—are refused.

The same operational mapping is applied to the retained Mindustry matched
results. Positive maps to `TARGET_REFERENCE_ONLY`; its `ambiguous` no-match stop
and `unreadable_evidence` stop both map to `NO_TARGET_AUTHORITY`, while their raw
diagnostics remain unchanged. This does not relabel the prior formal failure.

One preregistered no-GUI endpoint preflight accepts the flat schema in
7,232.759ms. Reported usage is 7,916 input, 107 output and 48 reasoning-output
tokens. Windows and WSL audits pass; there are no GUI artifacts.

## Decision

The contract now has one fresh [OpenTTD live pair](OPENTTD_EVIDENCE_AUTHORITY_PAIR_V2.md).
Positive selects and opens Company Finances; a target absent from the same five
receipts returns `NO_TARGET_AUTHORITY` and issues zero target buttons. Retain the
contract. Natural error rate, broad task reliability, causal speed and token
saving remain unmeasured.

Primary artifacts:

- `results/evidence-target-contract-v2-01/preregistration.json`
- `results/evidence-target-contract-v2-01/report.json`
- `results/evidence-target-contract-v2-01/audit.json`
- `evidence_target_contract_schema_v3.json`
- `evidence_target_contract_v2.py`
- `test_evidence_target_contract_v2.py`
