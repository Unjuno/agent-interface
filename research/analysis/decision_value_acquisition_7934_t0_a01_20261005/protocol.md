# Decision-value acquisition T0 A01 frozen protocol

The GitHub Issue #7934 preregistration comment (ID 5987336070) is authoritative.
This package instantiates its finite state/check profiles and deterministic draw
scheme. No profile, threshold, seed, source file, or decision gate may change
after the freeze comment.

Each hidden state is `(X,Y)`. Both routes are pre-admitted by all hard gates:
route A has utility `1[X=0]`; route B has utility `1[X=1]`. Candidate checks
are one-step alternatives. `xcheck` returns X with 0.8 accuracy. `ycheck`
reveals Y; the state priors encode independent or correlated observations.

The cost baseline picks the least-cost check under budget 0.06. The information
baseline picks the check with highest mutual information about the complete
hidden state, requiring at least 0.05 bits and staying within budget. The
decision-value policy maximizes exact expected best-route utility after the
check minus current best-route utility minus check cost; it selects only a
strictly positive net value. All ties resolve lexically, and route ties resolve
to A. The oracle uses exact modeled distributions to minimize expected route
regret plus check cost.

Evaluation uses 128 paired deterministic SHA256 draws per profile. For each
seed, hash `7934-T0-A01|<profile>|<seed>|<stream>`; convert the first 13 hex
digits to a uniform variate by dividing by `16**13`. Streams are `x`, `y`, and
`xcheck`. Use the frozen profile probabilities and inverse-CDF comparisons.

Stale source, unknown verifier dependency, and 0.10 unmodeled-state-mass
controls must return UNKNOWN with zero checks. With only route A admitted, every
policy must choose A, perform zero checks, and record no gate violation.

Formal execution is one WSLc container launch, pinned to
`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`,
network disabled, one CPU, read-only `/src`, writable `/output`, no retry. The
container runner verifies all frozen SHA256 identities before starting the
simulator or independent auditor.
