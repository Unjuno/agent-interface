# Belief-space recovery margin — T0 A02

Allocation: \`BELIEF-RECOVERY-8527-T0-A02-20261008\`

This is a fresh successor allocation to #8527 A01. A01 construction hashes and its pre-run infrastructure STOP remain unchanged. No live-control, GUI, model, task, or probabilistic claim is in scope.

## H / T / D / C / U

**H.** On a finite, complete, partially observed interface fixture, exhaustive bounded belief-set reachability distinguishes states that are individually recoverable from beliefs with no single safe observation-contingent policy, and identifies the first feasible horizon. Omitted transition coverage, stale generation, unverified recovery markers, and incomplete transition maps remain UNKNOWN.

**T.** Ten frozen synthetic cases × horizons 0–3 produce 40 case-horizon rows. The fixture has explicit hidden states, action availability, nondeterministic (including uncontrollable) successors, observation partitions, forbidden states, a verified marker, and bounded budgets. Cases cover: fully observed recovery; aliased opposite-action recoveries; a safe information-gathering split; the same cue with a one-step deadline; an uncontrollable unsafe branch; an alternate route reaching the marker exactly at the horizon; omitted transition mass; stale observation generation; an unverified marker; and an incomplete transition map. Candidate uses bounded recursive policy search. The independent auditor enumerates every finite policy tree, verifies each witness and compares against separately sealed labels. Two singleton controls accompany the aliased case. Three frozen input mutations remove a hidden belief state, remove an uncontrollable outcome, and move the marker earlier.

**D.** \`PASS_BELIEF_RECOVERY_MARGIN_SCOPED\` requires all 40 candidate rows to equal both the sealed expected labels and an independently enumerated policy-tree result; all reported policies must be safe and cover every observation branch; the two singleton controls must be recoverable while their joint aliased belief is not; the exact-horizon boundary must pass with zero margin; all four incomplete/stale/unverified cases must be UNKNOWN; and all three input mutations must be rejected. Any mismatch is retained as FAIL/HOLD/STOP, with no retry.

**C.** State-by-state recovery unions, a single sampled trajectory, or a point-belief baseline may disagree with a common policy over an aliased belief. A conservative fresh-observation/YIELD gate may be sufficient without computing any recovery margin. The finite fixture is authored to expose a coordination boundary and may overstate its practical frequency.

**U.** This is a deterministic toy-model method test only. No calibrated probabilities, real-time seconds, actual GUI transitions, hidden live states, independent application effects, runtime behavior, MAP01 control, task completion, safety guarantee, or product benefit is inferred.

## Frozen run contract

- Main base, source hashes, image identity and canonical input/truth digests are recorded in \`FREEZE.json\` before either formal CLI invocation.
- Runtime: Microsoft WSLc, cached \`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f\` (\`linux/amd64\`); Docker is not used.
- Two separate disposable containers, each with one requested CPU, network disabled, \`--pull never\`; source and inputs are mounted read-only and each result directory is separate/writable. No shared image/container is reused as a task workspace.
- Run \`candidate.py\` exactly once. Only if it exits 0 and its exclusive-created raw file exists, run the independent auditor exactly once. No candidate/audit retry or output replacement.
- No global container inventory or cleanup is allowed. Record the two exact owned container IDs and their scoped \`--rm\` completion receipts; do not inspect or mutate another owner's resource.
- Retain full commands, stdout/stderr, exits, wall time, exact raw/audit files, image/runtime metadata, and checksums. Treat any cgroup/swap warning as an unverified resource limit, not as a test failure or an effective cap.
- This allocation may launch only after a clean current-main source freeze, a collision check, and explicit exclusive WSLc-lane clearance under the governing #6389/#6693/#7924/#7970 gates. Version/help or an absent process snapshot is not lane clearance.

## Expected labels (sealed before execution)

| Case | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| fully-observed | not recoverable | 1 step | 1 step | 1 step |
| aliased-opposite-actions | not recoverable | not recoverable | not recoverable | not recoverable |
| safe-information-gathering | not recoverable | not recoverable | 2 steps | 2 steps |
| late-cue (budget capped at 1) | not recoverable | not recoverable | not recoverable | not recoverable |
| uncontrollable-destroys-recovery | not recoverable | not recoverable | not recoverable | not recoverable |
| exact-horizon-alternate-path | not recoverable | not recoverable | 2 steps | 2 steps |
| omitted-transition-mass | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| stale-observation-generation | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| unverified-marker | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| missing-transition | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

For recoverable rows, \`margin = effective_budget - minimum_steps\`; UNKNOWN and not-recoverable rows have no numeric margin. The explicit row-wise sealed oracle is \`truth.json\`.
