# Preregistration — Issue #6586 T0

Allocation: `PATH-CLASS-SWITCH-6586-T0-SUCCESSOR-20261002-02`  
Intake main: `dd141de60516f0c164cd8be310981839fea9e53a`  
Branch: `research/path-class-switch-6586-t0-20261002`  
Additive path: `research/analysis/path_class_switch_6586_t0_20261002/`

This is a separately frozen successor to the exploratory predecessor retained by open draft PR [#6596](https://github.com/Unjuno/agent-interface/pull/6596). That predecessor used abstract route tokens, ran on macOS outside a container, omitted the live Issue's planar-embedding and ambiguous-prefix controls, and its independent audit failed terminal-action replay. Its raw output and failure remain unchanged. This successor uses a frozen planar embedding and source-visible cues, adds all corrected controls, and has its own allocation ID and one-shot records; it does not repair or replace #6596.

The hypothesis, six case identities, route geometries, source-visible barriers, policy order, cost table, one-shot counts, output schema and gates are frozen by `FREEZE.json`, `inputs.json`, `oracle.json`, `candidate.py` and `audit.py`. The path-class definition is a planar embedded-path diagnostic: a valid complete path is UPPER or LOWER according to its x=0 crossing relative to the frozen central obstacle. A partial prefix carries only the set of classes compatible with that exact source-visible prefix and candidate completions; it must not be forced to a unique class when the set has cardinality two.

The positive selector may switch only at the declared visible branch when (1) the current map version equals the observation version, (2) the prior-attempt prefix supports exactly one class, (3) the visible blockage cue intersects the claimed route, (4) every visible candidate in that same class intersects the common gate, and (5) an unblocked distinct-class route is present. Otherwise it emits a typed non-action decision.

Three policies receive identical case input and the same event budget: novelty-only route ordering, route-level backtrack with one extra return event after each blocked attempt, and class-aware grouping. Attempt cost is a fixed authored unit from `route_costs`; it is not elapsed time or path length. No tuning after candidate output, retries, seed replacement, model/GUI allocation, or privileged map input is permitted.

Formal invocation budget: construction 1× on frozen source; candidate 1×; independent auditor 1× only if candidate exits 0; retries 0. Each formal stage uses cached digest-pinned Python 3.12.14, WSLc `--pull never --network none`, 0.25 CPU requested, 512 MiB requested, non-root UID 65534, read-only source/input, and distinct writable output mounts. The WSLc cgroup/swap warning must be retained; memory enforcement is not claimed.

The live state at freeze and before launch must be checked against this exact main SHA, the complete source/input hash list, unique empty output directories, current Issue/PR/branch overlap, WSLc cache identity, and resource-owner instructions. Any changed prerequisite stops before candidate. The independent auditor may not import candidate functions or read candidate-only process state. Its decisions are recomputed from immutable input, oracle and raw JSON.
