# Issue #8648 C01 — coupled route/task-mix hysteresis construction

Status: preregistration. This is a synthetic construction test under Issue #8648, not a user/workflow observation and not evidence that real route adoption is path-dependent.

## Question and source boundary

The source literature establishes that decisions can alter future distributions (Perdomo et al., ICML 2020, https://arxiv.org/abs/2002.06673) and that two-strategy games coupled to renewing/decaying environments can admit bistability under stated model conditions (Tilman et al., Nature Communications 11, 915 (2020), DOI 10.1038/s41467-020-14531-6). Neither establishes this behavior for GUI workflows. This allocation asks only if a transparent route/task-mix finite model separates reciprocal feedback from one-way and exogenous controls.

## Frozen model

State is (a,q) in [0,1]^2, where a is use share of an optional route and q is the share of a task stratum for which route-relative benefit differs. Fixed opportunity count is 100 each period. External advantage theta is swept over 21 values from -0.30 to +0.30 in 0.03 increments. Parameters are beta in {2,10,20}, gamma in {0.5,1.5}, delta in {2,10,20}. The held-out parameter slice is delta=20; all other tuples are descriptive training-grid coverage, with no tuning after execution.

Let sigmoid(z)=1/(1+exp(-z)), relaxation r=0.25, and d=theta+gamma*(q-0.5). The candidate response targets are:
- COUPLED: a*=sigmoid(beta*d), q*=sigmoid(delta*(a-0.5)).
- ONE_WAY: a*=sigmoid(beta*theta), q*=sigmoid(delta*(a-0.5)); task mix responds to uptake but does not feed back into route choice.
- EXOGENOUS_ONLY: q*=sigmoid(delta*theta), a*=sigmoid(beta*d); task mix depends on the external condition only.
- ZERO_FEEDBACK: q*=0.5, a*=sigmoid(beta*theta).

Every update is synchronous relaxed iteration: (a,q) <- (1-r)*(a,q)+r*(a*,q*). For each arm and parameter tuple, run UP and DOWN sweeps, each from LOW=(0.01,0.01) and HIGH=(0.99,0.99). At each theta, iterate until max coordinate change <1e-10 or 10,000 updates. Record nonconvergence as HOLD; do not omit it. Report route utility 100*a*d and the fixed correctness gate (100 opportunities in every profile; no utility can compensate for a correctness failure).

For COUPLED at a converged endpoint, let A=beta*gamma*a*(1-a), B=delta*q*(1-q); the relaxed Jacobian spectral radius is max(abs(1-r+r*sqrt(A*B)), abs(1-r-r*sqrt(A*B))). For controls, calculate the Jacobian from the exact frozen transition map. This stability calculation is an audit diagnostic, not an empirical stability claim.

## Hypothesis and gates

H: In the held-out delta=20 slice, at least three distinct held-out (beta,gamma) settings have at least three adjacent theta points where LOW- and HIGH-initialized COUPLED sweeps converge to distinct stable equilibria (|a_LOW-a_HIGH| >=0.25, both spectral radii <0.99) and their period utility differs by at least 0.05, while no control arm meets the same gate.

D:
- PASS_METHOD_SCOPED if the independent auditor reproduces all frozen profiles/endpoints, 4 arms, both directions and initial states; all required points converge or are explicitly HOLD; 5/5 in-memory mutation controls are rejected; and every arm preserves the fixed opportunity/correctness gate.
- H_PASS_SCOPED if PASS_METHOD_SCOPED and the preregistered held-out H condition is met.
- NO_HYSTERESIS_SCOPED if PASS_METHOD_SCOPED and the H condition is not met.
- FAIL_METHOD for any missing/duplicate profile, incorrect transition or audit mismatch, omitted nonconvergence, or changed opportunity/correctness accounting.

C: A single-valued route response, one-way rebound, or exogenous task drift may explain route/task changes without reciprocal feedback or hysteresis.

U: The response maps, finite task strata, slopes, and utilities are authored. This is not an estimate of user preferences, actual task-mix shifts, welfare, GUI correctness, or deployment benefit. The candidate and auditor can validate code against this model, not the model's external validity.

## Execution custody

Candidate/auditor will be frozen on branch research/8648-hysteresis-c01-20261009 before execution. Candidate output is to be persisted byte-for-byte (compressed transport is permitted only if decompression is lossless and hash-checked) before any result is described as promotable. Candidate and independent auditor each get one invocation; preserve STOP/HOLD/FAIL and do not rerun.
