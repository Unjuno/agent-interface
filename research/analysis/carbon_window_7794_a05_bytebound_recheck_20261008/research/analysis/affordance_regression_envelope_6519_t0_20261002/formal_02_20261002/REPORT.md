# Issue #6519 T0b — scoped method result

Allocation: `AFFORDANCE-REGRESSION-6519-T0B-20261002-01`\
Branch: `research/6519-affordance-regression-t0-wslc-20261002`\
Frozen preregistration head: `e10f276a684eb1531127df9f4d95a53ac4856320`\
Latest main merged before T0b freeze: `211f74a8f242294eb60240b84d89fd48180709f6`\
Formal runtime: native Microsoft WSL Containers (`wslc.exe`), reported version `5.0.1.1`; pinned cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

## Result

**`METHOD_PASS_SCOPED`.** The single WSLc construction invocation exited 0 and passed all 12 protocol tests. The single candidate invocation exited 0 and emitted exactly 72 rows (eight synthetic cases × nine arms). The single independent auditor invocation exited 0 and reported `METHOD_PASS_SCOPED`, 72/72 rows, zero audit errors, and one independently caught witness for each of the five planted corruption classes: dropped source binding, flipped effect label, suppressed UNKNOWN, card-as-authority, and hidden raw evidence. Candidate raw and the auditor's read-only input copy have identical SHA-256 `0d9bc8a17e0e123c01ac1100d2ba1ff758a40867697e8be93e8be37e23da4664`.

The auditor recorded nine unverified effect/oracle disagreements in total (one each for `CANDIDATE_EFFECT`, `UNCERTAINTY_CONTRADICTION`, `DROP_SOURCE_BINDING`, `SUPPRESS_UNKNOWN`, `CARD_AS_AUTHORITY`, and `HIDE_RAW_EVIDENCE`; three for `FLIP_EFFECT_LABEL`). These remain `UNVERIFIED`, not promoted application effects. Every candidate row preserved `authority=false`, `completion=NONE`, and `effect_claim_status=UNVERIFIED`; the independent audit found no canonical invariant error.

## Runtime and preserved execution record

Each formal stage ran once, in its own native WSLc container with `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`; source and oracle mounts were read-only, and no GPU, Podman, or Docker CLI was used. The WSL kernel emitted: `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The configured memory cap is therefore **not** claimed as enforced. Container IDs and stage exit/time/command records are in the per-stage `RUN.json` files and parent `RUN.json`; raw stdout/stderr and exit receipts are retained next to them. `SHA256SUMS` covers retained execution artifacts.

The parent allocation `AFFORDANCE-REGRESSION-6519-T0-20261002-01` remains separately and immutably `STOP_LAUNCH_PATH_UNRESOLVED`: its relative path failed before tests; it ran no candidate or auditor and was not retried. T0b is the separately preregistered fresh allocation with a corrected absolute-path runner, new output directories, unchanged scientific sources and frozen method.

## Scope boundary

This is a finite synthetic **method-contract** result only: the source-bound optional-annotation protocol, UNKNOWN/raw-evidence preservation, non-authority and non-completion constraints, and planted mutation detection passed this fixture. It does not test a language model, live GUI, real application, task outcome, user benefit, annotation truth, planner behavior, production runtime safety, or a gradual-typing theorem. It neither resolves Issue #6519's behavioral H nor authorizes a model/GUI T1. See `PREREGISTRATION.md` and `RUN.json` for the frozen question, denominators, runtime, and complete receipts.
