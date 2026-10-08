# #7164 field-level invalidation T0 A01

## Scope and hypothesis

This finite test compares whole-record invalidation and reacquisition, direct-field-only refresh, and dependency-aware selective invalidation against a fresh derivation from the same current visible inputs. It tests only the authored support graph and update semantics. It does not test GUI observation completeness, object re-identification, model behavior, runtime safety, or memory utility.

H: with a complete declared support graph, dependency-aware invalidation should match fresh derivation while retaining unaffected current fields and recomputing fewer derived fields than whole-record invalidation. Direct-field-only refresh is a negative comparator expected to retain stale derived values after relevant source changes.

## Frozen design

Six deterministic cases cover parent/surface replacement, transitive layout derivation with an unaffected sibling, mode-dependent dependency switching, an out-of-order older update, object-ID reuse across generations with a partial new snapshot, and missing source/support coverage. The candidate receives only INPUT.json and SCHEMA.json; oracle semantics exist only in audit.py.

For each case, compare three policies: whole_record, independent_field, and dependency_aware. The candidate sees only the finite fixture and dependency schema; the separate audit program implements the fresh-input oracle independently. Current values without current source support must be UNKNOWN. A generation change replaces the old record. Events older than the current epoch or for a stale generation must not update the active record. The enabled field has a mode-dependent read set; a mode switch invalidates and recomputes it using the newly active branch.

## Decision gates

PASS_METHOD_SCOPED requires the independent auditor to reconstruct all dependency-aware and whole-record outcomes from the current input snapshots; no unsupported or stale value may be CURRENT; incomplete dependency/source coverage must produce UNKNOWN; stale epoch/generation events must be refused; the mode switch must use the new branch; direct-field-only must expose at least one planted stale-derived counterexample; and every frozen audit mutation must be rejected.

The comparative hypothesis is supported only if dependency-aware output agrees with the oracle in all six cases, preserves every unaffected supported field, and performs strictly fewer derived recomputations than whole-record invalidation on at least one fully supported case. Counts are deterministic method work, not latency or product cost.

Any failure in the frozen auditor/result-integrity contract is FAIL_METHOD. If the graph or source boundary is incomplete, the relevant fields must be UNKNOWN; no live inference or authority follows. No participants, user data, GUI, model, external effect, network, or runtime change is included.

## Reproduction and stop rule

Freeze source, schema, inputs, construction tests, and container image identity before formal execution. Run the candidate exactly once and the separately implemented auditor exactly once. No candidate/auditor retry, tuning, replacement, or pooling is allowed. Preserve the first outputs and cleanup receipt. A construction repair requires a separate additive version and is not a formal rerun.
