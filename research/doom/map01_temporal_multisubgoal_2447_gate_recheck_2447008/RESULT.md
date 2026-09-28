# Issue #2447 — post-continuation phase gate recheck

Decision: **PASS_CONSTRUCTION_FAIL_CLOSED_STOP** for this single construction rung. It is not a formal Issue #2447 pass.

## H/T/D/C/U

- **H:** When a phase gate says `NO_DROP` and requests a bounded continuation, do not begin another subgoal until fresh visual evidence recomputes as `DROP_COMPLETED`; `NO_DROP` or `UNKNOWN` must stop.
- **T:** One Docker Desktop Linux/amd64 MAP01 episode, seed 2447008, temporal gate, requested heading 120°. After the inherited first phase and exactly one bounded extra-forward, collect 450ms of input-free pixels and recompute the inherited temporal optical-flow threshold before any handoff.
- **D:** Pass this construction rung only if saved recheck frames independently support the reported status, no next-subgoal input occurs unless status is `DROP_COMPLETED`, and all emitted holds are verified released. This run exercises the fail-closed `NO_DROP` branch.
- **C:** Pinned local image/source bundle; network disabled, container root filesystem and runner mount read-only. Hidden game state is excluded from the handoff guard.
- **U:** One seed and one `NO_DROP` branch only. No endpoint comparison, false-positive/fault matrix, formal rates, held-out transfer, or episode completion evidence.

## Outcome

The initial temporal gate reported `NO_DROP` and requested one bounded continuation. Afterward, the input-free observer captured four frames over the frozen 450ms window. Independent Docker audit recomputed the three adjacent pairs: one pair met the <=100ms timing and >=80-track eligibility criteria (525 tracks, median vertical flow 0.0px); zero eligible pairs met the <= -20px drop threshold. Recomputed and reported status both remained `NO_DROP`.

The runner recorded `STOP_PHASE_NOT_CONFIRMED`. No `next_subgoal` directory was created, so no next-subgoal action was emitted. The observer recorded 0 inputs. All 33 observed owner-release records across setup/phase/continuation were verified empty. Independent audit errors: none; formal rows: 0; retries: 0.

This establishes only that this constructed fail-closed branch stopped instead of authorizing a handoff after an unresolved phase. It does not validate the `DROP_COMPLETED` allow branch or broader safety/performance.

## Evidence and reproduction

Raw package: [issue2447-gate-recheck-construction-2447008.zip](raw-evidence.zip), SHA-256 `69736575b4e8537bf2cac232b0f560056df7266147d6c0f297dbf4061df9b3b8` (1,871,339 bytes). It includes the frozen source, runner, plan/schedule, 32 raw evidence files and independent audit. Container image ID: `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`.

```sh
python -B /runner/src/run_case.py --out /evidence/issue2447-gate-recheck-construction-2447008 --class drop --seed 2447008 --gate temporal_gate --heading 120 --source /tmp/project
python -B /audit/src/audit_gate_recheck.py --evidence /evidence/issue2447-gate-recheck-construction-2447008 --out /evidence/AUDIT_POSTHOC.json
```

Formal schedule rows spent: 0.