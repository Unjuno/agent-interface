# Astra guard-observation availability audit A01

This read-only audit asks whether the retained 2026-10-05 Astra attempt can establish when the current V39 health validity guard would have crossed its threshold during a pending planner turn. It does not reinterpret the attempt or replace the fresh live threat-exposure test required by current `docs/CURRENT_GOAL.md` r139.

## H / T / D / C / U

- **H:** The retained raw event stream and controller report do not contain per-observation health/ammo signal samples or policy-invalidation outcomes, so they cannot establish whether or when the current guard would have fired before a model answer returned.
- **T:** Verify the frozen event/report SHA-256 values, count observations and decision records, and independently search those records for typed signal samples, guard outcomes, and policy invalidations. Candidate and auditor use separate traversals of the immutable inputs.
- **D:** `PASS_OBSERVABILITY_GAP_ONLY` requires exact frozen input hashes, the retained 852-event/530-observation/13-decision counts, and zero runtime health-signal or invalidation records in those artifacts. Any mismatch is a failure/hold; no inference is made from the absence of a log field beyond that artifact.
- **C:** The archived HUD frames and video can support coarse visual transcription, but their timing does not reconstruct the exact current signal-reader sample, guard decision, or controller cancellation point.
- **U:** This is a raw-availability audit of one historical run. It does not establish how current main would behave, whether a guard crossing occurred, causality for health loss, or any live threat response, release, recovery, or gameplay outcome.

## Reproduction

From the repository root, run the candidate once and then the independent auditor once:

```sh
python3 research/doom/map01_astra_guard_observation_audit_a01_20261007/candidate.py
python3 research/doom/map01_astra_guard_observation_a01_20261007/auditor.py
python3 research/doom/map01_astra_guard_observation_a01_20261007/auditor_v2.py
```

The candidate writes `results/a01.json`; the original audit writes `results/audit-a01.json`; the recursive raw-only audit and three nested-field mutation controls write `results/audit-v2.json`. Inputs are immutable retained artifacts pinned in `FREEZE.json`; no GUI, game, model, input, container, or live allocation is used. The v2 audit supplements the retained A01 audit rather than replacing it.
