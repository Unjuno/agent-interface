# Issue #5516 T12 — branch-readiness beyond visible trace equality

## Provenance and boundary

This is a fresh additive finite-semantics probe for the open hypothesis in
Issue #5516. It does not alter T0–T11, their raw output, or their dispositions.
No matching branch or open PR was found in the bounded GitHub search on
2026-10-01. The repository's Docker queue has an unresolved cross-context
provenance hold (#5085 comment #5917772963); this exact model is decidable from
its finite transition systems and therefore runs as a host-local semantic
experiment. It is not a Docker/OrbStack run and makes no GUI/timing claim.

## H / T / D / C / U

**H:** Equality of all finite visible traces is insufficient to establish
substitutability when an agent's legal next-action set depends on the hidden
branch reached after a shared prefix. Strong bisimulation over visible labels
will distinguish such a branch-readiness mismatch while accepting an exact
positive control. The test is tau-free, so strong bisimulation is the relevant
bounded relation; it makes no claim about divergence or weak-bisimulation
semantics.

**T:** Freeze three acyclic finite-LTS pairs. (1) Exact positive control: same
OPEN→SAVE behavior. (2) Branch-split pair: system P reaches one of two hidden
post-OPEN states, one enabling {SAVE,COPY}, the other {SAVE,DELETE}; system Q
reaches one state enabling {SAVE,COPY,DELETE}. Their complete finite visible
trace sets are equal, but neither pair of post-OPEN states can match all
transitions under bisimulation. (3) Negative label control: replace DELETE by
ARCHIVE on Q, yielding a visible trace-set mismatch. Candidate outputs graph
edges and summaries once. A separate raw-only auditor recomputes trace sets and
the greatest strong-bisimulation relation solely from graph edges, and returns
an independently derived post-OPEN action-set witness. Seven corruption
controls mutate/delete graph edges, create a cycle, or alter summaries.

**D:** `PASS_BRANCH_READINESS_METHOD_SCOPED` iff the positive control is
trace-equal and bisimilar; the branch-split pair is trace-equal and not
bisimilar with a post-OPEN distinguishing action; the negative label control
is neither trace-equal nor bisimilar; raw-only audit has zero errors; and all
seven corruption controls reject or ignore the relevant mutation as preregistered.
Any candidate false-equivalence summary accepted by the auditor is FAIL.

**C:** This supplies a hand-authored finite witness, not a prevalence estimate.
Trace equality might still be sufficient for a particular interface contract
if only complete successful traces matter and next-action availability is
irrelevant. The model has no tau, clocks, nondeterministic environment, or
external effects.

**U:** No real adapter, GUI, user task, observation noise, action authority,
timing, transport, latency, safety rate, or product equivalence is tested.
The labels and branch structure are stipulated. A result supports only the
method distinction for this witness; application to #5516 needs an authored
observation alphabet and real traces.

## Frozen source and commands

- Base: current `origin/main` `e32ace71fa1158ca8d5eec13fe620a1a51c1ff00`.
- Execution: host CPython 3.14.5, standard library; no network, model, GUI,
  Docker, OrbStack, or external effect.
- Candidate: `candidate.py`; independent auditor: `audit.py`; mutation suite:
  `corruption_controls.py`; construction tests: `test_t12.py`.
- Preregistered construction command:
  `python3 -B -m unittest discover -s research/analysis/observation_bisimulation_branch_readiness_5516_t12 -p 'test_*.py' -v`
- Frozen candidate command (exactly once):
  `python3 -B research/analysis/observation_bisimulation_branch_readiness_5516_t12/candidate.py > research/analysis/observation_bisimulation_branch_readiness_5516_t12/raw/candidate.jsonl`
- Frozen audit command (once):
  `python3 -B research/analysis/observation_bisimulation_branch_readiness_5516_t12/audit.py research/analysis/observation_bisimulation_branch_readiness_5516_t12/raw/candidate.jsonl > research/analysis/observation_bisimulation_branch_readiness_5516_t12/raw/audit.json`
- Frozen mutation-control command (once):
  `python3 -B research/analysis/observation_bisimulation_branch_readiness_5516_t12/corruption_controls.py research/analysis/observation_bisimulation_branch_readiness_5516_t12/raw/candidate.jsonl > research/analysis/observation_bisimulation_branch_readiness_5516_t12/raw/corruption-controls.json`

Record source hashes before candidate execution. One candidate invocation only;
no retry, tuning, or replacement. Construction tests are not formal output.
