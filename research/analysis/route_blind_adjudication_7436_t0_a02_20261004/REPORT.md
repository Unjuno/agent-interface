# A02 result — PASS_METHOD_SCOPED

## Decision

The independent auditor reconstructed all six blinded packets exactly, confirmed no explicit canary in the blinded JSON, verified the seed/order and changed-order control, and accepted the route mapping only after the complete score commitment. All eight preregistered corruptions were effective and rejected. A02 therefore passes the finite synthetic presenter/custody method gate.

## Formal record

- Candidate command: `python3 -I research/analysis/route_blind_adjudication_7436_t0_a02_20261004/candidate.py`; one invocation, exit 0, six packets, precommit reveal denied, six scores committed.
- Auditor command: `python3 -I research/analysis/route_blind_adjudication_7436_t0_a02_20261004/audit.py`; one invocation, exit 0, `PASS_METHOD_SCOPED`, 8/8 effective mutations rejected.
- Candidate and audit JSON, stdout, run record, and frozen source/fixture hashes are retained under `results/` and `PRELAUNCH_FREEZE.json`.
- A01 remains `FAIL_SETUP_ENTRYPOINT`; it is neither rerun nor regraded.

## Scope and limits

This is only a synthetic method result. The “assessor” scores are deterministic protocol probes, not human judgments. All files share one checkout/process; the probe does not create confidentiality or prevent a real assessor from reading escrow. Natural visual, temporal, or semantic cues may reveal route identity after explicit labels are removed. It establishes no observer-bias effect, route-favorable false-positive rate, false-negative margin, assessor agreement, user preference, route recommendation, or product benefit. Issue #7436 T1 remains open and would require prospective matched evidence, separate assessors, a frozen rubric/analysis and any required participant consent/ethics review.

## Environment

Host-only macOS arm64, standard-library Python. OrbStack image-store inspection STOP is retained from A01 and was not retried. No container, network, model, provider, GUI, game, application, GPU, or external participant was used; no container-isolation claim is made.
