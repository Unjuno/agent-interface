# Running action guard v2

V1 continuously re-evaluates one immediate action contract, but its program
admission records only Executor ID and time. V2 adds an exact binding between the
validated planner action, each semantic program slice, its compiled steps, the
submitted command and the Executor acceptance.

Primary programs must cover the planner command list in contiguous order without
overlap. A fallback must exactly match the authored contingency at the most
recent completed primary boundary. Its branch evidence binds the latest primary
program ID, completed terminal, command index, semantic command and full retained
`no_visible_effect` receipt. A branch label alone is rejected. The submitted step
list must equal the bound compiled list, and the
Executor acceptance must match program ID, step count, send ordering and the
Executor v10 SHA-256 attestation of its validated immutable step snapshot. V2 also
re-runs the supplied deterministic compiler and rejects a submitted/recorded step
list or attestation that does not exactly match compilation of the semantic
commands. The root receipt retains the compiler identity used for this check.

The root receipt is the single current authority view. It retains the first
Executor acceptance under `historical_first_admission`, but consumers use the
root `current_input_authority`, `physical_input_may_be_down` and
`physical_release_verified` fields. Continuous health/ammo/binding/freshness
checks and cancel/release transitions remain delegated to the deterministic v1
guard and are mirrored at the root.

V35 now wires this guard into primary and fallback submissions. A deterministic
five-path replay covers seven exact bindings and closes every path with current
authority false. This remains model-free construction and has not exercised a
planner-authored fallback live. Exact program binding does not prove that a
viewport-effect classifier is semantically correct.
