# Issue #5385 T0 — bounded active lifecycle learning

Status: preregistration/frozen source; host-only run pending.
Intake main: 0cf275c05cc4870d17936bfcff0e8b98539c7cf2.
Branch: research/active-lifecycle-learning-5385-t0-20260930.
Scope: deterministic finite oracle only; no Docker/OrbStack (the current #5085 hold bars CLI inspection and invocation), no network, model, GPU, GUI, input, or external effect.

## H/T/D/C/U

- H: A membership-query learner with counterexample refinement will recover all four safety-relevant lifecycle states (fresh-valid, stale, half-open, compensation-pending) in a small deterministic oracle, and expose a trace accepted by a deliberately coarse hand-authored policy although the baseline examples miss it.
- T: Run the frozen standard-library-only L*-style observation-table learner once against a six-state complete DFA (four lifecycle states plus safe-terminal and reject sink). The exact finite equivalence teacher performs breadth-first search over the target/hypothesis product and returns the shortest counterexample; cap at 16 symbols and 32 refinement rounds. Separately run the four frozen hand-authored traces against a mutant that incorrectly allows compensation to begin from stale. Then run a separate raw-only auditor which reimplements the target transitions and checks exact product equivalence, state distinguishability, baseline blind spot, provenance, and four corruption controls.
- D: PASS_BOUNDED_DISCOVERY_ONLY if the learner terminates within bounds, its six-state hypothesis is exactly equivalent to the target under the finite product teacher, the four lifecycle access prefixes map to four distinct learned states, the baseline misses the mutant's shortest false admission, the learner has zero false accepts/rejects, and the independent auditor passes all checks and rejects 4/4 mutations. FAIL on a missed hidden distinction or false admission; UNCERTAIN on bound, provenance, or audit failure.
- C: The explicit schema/test oracle may already cover these distinctions more cheaply; the hand-authored baseline is intentionally small and not representative of repository-wide coverage.
- U: This is a closed, deterministic, hand-authored DFA. The teacher's equivalence query is exact only for this oracle and its finite product; it says nothing about nondeterministic/noisy observations, instrumentation cost, real lifecycle discovery, authority safety, or distribution shift.

## Frozen artifacts and execution

- learner.py: candidate, including target fixture, observation-table learner, and exact bounded equivalence teacher.
- audit.py: separate raw-only verifier with independently repeated literal transition rules; imports no candidate code.
- One local CPython 3.11+ host run because no #5085 container lease exists. This is a documented environment deviation from the preferred container lane, not a resource lease. Run each source from the exact GitHub readback, with bytecode writing disabled (-B); raw JSON is stdout only. No local files, Docker CLI, GPU, model, CUDA, retries, or tuning.
- Freeze SHA-256 values are recorded in the result report before execution; source changes after freeze invalidate this allocation and are not to be silently rerun.

## Roadmap

Read current main/Issue and collision-check -> freeze sources and hashes -> construction tests -> one host-only candidate execution -> separate independent raw audit + mutations -> retain result/hash and Issue disposition -> additive PR and repository CI -> review/merge only if exact-head checks pass. The formal experiment is one bounded T0; it is not a product/runtime gate.
