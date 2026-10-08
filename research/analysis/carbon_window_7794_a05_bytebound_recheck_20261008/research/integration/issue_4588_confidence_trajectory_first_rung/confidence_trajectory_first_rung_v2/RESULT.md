# Issue #4588 synthetic first rung v2 — matched allocation

## H — Hypotheses

The test asks whether fixed causal velocity/acceleration rules separate
synthetic action/no-op trajectories, and how this trades false actions against
missed actions under confidence noise. No learned model or execution authority
is involved.

## T — Test

One frozen Docker Desktop run: 16 scenario families × 128 replicates per
condition, evaluated at clean, ±0.01, and ±0.12 confidence perturbation. Each
replicate shares its irregular time intervals and noise vector across all
scenario templates. Four frozen arms receive the same 2,048 rows per
condition. Full aggregate confusion counts and paired-alias audit counts are
in `METRICS_TRANSCRIPTION.json` (transcribed from the single JSON stdout).

Command:

```powershell
docker run --rm --pull=never --name issue4588-confidence-probe-v2 --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 --mount 'type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\.agent-interface-docker-validation\issue4588\research\integration\confidence_trajectory_first_rung_v2,target=/study,readonly' --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16777216 --workdir /study --entrypoint python python:3.12-slim /study/probe.py
```

## D — Result / disposition

`HOLD_NOOP_STALL_RISK` and `HOLD_ACCEL_NOT_BETTER_THAN_VELOCITY` for any
shadow-transfer gate. Integrity assertions passed and the clean acceleration
alias was separated correctly: current-only and level+velocity agreed across
all 128 matched action/no-op pairs, while level+velocity+acceleration
disagreed across all 128. However, the acceleration arm's aggregate accuracy
was 89.55% versus 93.75% for level+velocity in clean data; action recall was
58.20% versus 100%. Under stress noise, action recall fell to 26.17% for
acceleration and 19.34% for smoothed trajectory.

False-executable rates were lower than CURRENT_ONLY in all three conditions
for all temporal arms. In clean data, acceleration reduced unnecessary
actions to zero but classified 188/512 true ACTION rows as NO_OP; smoothed
trajectory classified 262/512 as NO_OP. This is a substantial stall-risk
tradeoff, not a safe efficiency win. Noise-stress aggregate accuracy fell to
68.51% (acceleration) and 67.04% (smoothed). The fixed rule shows a synthetic
feature-separation mechanism, but does not support a broad action-selection
benefit.

Do **not** advance to caller-visible shadow or live action from this result.
The issue's next rung requires a real, caller-visible sequential corpus and an
independent correctness measure. No such corpus is part of this allocation.

## C — Controls and provenance

- v1's integrity failure and results are preserved separately and unchanged.
- Seed `20260928`; 128 replicates; three declared noise levels; common clock
  intervals and perturbations across scenario counterfactuals.
- `contract_controls=PASS`; generated alias invariants passed for every
  replicate in every noise condition; malformed/missing/stale/epoch-invalid
  histories fail closed to YIELD; causal EWMA prefix assertion passed.
- `model_trained=false`; `authority_granted=false`; no GUI, provider, network,
  or input was used.
- Probe SHA-256:
  `6ca95c352f60366642820daa19e557c5972ad7485d27902c54b4df794615f0b9`.
- Preregistration SHA-256:
  `625f2906db172b1df060bab68b123f344ee7f6d39c88f6b31fd9376fc71b00ec`.
- Image `python:3.12-slim`, ID
  `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  Linux/amd64. Docker Desktop Engine 28.5.1. No-network, read-only root and
  source, all capabilities dropped, no-new-privileges, 1 CPU, 256 MiB memory,
  32 PID limit, 16 MiB tmpfs. `--rm` removed the container.
- The CLI emitted machine-readable JSON once. The complete aggregate and
  pair-control counts are preserved as a structured transcription in
  `METRICS_TRANSCRIPTION.json`; verbatim stdout was not separately redirected
  to a file. No rerun was made to recreate it.

## U — Limits / stop conditions

All conclusions are confined to these deterministic synthetic templates and
the four hand-authored rules. They do not establish confidence calibration,
real model behavior, generalization, GUI correctness, end-to-end task effect,
human tempo, or token/cost benefit. Stop this allocation; future transfer
requires a new frozen design based on actual caller-visible sequences and
explicit missed-progress/stall scoring. Preserve v1's `FAIL_INTEGRITY` and
this v2 HOLD; neither may be silently replaced by a favorable synthetic claim.
