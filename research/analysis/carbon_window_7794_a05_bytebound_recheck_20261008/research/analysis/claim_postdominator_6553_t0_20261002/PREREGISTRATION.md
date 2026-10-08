# Issue #6553 T0 preregistration

## H / T / D / C / U

**H.** In a finite branching workflow where one independently specified,
source/generation-bound semantic oracle genuinely covers every claim obligation,
typed freshness-aware placement can preserve exact claim verdicts at lower total
cost than route-local checks. A generic graph-only instrumentation cut can be
cheaper while being semantically unsound. A null case is expected where graph
maintenance cost erases the check savings.

**T.** Freeze seven finite cases in `fixture.json` and the separate evaluator
truth in `oracle.json`. The candidate reads only `fixture.json`; the independent
auditor reads both and recomputes all finite paths from the complete oracle graph.
Enumerate every entry-to-terminal route and every subset of candidate checks.
Compare (1) route-local semantic checks, (2) generic minimum graph cut ignoring
type/freshness, and (3) typed/freshness-aware placement including graph
maintenance cost. The cases are: valid shared oracle plus timeout/YIELD;
bounded one-repeat loop with no net cost gain; wrong target; stale generation;
hidden effect; candidate graph explicitly not closed with an oracle-only bypass;
and an early claim followed by a late check. Candidate invocation cap 1, auditor
cap 1 iff candidate exits 0, retries 0. Run in one pinned WSLc CPU container
with no network and separate candidate/auditor processes. No GUI, model, game,
GPU, physical input, or external effect.

**D.** `PASS_METHOD_SCOPED` only if the positive shared placement returns the
same exact finite claim disposition at total cost 3 versus route-local cost 6;
the no-gain control retains route-local checks at equal total cost 6; graph-only
cuts are not promoted as semantic evidence; wrong-target, stale, hidden-effect,
incomplete-graph and early-claim cases remain UNKNOWN/HOLD; the independent path
enumerator and six corruption controls pass. Any soundness or audit failure is
FAIL; missing/changed inputs or a runtime gate failure is STOP. No pass implies
that a real GUI graph is closed or an application oracle is adequate.

**C.** Cost values and graph-maintenance charges are stipulated fixture units,
not measured GUI costs. The graph and oracle are finite and fully enumerated only
for the declared positive fixture. Per-route checking may remain simpler or
cheaper once graph extraction and maintenance are priced.

**U.** Dynamic callbacks, hidden edges, concurrent effects, delayed observations,
nonterminating loops, privacy cost, and correlated verifier errors are not
represented. This T0 cannot establish runtime speed, GUI correctness, action
safety, product value, or a general placement algorithm. It is a synthetic
method test only.

## Frozen execution identity

- Allocation: `CLAIM-POSTDOMINATOR-6553-T0-WSLC-20261002-01`
- Base main: `3d768b0b1db255b5dacd099769a30a1b952a3f99`
- Branch: `research/6553-claim-scoped-postdominator-t0-wslc-20261002`
- Path: `research/analysis/claim_postdominator_6553_t0_20261002/`
- Runtime: WSLc 3.0.1.0; cached image
  `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`;
  `--pull never --network none --cpus 1 --memory 512m`.
- Cgroup/swap enforcement is not inferred from flags; report any WSL warning.
- No main-source files are changed. Candidate and auditor source/input hashes
  are recorded in `FREEZE.json` before formal invocation.

