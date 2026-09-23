# Typed effect outcome contract v2

Task `EFFECT-OUTCOME-CONTRACT-V2-CONSTRUCTION-20260916-001`, Issue #477.
Construction base: `81fed4e536dab1a78f6e3ea5529a6fd145dea57c`.

Decision: **`PASS_CONSTRUCTION_CANDIDATE_V2`**.

## Evidence-driven change

V1 preserved pre-effect versus post-effect outcomes and retained wrong-effect history after compensation. The next retained formal rung showed a narrower bug in the meaning of `compensation_verified`: checking only the primary target was truthful 20/30, while checking the full declared `(primary, collateral)` invariant was truthful 30/30. All ten collateral-damage rows were falsely called fully compensated by the primary-only policy.

V2 therefore changes one contract boundary only. Post-contradiction compensation receives:

- unique named `InvariantRequirement(name, expected)` entries;
- unique named `InvariantEvidence(name, observed, independently_verified)` entries.

`compensation_verified=True` is allowed only when every required invariant has present, independently verified, matching evidence. Missing, unverified or contradicted required evidence yields `EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE`. Historical `effect_occurred=True`, contradiction and ordered wrong-effect/compensation history remain first-class in both complete and incomplete outcomes.

Extra evidence is retained in status but cannot substitute for a missing declared requirement. Empty requirement sets and duplicate requirement/evidence names fail closed.

## Regression surface

The construction retains V1 regression coverage for:

- `PUBLISHED_VERIFIED`;
- `REJECTED_PRE_EFFECT`;
- `EFFECT_VERIFIED`;
- `EFFECT_CONTRADICTED_UNCOMPENSATED`.

New invariant tests cover:

- clean two-invariant compensation -> complete/verified;
- contradicted collateral -> incomplete;
- missing collateral -> incomplete;
- present but independently unverified collateral -> incomplete;
- extra evidence not substituting for missing required evidence;
- all required evidence missing -> incomplete;
- wrong-effect history preserved in incomplete compensation;
- extra evidence retained when all requirements are satisfied.

Fail-closed tests retain sequence/history constraints and add malformed invariant-contract rejection.

## Test receipt

The exact publication candidates were tested twice: once in the construction directory and once after copy into a fresh clean directory.

- `python -m py_compile outcome.py test_outcome.py`: PASS in both locations.
- `python -m unittest -v`: **27/27 PASS** in both locations.
- `outcome.py`: 10,877 bytes; SHA-256 `352e9d202d0cf31ea9146d9f79e0fab7853896ebe6e197b177d84e194d270a63`; Git blob `b519360f3e8d607f13508857e0080ebc564a45dd`.
- `test_outcome.py`: 10,702 bytes; SHA-256 `ff2677838b293e4ab0c9b137cb0840b959c1e01e83281f24db9bc7c5d3f47d43`; Git blob `658623c95525ec4809b2ef7500f68c11010b8631`.

GitHub readback matches both local Git object identities exactly.

## Scope and limits

This remains an additive research construction, not a shared-runtime promotion or production ABI. The required invariant set is caller-authored. If a real dependency is omitted, V2 cannot discover it. This construction does not establish arbitrary compensation safety, GUI undo, external-service semantics, distributed transaction correctness, concurrency, power-loss behavior, performance, or natural failure rates.

The next integration gate should bind required invariant requirements to an actual caller/effect receipt source and demonstrate that requirements are derived from the task/effect contract rather than silently invented after the outcome is known.
