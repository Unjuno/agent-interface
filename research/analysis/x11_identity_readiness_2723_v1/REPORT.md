# #2723 X11 identity-readiness preflight outcomes

Disposition: **HOLD_IDENTITY_DISCOVERY**. No PASS or formal acceptance is claimed.

## H/T/D/C/U

- **H**: readiness barriers and a WM_CLASS-capable query would yield two stable captures containing Inkscape, LibreOffice Calc, and Chromium with distinct typed identities.
- **T**: two first attempts of the read-only CI preflight on hosted Ubuntu; no keyboard/pointer input or model action was requested. The workflow was not container-pinned.
- **D**: two Actions run logs and the exact second-run JSON output are referenced in `ATTEMPTS.jsonl`. No uploaded artifact, complete raw JSONL capture set, source/container package manifest, or independent live-output audit was retained.
- **C**: PASS required all three applications in both captures with stable, complete, distinct identities. Neither attempt met this gate.
- **U**: this evidence cannot distinguish application startup failure from window visibility/query behavior or WM_CLASS exposure; it says nothing about task effects, latency, reliability, model utility, or real desktop use.

## Outcomes

1. Run [35457729725](https://github.com/Unjuno/agent-interface/actions/runs/35457729725), head `d01ae9360e83cdb04d49e339afe68b2f3fb636b8`: the two contract tests passed, then the workflow failed before the live preflight because `live_preflight.py` was absent from that commit tree (exit 2). This is a workflow/source-input STOP, not an experiment outcome.
2. Run [35457730688](https://github.com/Unjuno/agent-interface/actions/runs/35457730688), head `43f7de082f269af14cd64358100db3404aa971e8`: the two contract tests passed. The live preflight returned `HOLD_IDENTITY_DISCOVERY`: Chromium alone appeared in both captures; Inkscape exited 1 and LibreOffice produced no visible identity record. The runner itself exited 1 on the HOLD.

The second-run JSON says `input_operations=0`; the runner also prints `model_calls=0` and `network_calls=0`, but those counters are initialized constants, not independent instrumentation. The workflow installed packages over the network. The runner's `finally` sends termination signals but does not retain a cleanup receipt or wait for process exit.

## Provenance and limits

Both attempts are hosted-runner workflow executions, not pinned-container experiments. The first head did not contain the invoked script; the second preserved only its stdout in the Actions log. Contract tests cover the small pure identity predicate only; they do not audit the live captures. Treat this as a retained setup STOP plus one bounded read-only HOLD, not as a validated identity pass or task result. The original #2723 source/plan and predecessor evidence remain unchanged.
