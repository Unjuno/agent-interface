# Phase-overlap resource-footprint serializability A2

Issue #1730. Fresh successor to #1720. Scientific hypothesis and exact frozen sources are unchanged; only execution materialization was repaired.

## Source identity

Before execution, exact Git blob identities were recomputed locally using the Git blob framing `blob <size>\0<bytes>`:
- formal.py = `d1f1e1200ce3077fa206a2a0ad022dbe3f9dfd48`
- audit.py = `bd9a2339ee9e72fbec54d5f924bd90e69dc4749f`
- corruption.py = `4446ba4ebf6c82e78443491b2bdfd87472152c7f`

All 3/3 matched #1720 FREEZE.json before the sole formal invocation.

## Formal first outcome

Disposition: `PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED`.

- exhaustive cases: 186,624
- complete-footprint overlap admissions: 51,936
- complete-footprint mismatches: 0
- declared conflicts serialized: 134,688 / 134,688
- UNKNOWN parallel admissions: 0
- surface-only mismatches: 52,800
- omitted-dependency mismatches: 24,576
- reversed-conflict-policy mismatches: 52,800
- both serial orders exercised: 2

Independent retained audit PASS; all ten checks true.
Corruption controls 4/4 rejected.

## Interpretation

Within this deterministic finite model, complete declared read/write footprints plus ordinary RW/WW conflict exclusion are sufficient for the scoped phase-overlap serializability contract, and UNKNOWN must fail closed to serialization.

The negative controls are non-vacuous: surface identity alone, an omitted real dependency, and a reversed conflict predicate all admit observable mismatches.

This is not evidence that real applications expose complete static footprints. It establishes the contract conditional on complete declared footprints and deterministic operations. Hidden/global/data-dependent resources remain the next applicability boundary.

Formal invocation1; reruns/replacements/tuning0. #1720 remains failed and unchanged.
