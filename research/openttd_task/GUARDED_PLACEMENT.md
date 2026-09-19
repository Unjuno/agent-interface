# Guarded placement study — 2026-09-13

The previous three-road/two-edge score admitted an overlong drag. Replaying the
published visual coordinates in a fresh canonical save built an additional road
on tile 681. The old score still passed; the new surrounding-state score failed.
This is a newly observed replay result, not a retrospective measurement of the
original episode's unrecorded surrounding tiles. Original evidence stays intact.

The assistant then visually inspected the C tile's white selection outline and
chose a corrected endpoint. A separate fresh episode passed target ownership,
bidirectional connectivity, forbidden-row clearance **and** surrounding road/owner
preservation through the same `session_v9`/`executor_v3` input path.

## Contract fixed before these runs

`guarded_score.py` retains the old contract and additionally compares all
non-target tiles in a 7×6 neighborhood against the initial restored observation:
map x=36…42, y=8…13 (42 tiles including the three targets). Road presence and owner
must remain unchanged outside the target. This permits pre-existing roads rather
than assuming all surrounding tiles start empty. `observer_v2` adds only queries;
its save-compatible GameScript identity remains InterfaceTask version 1.

This bounds the side-effect check; it is not full-world protection. Trees, terrain
height, buildings, partial-road bits, other road types, funds and edits beyond the
neighborhood are not independently checked. Autonomous world changes can also
affect preservation; this score does not attribute every change to the controller.
Longer tasks need explicit treatment of that distinction.

| Episode | Controller | Old score | Guarded score | Observations |
|---|---|---|---|---:|
| `results/guard-01/episode` | scripted replay of prior coordinates | pass | fail: extra road/owner change at 681 | 6 |
| `results/guard-self-use-01` | assistant, screenshot decisions | pass | pass: no surrounding changes | 7 |

The replay omits the old full-frame quiet wait and uses fixed coordinates; its
1.43-second interval is not agent inference performance. The corrected visual
episode used two programs and took 43.42 seconds from initial capture to last
terminal, including assistant reasoning/tool delays. Neither comparison supports
a speedup claim: programs, knowledge and controller differ. The corrected episode
is a development case informed by prior failure, not held-out generalization.
No final oracle was delivered to the controller until it finished each episode.

`audit_guard.py` verifies launch source hashes, canonical save bytes, identical
initial 42-tile observations across the two fresh restores, all 13 exact image
reconstructions, final engine records, terminal releases and owned process exit.
It also rejects missing, duplicate, contradictory and incorrectly typed guard
records, plus a synthetic outside-target owner change. The real extra-road
negative is separate from these synthetic parser/counterfactual checks.

## What this changes in architecture discovery

Successful input execution and a narrow task score can hide a placement error.
A visible target preview before committing a drag supplied useful feedback in
this case; waiting for the entire animated screen to become quiet did not.
Keep independent side-effect scoring alongside success and feedback latency.
Do not count this task refinement as a shared-runtime promotion or freeze pass.
The input implementation itself is unchanged in this study.

Next extend beyond this known placement: fresh geometry/tasks and desktop pointer
regressions, resolve the hand-made GUI startup fault, and assess observation age
and feedback during bounded pointer continuation. Mindustry's fixed-state planning
pilot remains part of the domain portfolio; DOOM remains one stress domain.

```sh
python3 research/openttd_task/audit_guard.py
python3 research/openttd_task/guard_replay.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out research/openttd_task/results-local/new-negative-replay
python3 research/openttd_task/interactive_v2.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out research/openttd_task/results-local/new-visual-episode --controller assistant
```
