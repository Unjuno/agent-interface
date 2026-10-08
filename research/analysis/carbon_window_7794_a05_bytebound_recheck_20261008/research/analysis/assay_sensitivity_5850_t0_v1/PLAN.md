# Issue #5850 — assay-sensitivity T0

Allocation: `5850-ASSAY-SENSITIVITY-T0-20261001-01`  
Scope: deterministic synthetic method experiment; no model, GUI, or live route data.

## H / T / D / C / U

- **H:** A claim-specific sensitivity card distinguishes an interpretable null from an unresolved comparison, including missing outcomes, absent target events, broken shared measurement paths, inadequate precision at the meaningful delta, and a gross-but-unrepresentative control.
- **T:** Freeze eight authored cases at meaningful delta 10. One candidate classifies each case; an independently written raw-fixture oracle reconstructs each outcome and applies eight adversarial mutations.
- **D:** `PASS_METHOD_SCOPED` only for exact expected dispositions and rejection of all eight mutations. A sensitivity PASS only qualifies the synthetic measurement design; it never establishes candidate benefit, equivalence, or production validity.
- **C:** Inputs and truth labels are deterministic and authored; the oracle shares the declared fixture schema and decision contract, though not candidate code.
- **U:** No model variance, real endpoint noise, task-population coverage, provider usage, human tempo, causal estimate, or validation of any live #57 arm is represented.

## Frozen decision semantics

Missing outcomes, no target events, or a defect on the common measurement path => HOLD. A defect isolated to an outcome channel is explicitly `OUT_OF_SCOPE_UNDETECTED`, never sensitivity PASS. A known control below the minimal meaningful delta or resolution coarser than that delta cannot qualify the contrast. A qualified synthetic control with zero observed effect is `NULL_INTERPRETABLE_NOT_EQUIVALENCE`.

## Execution boundary

Construction checks run locally. Formal candidate and auditor are intended for one isolated, network-disabled, pinned Python container each. No retries, data tuning, or live allocation is included. If container execution is unavailable, preserve STOP and do not relabel local construction as formal.
