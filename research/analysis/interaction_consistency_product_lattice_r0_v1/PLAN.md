# Interaction consistency product lattice R0 — plan

Parent: GitHub Issue #1717. Successor Issue: #1727.
Task: `INTERACTION-CONSISTENCY-PRODUCT-LATTICE-R0-20260919-001`.
Base: `ca9b9be2fda8d5e10dd092bc7e952bbb5671d1f7`.
Additive publication path: `research/analysis/interaction_consistency_product_lattice_r0_v1/**`.

## Question

Can the illustrative concurrency modes in #1717 be a scalar ladder, or are the safety conditions orthogonal and therefore better represented as a product contract?

## H

`SURFACE_ISOLATED` and `READSET_VALIDATED` are incomparable raw admission sets. Each constrains a different hazard and each admits unsafe states when orthogonal hazards are present. A product contract over dependency completeness/currentness, hidden-global conflict status, effect commutativity, actuator independence, and schedule phase matches the frozen safety oracle exactly.

## Frozen state variables

All are booleans. Exhaustive state count is `2^7 = 128`.

| field | meaning |
|---|---|
| `surface_disjoint` | logical surfaces differ; heuristic only, never sufficient authority |
| `readset_complete` | all task-relevant dependencies are represented |
| `readset_current` | represented dependencies are unchanged at commit |
| `global_conflict_free` | no hidden shared/global resource conflict |
| `effects_commute` | overlapping effect/verification tails preserve outcomes |
| `actuator_independent` | simultaneous task input has independent physical/routing resources |
| `simultaneous_input_requested` | schedule asks input bursts to overlap, not only no-input tails |

## Frozen oracle

Let `base_ok = readset_complete and readset_current and global_conflict_free and effects_commute`.

- if `not base_ok`: `SERIAL`;
- else if `simultaneous_input_requested and actuator_independent`: `FULL_PARALLEL`;
- else if `simultaneous_input_requested and not actuator_independent`: `SERIAL`;
- else: `PHASE_OVERLAP`.

The oracle deliberately does not use `surface_disjoint`: retained evidence shows surface identity alone cannot establish dependency completeness, hidden-global independence, or physical actuator independence.

## Policies

1. `SAFE_SERIAL`: always serial.
2. `SURFACE_ONLY`: use only `surface_disjoint` to grant requested concurrency.
3. `READSET_ONLY`: use only `readset_complete && readset_current`.
4. `ACTUATOR_ONLY`: use only actuator independence for simultaneous input and otherwise grant phase overlap.
5. `STRICT_FULL_ONLY`: grant full parallel only when all base gates pass, actuator is independent, and simultaneous input is requested; otherwise serial.
6. `PRODUCT`: frozen oracle/product contract.

A decision is unsafe if it grants more concurrency than the oracle. Ordering: `SERIAL < PHASE_OVERLAP < FULL_PARALLEL`.

## T

- analytical set-inclusion witness for surface-only vs readset-only raw admission;
- one formal exhaustive invocation over all 128 states;
- independent audit re-derives the oracle without importing candidate policy functions;
- corruption controls mutate one product row, one oracle row, and one summary count and require all to fail audit;
- formal invocations: 1; reruns: 0; tuning after source freeze: 0.

## D

PASS only if:
- product/oracle mismatch = 0/128;
- surface and readset raw admission sets are mutually non-subsets with explicit witnesses;
- each single-dimension concurrency policy has unsafe admissions > 0;
- serial unsafe admissions = 0 and serial false-serializations > 0;
- product preserves at least one shared-actuator `PHASE_OVERLAP` state;
- product preserves at least one independent-actuator `FULL_PARALLEL` state;
- independent audit and all three corruption controls pass.

## C

A scalar UI label can still exist if it expands to the full structured predicate. In that case the scalar order itself has no safety semantics. Real backends can add further dimensions such as deadlines, authority scopes, and device-routing generations.

## U

Finite synthetic semantics only. No natural hazard frequencies, latency gain, scheduler overhead, automatic dependency discovery, GUI transfer, or production ABI claim.
