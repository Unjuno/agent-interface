# Typed quantity-effect contract — T0

Status before formal use: PRE-REGISTERED, candidate=0, auditor=0, retries=0.

This is the first bounded CPU-only method rung for [Issue #6524](https://github.com/Unjuno/agent-interface/issues/6524). It uses a deterministic synthetic app-state fixture, not a real GUI. The question is whether unit/dimension/kind/persistence/tolerance-aware adjudication separates cases that a bare numeric comparison misses.

## H / T / D / C / U

**H.** A typed effect oracle accepts a persisted equivalent m/cm quantity, while rejecting a same-number/wrong-unit, wrong-dimension, wrong-quantity-kind, switched-selector, out-of-tolerance, no-effect, and duplicate-effect case. Undeclared unit conversion or rounding must remain UNKNOWN. A frozen numeric-only baseline intentionally ignores units and effect identity.

**T.** Eleven fixed-order model-free synthetic app traces compare the exact bare-number baseline with a typed quantity-effect checker. The fixture holds locale/parser/keyboard/task/target fixed. It includes an equivalent conversion, same-number wrong unit, incompatible dimension, same-dimension wrong kind, unit-selector switch after entry, within- and outside-tolerance rounding, unchanged pre-existing state with no save, unknown unit, unknown rounding, and duplicate effect. One candidate process emits raw JSON; if it exits successfully with one valid JSON line, one independently implemented raw-only auditor process recomputes every row. No randomness or seed is used. The original allocation can start only after source/image/output/inventory preflight; candidate and audit retries are zero.

**D.** `METHOD_PASS` requires exact independent row reconstruction, all equivalent in-tolerance values accepted, all injected wrong values/dimension/kind/effect-count and no-effect rows rejected, unknown conversions/rounding classified UNKNOWN, and every copied-output mutation rejected. `H_PASS_SCOPED` additionally requires at least one frozen bare-number false positive that the typed oracle rejects, with no typed false PASS. Any mismatch is FAIL or STOP as appropriate. These are synthetic finite-fixture outcomes only.

**C.** A task-specific exact persisted-state comparison may suffice for the tested fixture; typed normalization may add complexity without runtime benefit. Application rounding or state semantics can differ from this synthetic contract.

**U.** This cannot generalize to a real GUI, application, locale, currency, dosage, calendar or arbitrary unit. It grants no action authority and proves no production correctness, safety, reliability or user benefit.

## Frozen inputs and execution

Exact source/input/image identities and start gates are in [FREEZE.json](FREEZE.json). The host and WSLc construction checks are recorded in [CONSTRUCTION.md](CONSTRUCTION.md); neither is the formal result. Formal raw files go only into `results/allocation-01/`, which must be absent/empty before the sole run.
