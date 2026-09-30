# Issue #5385 T0 — bounded active lifecycle learning

Status: preregistration/source frozen; no experiment run yet.
Intake main: bbeee4da02285281e960334f8babefc2d7070358.
Branch: research/active-lifecycle-learning-5385-t0-20260930-v2.
Scope: deterministic finite oracle only; no Docker/OrbStack (current #5085 hold bars CLI inspection and invocation), network, model, GPU, GUI, input, or external effect.

## H/T/D/C/U

- H: A membership-query learner with counterexample refinement will recover all four safety-relevant lifecycle states (fresh-valid, stale, half-open, compensation-pending) in a small deterministic oracle, and expose a trace accepted by a deliberately coarse hand-authored policy although baseline examples miss it.
- T: Run the frozen standard-library-only L*-style observation-table learner once against a six-state complete DFA (four lifecycle states plus safe-terminal and reject sink). The finite equivalence teacher performs BFS over the complete target/hypothesis product, returns the shortest counterexample, and stops uncertain above 64 product pairs; cap refinement at 32 rounds. Separately run four frozen hand-authored traces against a mutant that incorrectly allows compensation to begin from stale. Then run a separate raw-only auditor which reimplements target transitions and checks equivalence, state distinguishability, baseline blind spot, provenance, and four corruption controls.
- D: PASS_BOUNDED_DISCOVERY_ONLY if the learner terminates within bounds, its six-state hypothesis is equivalent to the target under the finite product teacher, four lifecycle access prefixes map to four distinct learned states, the baseline misses the mutant's shortest false admission, the learner has zero false accepts/rejects, and the independent auditor passes and rejects 4/4 mutations. FAIL on a missed hidden distinction or false admission; UNCERTAIN on a bound, provenance, or audit failure.
- C: Explicit schema tests may cover these distinctions more cheaply; the hand-authored baseline is intentionally small and is not representative of repository-wide coverage.
- U: This is a closed, deterministic, hand-authored DFA. Equivalence is exact only for this oracle and its finite product; it says nothing about nondeterministic/noisy observations, instrumentation cost, real lifecycle discovery, authority safety, or distribution shift.

## Frozen artifacts and execution

- learner.py: candidate target fixture, observation-table learner, and finite product equivalence teacher.
- audit.py: separate raw-only verifier with independently restated transition rules; imports no candidate code.
- One local CPython 3.11+ host run because no #5085 container lease exists. This is a documented environment deviation from the preferred container lane, not a resource lease. Run exact GitHub-readback source with bytecode writing disabled (-B); raw JSON goes to stdout only. No local files, Docker CLI, GPU, model, CUDA, retries, or tuning.
- Record source SHA-256 values before the sole run. Any source change after execution invalidates this allocation; no silent rerun.

## Roadmap

Read current main/Issue and collision-check -> freeze sources and hashes -> in-memory syntax/construction gate -> one host-only candidate invocation -> separate independent raw audit + mutations -> retain result/hash and Issue disposition -> additive PR and repository CI -> review/merge only if exact-head checks pass. This bounded T0 is not a product/runtime gate.
