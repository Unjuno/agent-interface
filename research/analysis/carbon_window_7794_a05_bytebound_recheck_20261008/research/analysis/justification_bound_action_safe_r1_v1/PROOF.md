# Justification-bound ACTION_SAFE R1 - proof

## Variable table

| symbol | meaning | SI unit | definition | domain / assumptions | type |
|---|---|---:|---|---|---|
| `B` | base/support identity set | 1 (dimensionless) | `{B0,B1,B2}` in the finite confirmation | finite nonempty set | finite set |
| `F` | declared justification family | 1 | nonempty set of nonempty support subsets | positive OR-of-AND; here singleton/pair subsets | family of finite sets |
| `j` | one justification | 1 | `j in F`; satisfied iff all its supports are true | nonempty support set | finite set |
| `c(b)` | support truth at COMMIT | 1 | Boolean validation-time truth | `{0,1}` | Boolean scalar |
| `R` | recorded commit justifications | 1 | `{j in F : forallbinj, c(b)=1}` | nonempty because commit claim is true | finite family |
| `nu_c(b)` | committed semantic version identity | 1 | exact support-version recorded at COMMIT | equality-comparable opaque identity | discrete scalar / token |
| `nu_a(b)` | action-time semantic version identity | 1 | current support-version at action boundary | equality-comparable opaque identity | discrete scalar / token |
| `x(b)` | action-time support truth | 1 | current truth at action boundary | `{0,1}` | Boolean scalar |
| `P(b)` | preserved support predicate | 1 | `x(b)=1 AND nu_a(b)=nu_c(b)` | Boolean | Boolean scalar |
| `A` | candidate ACTION_SAFE predicate | 1 | true iff one recorded justification has all supports preserved | Boolean | Boolean scalar |

All quantities are logical identities, sets or counts and are dimensionless.

## Definitions

A positive OR-of-AND claim is true at COMMIT exactly when at least one declared justification is fully true. Because a commit is only studied when the claim is validated true, the recorded family `R` is nonempty.

A support is a valid action-time continuation of its committed premise only when both conditions hold: its current truth is true and its semantic version identity is exactly the one validated at COMMIT. Define this as the preserved-support predicate `P(b)` from the variable table.

The candidate admits an action exactly when there exists a commit-recorded justification whose every support is preserved:

`A = TRUE` iff there exists `j in R` such that `P(b)=TRUE` for every `b in j`.

This is the only ACTION_SAFE rule proved here.

## Theorem 1 - sufficiency

If the candidate admits, the old commit still has at least one complete current support witness.

### Proof

1. Assume `A=TRUE`.
2. By the candidate definition, there exists some `j in R` for which every `b in j` satisfies `P(b)`.
3. Because `j in R`, every support in `j` was true at COMMIT and the commit receipt recorded the exact semantic version of each such support.
4. Because `P(b)` holds for every support in `j`, each support is currently true and its action-time semantic version equals its committed semantic version.
5. Therefore the exact conjunction that validated `j` at COMMIT still holds through the same support identities/versions at the action boundary.
6. Since the claim is OR over its justifications, one intact recorded conjunction is sufficient for the committed claim premise to remain supported.
7. Thus ACTION_SAFE does not need every other recorded alternative to remain current. QED.

## Theorem 2 - necessity under the frozen contract

If no recorded commit justification remains fully preserved, the old commit cannot by itself justify ACTION_SAFE.

### Proof

1. Assume that for every `j in R`, at least one support `b in j` fails `P(b)`.
2. Therefore every justification that actually supported the commit has lost at least one required current premise: either the support is no longer true, or its semantic version differs from the one validated at COMMIT.
3. A declared justification outside `R` cannot repair this old commit, because it was not satisfied at validation time and hence was not a support witness for that commit.
4. Consequently there is no commit-recorded conjunction whose validated premises all remain current.
5. Under the frozen rule that external action requires a surviving commit witness, ACTION_SAFE must be false.
6. Establishing a different now-true justification requires a fresh validate/commit cycle; it cannot retroactively rewrite the support provenance of the historical commit. QED.

## Corollary 1 - STICKY_COMMITTED is unsafe

`STICKY_COMMITTED` admits every action after a commit. By Theorem 2, any state in which every recorded justification is broken requires ACTION_SAFE=false. Such a state exists: commit on `{B0}`, then change `B0`'s semantic version while keeping it true or making it false. Sticky admission therefore produces unsupported actions. QED.

## Corollary 2 - CURRENT_TRUTH_ONLY launders newly true alternatives

Consider declared family `{ {B0}, {B1} }`.

1. At COMMIT let `B0=true`, `B1=false`; therefore only `{B0}` belongs to `R`.
2. At action time change `B0` so it no longer preserves the committed support, and make `B1=true` under a changed/new semantic version.
3. The claim is currently true because `{B1}` is true.
4. But `{B1}` did not support the historical commit, while `{B0}` no longer survives.
5. `CURRENT_TRUTH_ONLY` has no provenance boundary and admits; the justification-bound rule rejects and requires a fresh validate/commit.

Hence current claim truth alone is insufficient to authorize an old commit. QED.

## Corollary 3 - requiring every committed support is over-conservative

Again use family `{ {B0}, {B1} }`, but let both supports be true at COMMIT, so both singleton justifications are recorded.

1. At action time keep `B0` same-version and true.
2. Let `B1` become stale or false.
3. The recorded `{B0}` justification is still fully preserved, so Theorem 1 makes ACTION_SAFE=true.
4. A policy requiring every support appearing anywhere in any recorded justification to remain current rejects because `B1` failed.
5. Therefore that policy false-rejects a valid surviving alternative. QED.

## Corollary 4 - truth without version identity is insufficient

Take a commit supported only by `{B0}` and later keep `B0=true` while changing its semantic version identity. The current Boolean truth is unchanged, but `P(B0)=false` because version identity differs. No recorded justification survives, so ACTION_SAFE=false by Theorem 2. This prevents replacement evidence from being silently treated as the evidence validated by the historical commit. QED.

## Exact finite confirmation size

The frozen confirmation uses six candidate justification sets (three singletons and three pairs), hence 63 nonempty declared families. Across those families there are 327 family/commit-valuation pairs in which at least one justification is satisfied. Each pair is combined with all 64 action-time support-state vectors, giving 20,928 formal rows. These are exact finite counts, not random samples.

## Dimensional / unit check

Every predicate compares Boolean truth or semantic identity and every reported quantity is a finite count. All variables therefore have SI dimension 1. The count 20,928 has unit `cases` as a pure cardinality; no physical units are added, multiplied or compared. There is no dimensional inconsistency.

## Scope boundary

The proof is exact only for positive acyclic/support-version semantics assumed above. It does not prove that a real system's version tokens are trustworthy, that all causal dependencies are declared, or that a semantic effect remains correct in a GUI. Those are separate empirical/runtime obligations.
