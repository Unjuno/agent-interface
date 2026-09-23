# Candidate after-state validation before publication

Issue #395. Additive research only; no shared runtime/workflow/history edits.

## Question

After read dependencies, write scope, write-target preconditions and current-OID CAS are correct, can a malformed candidate that remains inside the allowed path still be published?

## Design

The local allocation was frozen before measurement at commit `b178331f1e3348a6aea538441b6030ed5a256695` from publication base `0dd239b7db10831a4e8ac078d3a32d4be6370e3d`. GitHub write actions were unavailable during execution, so this later publication is explicitly not remote preregistration.

Two policies were applied to byte-identical paired Git candidates:

1. `scope_only`: enforce read/write conflict checks, declared changed path and final current-OID CAS;
2. `scope_and_postcondition`: the same checks plus exact requested after-state validation of the modified entry before publication.

Twelve authored scenarios include correct publication, unrelated-state preservation, read/write/ref races, no-op/extra-change candidates, wrong bytes, wrong file mode, wrong entry kind and target deletion. Three repetitions per policy/scenario = 72 first outcomes. No measured ID was rerun.

## Result

| Policy | Correct | Applied | Refused | Wrong publications |
|---|---:|---:|---:|---:|
| scope only | 24/36 | 18 | 18 | 12 |
| scope + postcondition | **36/36** | 6 | 30 | **0** |

The scope-only control publishes all 12 malformed within-scope candidates. The candidate rejects those 12 while preserving the six valid publications and all conflict/refusal controls. `36/36 correct` means 6 valid commits plus 30 correct refusals, not 36 task executions.

## Verification

Independent audit uses retained Git loose objects and Python standard-library parsing rather than the candidate's publication checks. Replay is byte-identical for all 72 rows. Seventeen tests pass before freeze and after independent extraction. All 2,192 evidence files match the retained manifest. The paired 36 candidate objects are byte-identical across policy arms.

Source SHA-256: `experiment.py` e58f44d2d041bf1d5ea6457500831bbd6d5edc96ec43429e3ee8660745588cad; `audit.py` a41d0321279c8b205c3a91dd7e7bd651c25c5c468ba6462e8eb00758418b8bb0; `test_contract.py` 2939c6cc3e7f14925eba93040f62bc8d63eef97378b1e16d059d33945b2e8d9c.

Full raw evidence is conversation-only: 258,016 bytes, SHA-256 `96674054f2042e257e8d88053ab8fed40077a056311e405ca9a0c959a750a990`.

## Decision and boundary

RETAIN the scoped mechanism for stageable immutable candidates: validate the proposed after-state, then publish exactly the inspected candidate under identity-bound CAS.

HOLD any claim that this solves irreversible effects, automatic semantic-postcondition discovery, arbitrary GUI actions, production integration or speed. A candidate object can be validated before publication; a click, network request or other external side effect may only be judgeable after execution and therefore needs a different contract.
