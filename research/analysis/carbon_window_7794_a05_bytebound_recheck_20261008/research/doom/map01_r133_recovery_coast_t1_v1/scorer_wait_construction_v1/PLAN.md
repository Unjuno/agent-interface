# Independent scorer during delayed command delivery — construction experiment

Status: `FROZEN_HOST_CONSTRUCTION`. This is one bounded integration probe for the #59 T1 measurement gap. It is not a live MAP01 trial, a Docker run, a formal allocation, or evidence of causal recovery benefit.

## H / T / D / C / U

- **H:** The existing 35 Hz main-thread scorer stdin adapter can observe and retain both a positive kill-count transition and a negative death-count transition while its real OS pipe has no command available, without including scorer payload in the line later returned to the controller.
- **T:** One WSL2/Linux x86-64 CPython 3.12.3 invocation, real anonymous pipe, one delayed `finish` line (writer delay 350 ms), one deterministic fake scorer. Baseline has 0 kills/0 deaths; at elapsed monotonic time >=60 ms it reports one kill; at >=140 ms it reports one death. The exact current-main component files and candidate/auditor sources are SHA-256 pinned in `FREEZE.json`. No ViZDoom, X11, GUI/input, Docker/OrbStack, model/provider, GPU, network, or GitHub write during execution.
- **D:** `PASS_SCORER_EVENTS_RETAINED_DURING_COMMAND_WAIT_CONSTRUCTION` only if: the exact command line is returned unchanged; at least three scorer samples are retained; exactly one `KILL_COUNT_INCREASE` positive and one `DEATH_COUNT_INCREASE` negative event are independently recorded strictly after wait start and before command send; all scorer rows/events remain `controller_visible=false`; scheduler sample count agrees with retained samples; and the separate auditor reproduces those checks and rejects (a) an omitted event, (b) controller-visible mutation, and (c) an event timestamp moved after command send. Any source drift, unexpected event inventory, command/scorer mixing, incomplete pipe/process cleanup, or audit mismatch is `STOP`/`FAIL` with original raw preserved; there is no rerun.
- **C:** Existing poller/adapter/clock source at the exact hashes in `FREEZE.json`; CPython 3.12.3 on WSL2/Linux x86-64; one real anonymous pipe with a delayed writer; deterministic scorer values with real monotonic sampling timestamps. The 350 ms delay is a test harness condition, not a model latency distribution.
- **U:** Proves only that the retained construction components can be composed to record scorer-only state changes during an empty command wait. It does not show integration with `session_map01_v6.py`/v23, plan/step/actuation binding, accurate game scoring, useful-effect causation, key-up timing, threat coverage, survival, task completion, or user-visible performance.

## Coordination and disposition

The #5156 live owner-thread X11 request and #59 T1 matched recovery/coast request are distinct, request-only allocations. This experiment spends neither. The completed #5486/#5489 nullable-key work is not repeated. Output is confined to this new additive path; no shared runtime, queue, predecessor result, or other branch is modified.

## Commands

Exactly one candidate invocation: `python3 candidate.py`.
Only if its exit code is zero, exactly one independent audit invocation: `python3 audit.py`.
