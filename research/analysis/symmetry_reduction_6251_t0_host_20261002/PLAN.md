# Issue #6251 — finite typed-symmetry T0 (host fallback)

## Research question and scope

Does a type/authority-preserving permutation quotient for a bounded multi-worker transition system preserve the reachable safety predicates and counterexamples while reducing state classes for genuinely interchangeable verifier replicas? Does it conservatively fall back to named-state enumeration when authority, lease ownership, an actor-named property, or an omitted effect target breaks the declared symmetry?

This is a new, single-shot host-CPU allocation under the existing #6251 question. The Issue's proposed container was infeasible at intake: Docker Desktop service is `Stopped`, `desktop-linux` does not answer, and #5085 has no transfer/assignment for this work. No daemon, image, or existing container will be started or altered. Because the model and oracle are deterministic stdlib-only computation with no external effects, host execution changes reproducibility scope only; it does not stand in for a container/image result.

## H / T / D / C / U

**H.** In the frozen finite model, swapping only the two same-role verifiers is equivariant for transitions and all checked properties, so typed quotienting strictly reduces reachable state classes while retaining the full oracle's safety-counterexample existence. Swapping all actor IDs is unsound because it can identify the named requester with a verifier. Fixed verifier ownership, a fixed lease-holder identity, an actor-named property, and omission of effect target from the canonical key must each refuse reduction or fall back to named states.

**T.** Allocation `PROPERTY-SYMMETRY-REDUCTION-6251-T0-HOST-20261002-01`, based on `97afcb82f90616589801a256893f886010ed6d27`. Enumerate from one initial state over actors `{requester, verifier_a, verifier_b}`. State fields: lease holder, replyer set, observation generation, committer, effect target and receipt target. Transitions: grant/revoke lease, observation becomes stale, reply/duplicate reply, effect commit, and effect receipt. Compare full named-state reachability with the verifier-swap quotient and a naive all-ID quotient. Check transition equivariance, property invariance, reachable violation predicates, and named-trace expansion for every unsafe quotient class. Four frozen controls bind a verifier, bind lease ownership to a verifier, name a verifier in a property, or omit effect target from the quotient key. Candidate and independent tuple-state auditor each run once; retries 0. No model/provider, GUI, live interface, user data, network, GPU, or external action.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs the full state count, typed quotient count, predicate/counterexample existence, transition-equivariance checks, property-invariance checks, all witness traces, and all four control outcomes; the symmetric baseline has strict quotient reduction; no predicate/counterexample is lost; and every mutation refuses the unsafe quotient or returns to named-state enumeration. Any disagreement is retained as `FAIL`/`FAIL_AUDIT`; infrastructure/freeze/raw-integrity problems are `STOP`. Candidate once, auditor once, no retries.

**C.** Finite authored state machine, no system/model/runtime code. Windows host scheduling and Python execution affect timing but timing is not an outcome. The independent checker is separately implemented with integer actor IDs and tuple states; it must not import candidate code.

**U.** This does not validate real worker symmetry, hidden actor-specific state, dynamic membership, fairness/liveness, external effects, runtime authority, partial-order reduction, production safety, or live GUI behavior. It is a finite method result only.

## Freeze / outputs

- Python: CPython 3.12.10, Windows 11 x64; stdlib only.
- Construction command: `python -B -m unittest discover -s research/analysis/symmetry_reduction_6251_t0_host_20261002 -p 'test_*.py' -v`.
- Candidate command (single formal invocation): `python -B research/analysis/symmetry_reduction_6251_t0_host_20261002/candidate.py --output research/analysis/symmetry_reduction_6251_t0_host_20261002/candidate.raw.json`.
- Independent audit command (single invocation): `python -B research/analysis/symmetry_reduction_6251_t0_host_20261002/audit.py research/analysis/symmetry_reduction_6251_t0_host_20261002/candidate.raw.json --output research/analysis/symmetry_reduction_6251_t0_host_20261002/audit.raw.json`.
- The exact output paths must be absent before candidate launch. No test is allowed to overwrite formal outputs.

Exact source hashes are in `FREEZE.json`; the raw outputs will be checksummed in `SHA256SUMS` after their single invocations. This plan and all prior allocations remain unchanged.
