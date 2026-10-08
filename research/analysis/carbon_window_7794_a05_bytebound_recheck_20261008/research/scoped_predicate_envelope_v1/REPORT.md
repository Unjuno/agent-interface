# Scoped predicate dependency envelope v1

Status: **RETAIN presentation scoping; HOLD compute pruning and live promotion.**

Immutable research base: `12ad78d903256d08743b49020eb8aced4fd45254`.

This block follows Issue #165 / PR #169. It asks one integration question: can an existing compiled GUI method acquire/present only the predicates required by its current state without changing retained behavior? No shared runtime, formal allocation, or historical result is modified.

## 1. Frozen Chromium v5 replay: presentation-only projection

The retained live Chromium v5 interface declares four predicates globally. From the method declaration, outgoing symbol dependencies, and the pending action's expected effect, the minimal runtime-visible sets are:

- `empty`: `field_pixels_changed`, `field_target_present` (2/4)
- `filled`: `field_pixels_changed`, `submit_target_present` (2/4)
- `submitted`: `submission_pixels_changed` (1/4)

The exact retained v5 positive and changed-target observation rows were replayed without changing sequence, evidence reference, or canonical evidence digest. Only the predicate dictionary presented to the compiled runtime was projected.

Result:

- positive: full and scoped both `TASK_SUCCEEDED / method_complete`, two actions;
- changed target: full and scoped both `SAFE_YIELD / unknown_state`, one completed action;
- omission ablation: dropping any one of the five required state/pending-effect predicate occurrences changed the result **5/5**.

Compact JSON predicate payloads fell from 121–126 bytes to 34–59 bytes in these five retained rows. This is serialization evidence only, not a token or wall-time result.

## 2. The reduction is not universal across compiled methods

The same mechanical extractor (state branch conditions ∪ outgoing action symbol dependencies ∪ incoming expected-effect keys) was applied to existing compiled specifications and finite boolean/enumerated states.

- Chromium v5: 4 global -> 2/2/1 by state.
- XTerm live v4: 2 -> 2/2/2; no reduction.
- MAP01 composition: planner-visible 2 -> 2/2/2; no reduction.
- continuous control: 2 -> 2; no reduction.
- desktop cross-domain two-step: 2 -> 2/2/2; no reduction.

All **200** finite state checks passed. Therefore state scoping is spec-dependent; it is not a generic “halve observations” mechanism.

## 3. Interface predicates are not the complete dependency envelope

The existing MAP01 composition has only planner-visible `surface_present` / `phase`, but final action admission separately reads action-validity evidence: health, optional ammo, focus/surface/geometry binding, sequence/freshness and age.

A finite simulation compared four acquisition policies over healthy, damage, no-ammo, binding-change, stale and unknown-health cases:

- full fresh admission dependencies: baseline **6/6**;
- interface-only fail-closed: safe but falsely stops the healthy case;
- interface-only cached semantic values: healthy succeeds but all **5/5** unsafe scenarios incorrectly reach task success;
- action-specific fresh dependency acquisition: baseline **6/6**.

Thus “not planner-visible” does not mean “not required.” Stale cached dependency laundering is unsafe; absence must fail closed unless the dependency is freshly acquired.

## 4. Existing action-validity contracts are projectable

The actual action-validity contract semantics were exhaustively checked over a 1,152-case finite grid.

- retreat/fire requires `health + ammo` signals;
- movement-only strafe requires `health` only;
- binding, sequence and age remain structural snapshot dependencies in both cases.

Projecting the signal dictionary to exactly the contract-referenced signal IDs matched the full-snapshot verdict in **1,152/1,152** cases. Omitting any required signal produced `REJECTED_SIGNAL_UNKNOWN`.

This is stronger than caching: it obtains fewer signals *freshly* because the already-authored contract proves which signals are relevant.

## 5. Verifier dependencies must also be declared or mediated

The compiled runtime passes the whole observation to `verify_effect`. A synthetic finite counterexample gave the action expected effect predicate `a`, while the verifier additionally depended on `b`.

- scoping only to expected-effect keys matched baseline **4/8**;
- including the verifier dependency matched **8/8**.

Current inspected project verifiers mostly use an independent scorer or evidence reference and did not expose an extra normalized-predicate read, but the ABI permits such a dependency. Therefore a generic scope derivation must include verifier dependencies or restrict verifier access.

## 6. Evidence identity is a separate blocker

Frozen Chromium v5 computes:

`evidence_digest = SHA256(image_sha256_hex + json.dumps(all_predicates, sort_keys=True))`.

The five retained v5 hashes were reconstructed exactly **5/5**. Recomputing the same formula after state projection changed the digest **5/5**. For the four observations whose state has at least two required keys, merely choosing two different projections of the same image/full semantic world changed the digest **4/4**.

`compiled_gui_interface_v1` uses digest equality for `no_progress`. Therefore presentation/schema projection must not silently redefine evidence identity. The first scoped experiment must preserve the canonical digest.

A first development assertion mistakenly required two distinct projections in the one-key `submitted` state and failed; the source is retained. The corrected check restricts that assertion to comparable states.

## 7. Performance disposition

A paired post-capture Python/Pillow benchmark was run, but no speed result is promoted:

- empty and filled timings were noisy and did not show a robust paired gain;
- submitted looked substantially cheaper only when field-diff work was removed, but that also removes data currently used by the canonical v5 digest.

Therefore the attractive submitted-state timing is **not** admissible as the first-change optimization result. Presentation scoping can be tested now; computation pruning must wait for a separate canonical-evidence/progress ABI experiment.

## Candidate dependency envelope

For one compiled action boundary, the safe acquisition envelope is at least:

1. branch predicates for current state;
2. selected symbol identity/dependencies;
3. pending expected-effect predicates;
4. action-admission contract dependencies (including non-predicate freshness/binding fields);
5. verifier dependencies if the verifier consumes semantic observation fields;
6. projection-independent canonical evidence identity/provenance.

This extends the typed dependency vocabulary from PR #169 rather than replacing it.

## H / T / D / C / U

**H.** State/action-scoped fresh acquisition can reduce unnecessary semantic presentation without changing behavior when every dependency-producing layer is included and canonical evidence identity is held fixed.

**T.** Retained Chromium replay + five-spec finite extraction (200 cases) + six admission scenarios + 1,152 action-validity finite cases + eight verifier finite cases + five retained digest rows. No model or new live GUI allocation.

**D.** RETAIN presentation-only state scoping for a new Chromium development allocation. HOLD compute pruning, generic runtime promotion and token/speed claims.

**C.** Hidden admission/verifier dependencies can invalidate an interface-only scope. Broad scoping may produce no reduction in already-small interfaces. Canonical evidence digests can couple progress semantics to fields that appear otherwise removable.

**U.** The actual Chromium v5 environment is not available in this container as the frozen Windows/WSL/model stack. Chromium itself is installed locally, but a substitute fixture would be a new environment rather than a reproduction. No formal/live allocation was consumed.

## Next smallest experiment

Create one separately versioned Chromium development runner from the frozen v5 design. Change only `local_observe` presentation: compute exactly the same four predicates and exact same canonical digest, but return only the derived state/pending-effect subset. Keep model grounding, target checks, action admission, execution, scorer and evidence retention otherwise unchanged. Run positive + changed-target once under a new allocation. Only after that passes may a separate experiment prune actual predicate computations.
