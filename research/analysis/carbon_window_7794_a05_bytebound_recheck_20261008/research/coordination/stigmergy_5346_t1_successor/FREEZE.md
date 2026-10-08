# Issue #5346 T1 freeze

Status: preregistered before execution; formal invocation has not occurred.
Predecessor: Issue #5346's T0 STOP, raw SHA-256
`c867e23a1de036f0c8b9a6c85e6016ca742445a7ea5d668f749bfad8db5edba0`.
No predecessor source or output is modified or reused as a T1 outcome.

## H/T/D/C/U

- **H:** When every policy is subject to the same independent atomic target-admission gate, scoped expiring markers can reduce redundant proposals / rejected admission attempts versus no coordination. Local markers require fewer explicit coordination messages than central claims. Markers never grant authority.
- **T:** Exhaustively enumerate deterministic schedules with 2–4 workers, one shared target, staggered proposal order, observation delay, marker loss/duplication/staleness, owner crash, and retry. Compare `NONE`, `CENTRAL_CLAIMS`, and `LOCAL_MARKERS`. Keep worker order, task duration, lease TTL, and atomic gate identical. Record proposals, blocked admissions, explicit coordination messages, completions, recovery, and invariant violations separately.
- **D:** PASS only if every arm has zero overlapping admitted leases; every completion follows an admitted lease and effect transition; malformed, stale, forged, duplicated, or absent markers never change admission authority; and local markers reduce redundant blocked attempts in at least one declared delayed-observation stratum without increasing unsafe events or explicit coordination messages versus central claims. FAIL on any authority/invariant violation or unrecoverable owner loss. HOLD/UNCERTAIN if these quantities cannot be isolated.
- **C:** PASS supports only this finite deterministic model. It does not establish strategic-agent behavior, real interface visibility, wall-clock speed, or production safety. If lease gating alone eliminates meaningful duplicate cost, stigmergy is not justified.
- **U:** Live trace visibility and scope; strategic/adversarial workers; realistic timing, clock skew, and task-cost distributions.

## Frozen schedule and policy

The complete scenario list is generated deterministically by `simulate.py`: worker count 2, 3, 4; each permutation of worker arrival order; observation delay 0, 1, 2 ticks; marker condition `clean`, `lost`, `duplicated`, `stale`, `forged`; owner outcome `complete` or `crash`. One target is contested per schedule. A single lease gate is the only code path that may admit work in every policy arm. The gate logs owner, generation, acquisition, expiry/release, and completion. Marker contents are never read by the gate.

All fixed constants and the arm-specific advisory behavior are in the frozen source. No tuning is permitted after formal execution. Raw output is one JSONL record per schedule-arm pair in deterministic scenario and arm order. The independent auditor is a separate executable; it reconstructs all policy counts and checks all rows and invariants from raw only.

## Allocation/resource boundary

No model, GUI, network, GPU, or external service. Python standard library only. Use the locally cached image
`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
The only formal command is `python simulate.py --out /out/raw.jsonl` in a fresh
`--network none`, read-only-root container with one CPU, 256 MiB memory, and 64
PIDs, after independent Docker monitoring confirms no active competing allocation.
No retry. Preserve any nonzero exit or malformed/partial output as the first
outcome; do not rerun this allocation.

## Result boundary

This experiment is a finite software-model test, not an empirical multi-agent or
interface experiment. Synthetic timing and visibility are assigned, not measured.
No result can grant production authority, validate shared GUI actions, or close
the global roadmap.
