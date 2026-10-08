# Issue #6147 T0 A04 — post-probe state/effect qualification

**Disposition: `PASS_METHOD_SCOPED` for the four frozen A04 fixtures.** The independent raw-only audit matched every enumerated tree across 12 depth/case layers, including counts, canonical tree digests, selected policy and terminal records. Seven explicitly injected mutation controls were rejected. This does not close #6147: its requested convergence control specifically names `p→q`, while A04's deliberately smaller convergence fixture reaches its shared terminal state after `p` alone.

## Results

| Fixture | Depth 0/1/2 policy trees | Resolved counts | Frozen observation |
|---|---:|---:|---|
| Initial A/B separated, terminal target stale | 1 / 4 / 13 | 0 / 0 / 2 | `p→q` produces LEFT/RIGHT; leaf states A2/B2 each have a distinct forbidden stale-target envelope; both decisions remain `YIELD_OR_REOBSERVE` |
| Initial C/D not distinguished, converges | 1 / 4 / 10 | 0 / 1 / 3 | `p` maps both candidate states to Z; current envelope allows only the fixture's scoped effect; initial-identity claim remains false |
| Action-equivalent aliases | 1 / 1 / 1 | 1 / 1 / 1 | Immediate `ACTION_EQUIVALENT_CURRENT`; no identity claim or probe |
| Safe-bisimilar action-different E/F | 1 / 4 / 13 | 0 / 0 / 0 | `YIELD`; exact output-equal, transition-closed safe relation; unsafe `u` has distinct output |

The raw retains every leaf's reachable terminal states, current effect
envelope, epistemic status, decision, and explicit false `initial_identity_claim`.
The auditor injects unsafe `u`, dropped branch, fabricated singleton, stale
initial-envelope action, false terminal convergence/effect, non-closed relation,
and recapture-as-identification mutations; all seven are rejected. It checks
fixed safe words through depth 2 and the exact unbounded relation certificate.

## Execution and evidence

- Allocation: `AI-6147-T0-20261003-04`; base main `43f7cd88d91af05036fae2100ec4e155c59e105c`.
- Host CPython 3.14.5, standard library only; candidate once (exit 0), then independent raw-only auditor once (exit 0); retries/tuning 0.
- RAW: 25,331 bytes, SHA-256 `3a7e3045562b3bc70f1d757df8088280e5e79c4241cce8209827d015561aa7e1`.
- Exact H/T/D/C/U and source freeze: [`PLAN.md`](PLAN.md), [`FREEZE.md`](FREEZE.md); machine-readable run record: [`RUN_RECORD.json`](RUN_RECORD.json).
- No model/GPU/GUI/network/physical input/container/OrbStack use. Analytical fixture only; no real probe safety, GUI-state completeness, effect truth, authority, product, or runtime claim.
- A03's qualified audit-control failure remains unchanged. A04's one-step convergence does not test the Issue-comment's exact two-probe non-identifying convergence control; a distinct fresh allocation is required for that narrower question.

## Additive follow-up

The exact two-probe non-identifying convergence control was run as distinct
allocation A05 under
[`../safe_probe_identifiability_6147_t0_20261003_a05/REPORT.md`](../safe_probe_identifiability_6147_t0_20261003_a05/REPORT.md).
A05 independently passed its scoped fixture gate for `p→q`; it does not edit
or replace any A03/A04 source or result.
