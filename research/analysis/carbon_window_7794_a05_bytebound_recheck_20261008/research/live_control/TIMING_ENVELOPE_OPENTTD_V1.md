# OpenTTD adaptive live-control TimingEnvelope

Status: scoped positive result, not a speed promotion.

One fresh canonical OpenTTD save was controlled from screenshots through the
shared guarded pointer runtime. The successful v8 episode built the three-tile
road from A to C, kept the adjacent X row clear, and changed no surrounding
guard tiles. The game script independently checked all four conditions after
the model requested verification.

The episode took 111.853 seconds from initial-observation detection to semantic
completion, with 50 ms endpoint uncertainty. This is substantially slower than
ordinary human interaction and is not a human-tempo result.

## What changed during self-use

The retained sequence separates interface failures from model-control failures.

| Revision | Result | Finding |
| --- | --- | --- |
| v1 | Failed | Prompt declared a 1024x720 coordinate surface although the received image was 1280x800. The model clicked unrelated toolbar controls. |
| v2 | Failed | Full-image coordinates were corrected. Immediate observations after pointer movement arrived before delayed tooltips. |
| v3 | Failed | An 800 ms cancelable `dwell_observe` exposed tooltips, but only the last hover reached the next model call. The driver and supervisor also disagreed on the turn limit. |
| v4 | Integration failure | One model proposal batched three hover probes. Its 2.4 seconds of declared dwell exceeded the fixed 3 second transport wait after capture overhead, leaving a safely retained pending command. |
| v5 | Model-control failure | Timeout was derived from program contents and five contact sheets preserved intermediate tooltip frames. Luna-low still selected a road-vehicle list rather than a construction tool and exhausted eight turns. |
| v6 | Independently failed | Tooltip-purpose guarding rejected list/status semantics, but Luna-low ended by selecting `Build tramways`. Independent scoring found zero target road while the forbidden row and surroundings remained unchanged. |
| v7 | Task succeeded; packaging failed | Two Luna-low exploration turns followed by Astra-medium. The road passed all independent checks, but the result wrapper expected the obsolete `contract_satisfied` field after evaluation. |
| v8 | Succeeded | The current `success` evaluation field was bound. A fresh run repeated the adaptive route and passed the complete TimingEnvelope audit. |

Failures remain in `results/timing-envelope-openttd-01` through `-07`. Source
hashes in each plan bind a result to its revision; those revisions were not
edited after execution.

## Candidate mechanism

The execution-time `session_v10.py` added one bounded passive operation:

```json
{"op":"dwell_observe","delay_ms":800}
```

The wait is cancelable, accepts 100–2000 ms per step, and limits combined dwell
to 3000 ms. The successful driver computes its transport timeout from declared
dwell and program length instead of applying a fixed three-second assumption.

During final integration review, that revision name was found to collide with an
existing drag-checkpoint `session_v10.py`. The original v10 was restored. Exact
execution bytes are retained under `frozen_sources/<sha256>/session_v10.py`.
A second inferred name, v11, also already existed and was restored before any
further run. The current delayed-hover candidate therefore continues as the
next unused revision, `session_v22.py`. The audit accepts the archive only when
the current named source does not match the hash.

`openttd_contact_sheet_v1.py` retains each observation produced after a dwell.
The next planner image contains the current full frame followed by labeled
toolbar strips. One model boundary can therefore receive up to three delayed
tooltips collected by one bounded local program. A deterministic construction
probe passes on Windows and WSL.

The planner policy also binds the intended operation to tooltip meaning.
`Display/list` does not authorize construction, and `Build tramways` does not
satisfy a request to build roads. This meaning check currently exists in the
planner prompt; the strict local schema validates only JSON shape, bounds and
supported operations.

After two Luna-low exploration turns, the candidate escalates unresolved visual
semantics to Astra-medium. This is an authored fixed route, not a learned
stagnation detector. v7 and v8 both reached independent success with the route;
v7 then failed only while packaging the already-positive score.

## Successful v8 measurement

All observed endpoints below use one Windows supervisor process and one
`perf_counter_ns` clock domain.

| Measurement | Result |
| --- | ---: |
| Initial observation detected → semantic completion detected | 111,852.730 ms ±50 ms |
| Wrapper-observed model waits, eight calls | 91,780.735 ms |
| Proposal published → useful feedback detected, seven actions | 18,285.649 ms total |
| Individual useful-feedback intervals | 3,740.164; 3,738.445; 3,761.243; 870.059; 2,684.608; 1,643.626; 1,847.504 ms |
| Model route | 2 Luna-low, then 6 Astra-medium |
| Actual reported model input | 126,420 tokens |
| Actual reported output / reasoning output | 1,503 / 766 tokens |
| Exact runtime frames | 44 |
| Contact sheets presented | 5 |
| Durable calls / append records | 28 / 57 |

Model waits occupy about 82.1% of the measured end-to-end interval. Batched
hovering reduced the number of planner boundaries needed to inspect multiple
icons, but it also intentionally spends 0.8 seconds per tooltip. This episode
does not isolate the contact sheet's causal effect because it has no matched
single-hover or single-model control.

Provider receipt, provider first token, runtime receipt and exact OS injection
endpoints remain `NOT_RECORDED`. No time is inferred between their clock
domains. Buffered TimingEnvelope v2 records events in tens of microseconds in
the earlier isolated test but may lose events if its process dies before close.

## Evidence

- Successful artifacts: `results/timing-envelope-openttd-08`
- Supervisor clock and result: `results/timing-envelope-openttd-control-08`
- Independent audit: `results/timing-envelope-openttd-08/audit.json`
- Independently failed semantic-guard run: `results/timing-envelope-openttd-06`
- Successful task with packaging failure: `results/timing-envelope-openttd-07`
- Shape controls: `results/openttd-proposal-schema-v5.json`
- Audit command: `python research/live_control/audit_timing_envelope_openttd_v1.py`

The audit replays all 28 durable exchanges against 223 runtime records, decodes
all 44 exact frame packets, verifies current source hashes, checks every model
proposal and reported usage record, validates one clock domain and explicit
missing endpoints, and recomputes the final interval. It passes on Windows and
WSL.

## Decision

Retain batched delayed observation, content-derived timeout budgets and exact
target-semantic guards as candidates. A subsequent preregistered matched block
allocated the identical task to fixed Luna-low, fixed Astra-medium and adaptive
routing. Fixed Luna failed the hard score; fixed Astra and adaptive passed, with
fixed Astra using fewer turns, reported input tokens, frames and durable calls
in that one block. The authored adaptive route is therefore not promoted. See
`OPENTTD_MATCHED_MODELS_V1.md`. Repeated counterbalanced blocks and a matched
human baseline remain required before a route or human-tempo claim.
A second reversed-endpoint block later reproduces fixed-Astra success and
fixed-Luna failure while adaptive fails the independent score after a visual
completion claim. See `OPENTTD_MATCHED_MODELS_V2.md` for the cumulative decision.
