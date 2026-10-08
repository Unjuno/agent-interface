# Issue #7934 decision-value calibration boundary — T0 A02

## Outcome

**PASS_CALIBRATION_BOUNDARY**, with a concrete misspecification limit. The
independent auditor rederived all 4096 SHA256-seeded observations in 32 grid
cells with zero errors. Decision-value and the true-distribution oracle chose
the same check/stop and had equal exact regret-plus-cost in all eight calibrated
cells. Hard-gate violations were zero, and both the marked distribution-shift
and 0.10 unmodeled-mass controls returned UNKNOWN with zero checks.

In 12/32 unmarked mismatch cells, decision-value produced higher sampled route
regret than both cost-only and maximum-information baselines. When the assumed
and true check accuracies landed on opposite sides of 0.5, the posterior acted
on the signal in the wrong direction. For example, qt=0.2/qm=0.8/cost=0.02
gave regret 0.8046875 versus baseline 0.546875; qt=0.8/qm=0.2/cost=0.02 gave
0.765625 versus 0.5. The shift flag was supplied by the test; this did not test
whether an agent can detect calibration drift.

A01 remains a separate frozen FAIL_AUDIT in [PR #7943](https://github.com/Unjuno/agent-interface/pull/7943).
A02 is a new calibration-boundary successor and does not alter or retry A01.

## H / T / D / C / U

**H.** The one-step decision-value rule should match the exact oracle when its
likelihood is calibrated, but may have worse regret than cost/information
baselines when an unmarked model likelihood is wrong. Marked shift or
unmodeled-state controls must return UNKNOWN with no check.

**T.** Two pre-admitted routes depend on balanced latent X. A direct check has
true accuracy qt and modeled accuracy qm from {0.2, 0.4, 0.6, 0.8}; a perfect
independent nuisance check observes balanced Y. Direct costs are {0.02, 0.12}.
Four policies were evaluated over 32 cells and 128 paired deterministic seeds
per cell. Exact definitions and seed derivation are in `protocol.md` and
`profiles.json`; the freeze and append-only outcomes are on [Issue #7934](https://github.com/Unjuno/agent-interface/issues/7934).

**D.** PASS_CALIBRATION_BOUNDARY requires a complete independent raw audit,
decision-value/oracle selection and exact total-loss agreement in all eight
qm=qt cells, zero hard-gate violations, and UNKNOWN/zero-check marked controls.
All requirements passed. The auditor independently reported the 12 mismatched
cells where decision-value regret exceeded both baselines; these are scoped
synthetic findings.

**C.** The assumed likelihood, prior, route utility, nuisance check, and costs
are artificial. The oracle shares the same finite model family. The test marks
distribution shift explicitly and does not detect it.

**U.** No live GUI/tool calibration, production safety, task effect, user value,
or end-to-end latency is established. CPU-only was sufficient; no GPU, GUI,
model, input, or user data was used.

## Runtime and evidence

One WSLc 3.0.1.0 launch used Python 3.12.15 from the pinned local image
`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`,
network none, one configured CPU, read-only source, writable output, and zero
retries. CPU quota enforcement was not measured. Formal outputs, eight gzip
parts, hashes, independent audit, and exact child streams are under `formal/`.
`reconstruct_formal.py` verifies and reconstructs the large files without
rerunning A02.
