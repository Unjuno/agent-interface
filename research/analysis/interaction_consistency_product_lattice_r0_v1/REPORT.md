# Interaction consistency product lattice R0 — retained result

Issue: #1727 (successor to #1717)
Task: `INTERACTION-CONSISTENCY-PRODUCT-LATTICE-R0-20260919-001`
Publication branch: `research/interaction-consistency-product-1727`
Frozen base: `ca9b9be2fda8d5e10dd092bc7e952bbb5671d1f7`
Frozen source commit: `2ac659e473f624d0a01d29b9db07eb808164855b`

## Decision

`PASS_CONSISTENCY_PRODUCT_NOT_SCALAR_SCOPED`

This is a finite analytical/synthetic result. It does **not** establish real-backend safety, latency improvement, natural hazard rates, automatic read-set completeness, or a production ABI.

## Exact claim

The illustrative #1717 labels cannot obtain their safety semantics from one monotone scalar ordering such as “serial < surface isolated < readset validated < full concurrent.” Surface separation and read-set validity constrain different hazards, and neither raw admission set contains the other. Safe admission therefore needs structured evidence dimensions; a scalar label may remain only as shorthand for such a structured predicate.

The retained product contract uses these orthogonal dimensions:

- dependency completeness;
- dependency currentness;
- hidden/global conflict freedom;
- effect/verification-tail commutativity;
- physical/routing actuator independence;
- whether the schedule asks task-input bursts themselves to overlap.

`surface_disjoint` is retained as a heuristic observation, not sufficient authority.

## Analytical proof of incomparability

Let `S` be the raw states admitted by the surface-only predicate. By definition, a state belongs to `S` exactly when `surface_disjoint=true`.

Let `R` be the raw states admitted by the readset-only predicate. By definition, a state belongs to `R` exactly when both `readset_complete=true` and `readset_current=true`.

The frozen state space treats these Boolean dimensions independently.

1. Choose any state with `surface_disjoint=true` and at least one of `readset_complete`, `readset_current` false. Then the state is in `S` and not in `R`. Therefore `S` is not a subset of `R`.
2. Choose any state with `surface_disjoint=false`, `readset_complete=true`, and `readset_current=true`. Then the state is in `R` and not in `S`. Therefore `R` is not a subset of `S`.
3. Hence `S` and `R` are incomparable under set inclusion. A scalar order that treats one as a strictly stronger safety mode than the other is not justified by these predicates.

The exhaustive formal found 48 states in `S \\ R` and 16 states in `R \\ S`, with explicit retained witnesses in `RESULT.json`.

## Formal execution

Source-first freeze occurred before the only exhaustive invocation. Git blob readback on the branch matched the local `git hash-object` for all five frozen source/freeze files.

- formal invocations: 1
- reruns: 0
- post-freeze tuning: 0
- Python: 3.13.5
- host kernel: Linux 6.18.44 x86_64
- enumerated states: 128/128
- product/oracle mismatch: 0
- shared-actuator `PHASE_OVERLAP` oracle states: 2
- independent-actuator `FULL_PARALLEL` oracle states: 2

### Comparator outcomes

| policy | unsafe admissions | false serializations | missed full-parallel |
|---|---:|---:|---:|
| `SAFE_SERIAL` | 0 | 6 | 2 |
| `SURFACE_ONLY` | 61 | 3 | 1 |
| `READSET_ONLY` | 26 | 0 | 0 |
| `ACTUATOR_ONLY` | 90 | 0 | 0 |
| `STRICT_FULL_ONLY` | 0 | 4 | 0 |
| `PRODUCT` | 0 | 0 | 0 |

Interpretation: one-dimensional permissive policies are unsafe in this model; the always-serial and strict-full-only controls are safe but unnecessarily serialize valid phase-overlap states. The product contract preserves phase overlap behind a shared actuator when task-input bursts remain serialized, matching the scope of retained #1670 rather than claiming simultaneous physical input.

## Independent audit

The auditor re-derived the oracle without importing candidate policy functions.

- audit errors: 0
- product-row corruption detected: yes
- oracle-row corruption detected: yes
- summary-count corruption detected: yes
- audit decision: PASS

Important limitation: `product_contract()` intentionally implements the frozen oracle contract directly. Therefore the zero product/oracle mismatch validates the retained contract/table construction, not an independently engineered runtime implementation. The nontrivial discriminators are the incomparability proof, unsafe counts of the reduced policies, and the independent audit's re-derivation.

## Integrity

Frozen local SHA-256 values are in `FREEZE.json`.

Formal output SHA-256:

- uncompressed `ROWS.json`: `16d68981da1975948c9b9fad2a0e63730374cb0608c1c85df635692a1a43f994`
- canonical semantic rows digest recorded by formal: `2be665d63ad6607e450e013a36e2224c0f27b672060614d05418224207cec8a3`
- `ROWS.json.gz` (deterministic gzip `-n`): `8a678be86303f1fe42ee2b80664de4fd4c55182f8019dddc3fe004b3e4812c65`
- `RESULT.json`: `a995cd40527b7f624032025b795f3e80bacdb5a3350b1401484525a14ce48df3`
- `AUDIT.json`: `5f9c8e567ea1d9802f9744c770ee94355cb7e66126cac9827a68f84f80f465de`

The raw pretty-printed `ROWS.json` was 65,015 bytes. A deterministic `ROWS.json.gz` was prepared locally, but the GitHub connector rejected that opaque binary blob during publication. It is therefore **not** claimed as a retained repository artifact. Reconstruct the exact raw rows with `python3 formal.py --out formal_out` from the frozen source; the reconstructed `ROWS.json` must match the uncompressed SHA-256 above. The rejected publication attempt did not rerun the formal.

## Relationship to prior evidence

- #1670/#1703: a shared input actuator does not force whole-intent serialization; no-input tails may overlap later serialized input.
- #1643/#1649: multiple logical cursors do not imply physical actuator parallelism when resources alias.
- #1678/#1683: independently stale-able lifetime dimensions should not be collapsed into one global epoch.
- #315/#319, #322/#323, #501/#506: observed read sets improve precision only inside their instrumentation/completeness boundary.

The present result composes those distinctions at the admission-contract level; it does not rerun or relabel their evidence.

## Design consequence for #1717

Do not give a scalar enum value independent safety meaning. Prefer a machine-readable structured contract with a fail-closed serial fallback. A UI can still present named presets, but each preset must expand to explicit evidence/resource predicates and schedule-phase constraints.

## H/T/D/C/U result

**H — PASS within frozen model.** Surface-only and readset-only are incomparable; structured product admission can exactly represent the frozen oracle while retaining shared-actuator phase overlap.

**T — completed.** One source-frozen 128-state exhaustive formal plus independent audit and three corruption controls.

**D — PASS.** All preregistered gates passed; product mismatch0; mutual non-subsets witnessed; all three single-dimension permissive policies exposed unsafe admissions; serial control unsafe0/false-serial>0; both phase-overlap and full-parallel positive controls exist; audit/corruption controls pass.

**C — retained.** A scalar name is harmless if it is only shorthand for the full structured contract; additional backend dimensions may be required.

**U — material.** Synthetic Boolean semantics, authored completeness/currentness, no empirical concurrency rates or latency, no GUI/backend transfer, no production implementation.

## ERROR CHECK

- no previous Issue/result modified or relabeled;
- no shared runtime/workflow/history path changed;
- source files frozen and remotely read back before formal;
- formal invocation count remained 1;
- result is scoped to the finite model and does not claim live transfer.
