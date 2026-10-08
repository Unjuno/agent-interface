# MAP01 terminal score agreement audit v1

Status: **POSTHOC PASS 2/2; frozen live-02 allocation INVALIDATED by duplicate execution.**

Base: `810479785d1adb7e785962d3e16d6b1e4bd29f79`

Issue: #76

## Finding

The live v13 measurement construction correctly creates one `direct_final_sample` when the game proxy closes, but the retained v1 integration audit does not compare that final scorer state with v12 `score.json`. That leaves the explicit O3-G2 terminal-agreement gate unenforced.

Separately, the same push SHA started the formal workflow twice. Both run `34968759795` and run `34968781910` reached and completed the formal probe, despite the frozen allocation requiring one run with no retry. Therefore neither run can be selected as the unique preregistered first outcome.

## New audit

`audit_map01_terminal_score_agreement_v1.py` fails closed unless:

- `score.json` and `scorer-samples.jsonl` exist;
- exactly one scorer record has `direct_final_sample=true`;
- that record is the final scorer record;
- its payload is `independent-progress-sample-v2`;
- `map_exit`, `episode_finished`, `player_dead`, `death_count`, and `kill_count` match `score.json` with exact Python type and value equality.

Six deterministic regressions pass, including value mismatch, bool/int type alias, duplicate-final, non-final direct sample, and missing-file negative controls.

## Retained live artifacts

Both distinct live artifacts pass the new audit post hoc:

| Run | Artifact digest prefix | Samples | Missed periods | Five-field agreement |
|---|---|---:|---:|---|
| 34968759795 | `dabbc5630b99...` | 19 | 0 | PASS |
| 34968781910 | `274623504341...` | 19 | 0 | PASS |

Both terminal states are `map_exit=false`, `episode_finished=false`, `player_dead=false`, `death_count=0`, `kill_count=0`. Their event/scorer file hashes differ, so these are two executions rather than two references to one artifact.

The existing integration audit also passes both runs: zero scorer leakage, one completed two-key hold, two verified v3 release transitions, direct retained-input measurement readiness, and zero missed scorer periods.

## H / T / D / C / U

### H — falsifiable hypothesis

The independently persisted final scorer state is exactly equal to the historical v12 terminal score on all five outcome fields, and disagreement is detectable without exposing scorer state to the controller.

### T — minimum test

Six deterministic audit regressions plus retrospective execution against every retained artifact produced by the duplicated live-02 workflow.

### D — decision

- Measurement mechanics: **PASS replicated 2/2**.
- Terminal score equality: **POSTHOC PASS 2/2**.
- Frozen `one run, no retry` allocation: **FAIL — duplicate formal execution**.
- Recovery-vs-coast efficacy allocation: **NOT AUTHORIZED**.

A new formal allocation is required. It must invoke this strict audit as part of its frozen gate and enforce single-execution semantics before the formal probe begins.

### C — break modes

A future real terminal episode can diverge between v12 score reads and proxy-close sampling; a second final sample can be introduced accidentally; a schema change can remove or coerce a field; workflow concurrency can duplicate a nominal one-shot allocation again.

### U — uncertainty

The two live passes reduce uncertainty about current measurement plumbing, but they do not repair the preregistration violation and do not establish recovery-policy efficacy. The next allocation must be a new frozen experiment, not a relabeling of either live-02 run.

## Cross-domain relevance

- **Measurement science:** an independent evaluator must be cross-checked against the system's established terminal observation, not merely sampled nearby in time.
- **Distributed systems:** workflow idempotency and single-writer/lease semantics are part of experimental validity when a CI runner is the laboratory.
- **Control/HCI:** actuator-release telemetry and task-outcome telemetry can both be correct while the experiment protocol itself is invalid; those validity layers must remain separate.
