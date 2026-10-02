# Issue #6147 T0 A03 — prospective experiment plan

Allocation: `AI-6147-T0-20261003-03`. Fresh successor to A02's `STOP_CANDIDATE_RUNTIME_ERROR / NOT_EVALUATED`; A02 remains unchanged and is not input here. Main base: `b521912b9da1fa292f2e4fed1f1ae695c4a7658e`. All artifacts are additive in this directory. Host CPython, standard library only, no model, GUI, network, physical input, or container. This follows the Issue's analytical T0. OrbStack is not part of this protocol; the shared exclusive container lane is not touched.

## H / T / D / C / U

**H.** A finite deterministic fixture with aliased observations can be resolved only to the extent justified by safe adaptive observations: find the minimum depth-two discriminator for action-different states, stop at action equivalence without asserting hidden identity, and yield for states with a safe-output-preserving bisimulation. Never admit an unsafe informative probe.

**T.** Independently authored candidate and raw-only auditor enumerate all output-contingent trees through depths 0, 1, 2 for three frozen two-state fixtures. Beliefs and observation branches are retained; every reachable leaf records the remaining next-action/effect envelope. The auditor checks tree sets/counts/digests, fixed-word completeness for two deterministic hypotheses, and exact bisimulation closure distinct from a depth-limited miss. Five corruptions must reject: unsafe probe, missing output branch, aliased singleton assertion, non-closed bisimulation, and same-image recapture claiming identity. Candidate once; auditor once only after exit zero. Any first error is preserved as STOP; no retry/tuning.

**D.** `PASS_METHOD_SCOPED` only if independent enumeration and optimum match; the separable pair's minimum depth is 2; the equivalent pair resolves only as action-equivalent; the impossible pair has no safe solution through depth 2 and its relation is exactly closed; unsafe probes are absent; all corruptions reject; and terminal reachable action/effect envelopes match the leaf contract. Otherwise FAIL or STOP, without retry.

**C.** A typed application query or ordinary YIELD may be simpler and safer; fixture separation may only reflect an authored table. Action-equivalence needs independent real-app evidence outside this experiment.

**U.** Finite deterministic synthetic machine only. No real GUI state/probe safety, stationarity, model completeness, workflow transfer, effect truth, authority, product safety, or runtime behavior is established.

## Freeze/execution record

Construction checks may precede freeze but are not formal results. Before the one formal candidate call, record source hashes, interpreter identity, UTC time and clean output-path status in `FREEZE.md`. After freeze do not edit candidate/auditor/fixture. Candidate writes a unique RAW exactly once. Nonzero exit: retain exact command/status/stdout/stderr and raw hash in STOP; do not invoke auditor. Zero exit: invoke independent auditor once. Local CI is scoped to these scripts and applicable additive-artifact repository checks; report each gate separately.
