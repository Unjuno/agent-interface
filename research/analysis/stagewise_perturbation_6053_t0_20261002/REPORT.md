# Issue #6053 T0 — finite stagewise diagnostic

**Disposition: PASS_METHOD_SCOPED for the six authored exact affine fixtures only.** This is not Agent Interface behavior, an empirical perturbation gain, or GUI safety proof.

## Results

Candidate and independent rational enumerator agree on all stage prefixes, branch/safety outcomes, and truth controls:

- Contracting: serial A terminal deviation `0.125` from injected `1` (ratio `0.125`); checkpointed B/C terminal deviation `0`.
- Amplifying: serial A grows injected `0.25` to `2` (ratio `8`); B/C checkpoints return terminal deviation to `0`.
- Late independent injection: first nonzero deviation appears at stage 2, ratio `1`; it is not attributed to upstream amplification.
- Branch boundary: first divergence at stage 0. A remains `INCOMPARABLE_BRANCHES`, ratio `null`; B's later reset cannot erase the earlier branch event or make its task-effect gate pass.
- Zero denominator: common exogenous disturbances affect both trajectories, their difference remains zero, and ratio is `null`/`NOT_COMPUTABLE_ZERO_INJECTION`.
- Forbidden-prefix control: A first crosses the bound at stage 1 and fails the safety/effect gate; B has a checkpoint after stage 0 and remains inside the model bound. The earlier A breach remains in its trace.

Ratios are finite-fixture diagnostics only. Checkpointing changes the modeled trajectory by resetting the paired perturbation; no observation/action/resource cost is represented, so no policy benefit follows.

## Integrity and construction history

- Frozen source base: `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`.
- Candidate and independent auditor each ran once after freeze; both exited 0. Raw outputs and SHA-256 hashes are retained.
- Freeze named the source paths and base commit but omitted pre-run per-file SHA values. The final SHA manifest was captured after execution; source files were not edited after freeze. This provenance gap is explicit in `RUN.json` and is not represented as pre-run hash verification.
- Construction controls pass for omitted/misaligned stage vectors, duplicate checkpoints, zero denominator, and branch-boundary mutation.
- Pre-freeze construction found and corrected two implementation issues: missing default empty checkpoint list for serial A, and float-vs-rational serialization mismatch. These were fixed before the final freeze; no formal output existed then.
- Host CPython only. Docker Engine unavailable; no shared restart and no container-isolation claim. No model/network/GUI/game/GPU/physical-input operation.

## H/T/D/C/U

- **H:** The finite diagnostic differentiates contraction, amplification, late injection, typed branch divergence and zero denominator while retaining all safety prefixes.
- **T:** Six matched nominal/perturbed finite stage cases, common exogenous disturbances, serial/checkpoint variants, candidate plus independently coded exact-rational replay.
- **D:** `PASS_METHOD_SCOPED` for analytic method controls only.
- **C:** Heterogeneous discrete GUI stages may have no scalar metric; checkpoint benefit may be resource spending rather than stability.
- **U:** All dynamics, bounds and oracles are stipulated. No eligible app chain, empirical distribution, resource-matched policy result or live safety is established.
