# Recovering saved-effect queries across a real client disconnect

The current saved-effect caller previously had live Calc evidence but only
simulated checkpoint response loss. This experiment uses the same current
cause-servo / Executor9 / durable-v5 path in a private Chromium form. It closes
each query connection after sending the request and before receiving any bytes,
then recovers the original result with one command-free read.

Both query losses recover. Before form input the result is UNKNOWN because the
application has not produced a saved file. The model then selects the visible
Value field, enters `t000240` and presses Return. After that input the recovered
query is VERIFIED. The caller finishes through independent scoring, with no
extra model decision or form input. Each query appears exactly once in the
runtime command stream.

## Shared caller changes

`recover_query_once_v1.py` performs one read of an explicitly identified pending
artifact query. Its guard runs under the existing durable journal lock. It
rejects a missing pending query, another operation or a changed original request
ID before transport. Timeout, conflicting evidence, or a closed reply without
evidence retains pending state. Transport errors propagate. It never sends a
command, clears uncertainty by itself or treats an effect as whole-task success.

`phased_submit_v2.py` accepts an explicit task proposal validator and retains the
v1 result format and default Calc validator. This removes the numeric-text
restriction from the shared control mechanism without broadening the Calc task.
The pointer activation, fresh handoff observation, focus/binding checks, keyboard
deadline and release requirements are unchanged. Two archived Calc phase results
replay exactly with the default validator.

`form_proposal_schema_v1.py` allows only the declared alphanumeric task value,
bounded clicks and a small keyboard vocabulary. Validation does not rewrite the
model's actions. The form driver supplies this validator to the shared caller.
Browser navigation to the private fixture is scripted setup; selecting the form
field, entering its value and submitting it are actual model decisions from the
received screenshot. No browser DOM or external website is used.

The model prompt and completion policy explicitly disclose saved-file evidence.
UNKNOWN is supplied as model feedback. The caller consumes VERIFIED according to
that policy and invokes the independent evaluator. This remains an opt-in
artifact-enabled profile, not a pixel-only computer-use baseline.

## Live measurement

Source: `results/checkpoint-recovery-form-01/audit.json`. One fresh private
Linux/X11 Chromium episode, seed240, requesting gpt-5.6-luna / low through the
existing responder runner. Served model identity and monetary cost remain
unavailable.

| Measurement | Observed value |
| --- | ---: |
| Actual model decisions | 1 |
| First capture to independent evaluation, including navigation setup | 12.966 s |
| Form screenshot capture to independent evaluation | 11.812 s |
| Model runner duration | 9.812 s |
| Reported input / output tokens | 9,690 / 128 |
| Reported cached input tokens | 1,792 |
| Activation-to-keyboard handoff | 236.865 ms |
| Runtime events / exact transported frames | 119 / 14 |
| Durable journal records | 31 |
| Normal exchanges / abandoned query attempts / recovery reads | 13 / 2 / 2 |
| Query resends / input after VERIFIED | 0 / 0 |

| Recovered query | Recovery read | Client close to reconciled state | Runtime receive to emission |
| --- | ---: | ---: | ---: |
| UNKNOWN before form input | 12.768 ms | 34.869 ms | 6.203 ms |
| VERIFIED after form input | 30.032 ms | 62.942 ms | 44.533 ms |

Recovery-read timing includes the helper, transport and durable result commit.
Close-to-reconciled timing also includes the live-process check, attempted new
command refusal and artifact recording between the loss and read. These use the
Linux caller clock. Model runner time uses its Windows clock; cross-platform
clock values are not subtracted. The measurements are individual observations,
not service guarantees or a comparison with Calc's larger artifact queries.

This is deliberate local response abandonment, not an observed organic network
failure. At connection close, server receipt is unknown to the caller. The later
correlated command echo and result establish that the query was executed. The
read succeeds without repeating it. Process death, journal migration, cursor
eviction, and arbitrary combinations of failures are outside this live test.

## Verification and limits

Ten offline controls test matching UNKNOWN/VERIFIED, timeout, closed channel,
read error, unrelated reply, conflicting echo, missing pending state, another
pending operation and a different expected identity. Invalid text, boolean
coordinates, a browser Save chord and another pointer action in the keyboard
tail are refused before transport; duplicate JSON keys are rejected. The first
control harness incorrectly expected the pending-state error before the
closed-channel error. Its failure and source are preserved in
`results/query-recovery-controls-01/`; corrected controls pass in `-02` without
changing runtime behavior.

The live audit replays every received event slice, continuation, pending write,
reconciliation and all 31 journal records. It checks the exact model image,
prompt, proposal and raw-response hashes; reruns target and shared phase checks;
replays setup observations; and decodes all 14 frames exactly. All six input
programs completed with verified empty input ownership. Every admission was
before its deadline. The form's Return step started and completed once.

The positive checkpoint archives the exact 13-byte `value=t000240` application
output. The audit hashes and reparses these bytes after the private source is
removed, matches the final exported output, and checks independent final scoring.
UNKNOWN before input has no artifact digest and is not misrepresented as an
empty or contradictory sample. The trace contains input after UNKNOWN and only
`finish` after VERIFIED. The exported app file does not count HTTP requests; the
one-submit claim here is about the admitted form Return operation, not an
independently counted HTTP-delivery guarantee.

Commands for replaying the audit in the recorded WSL environment:

```text
python3 research/live_control/audit_checkpoint_recovery_form_v1.py
```

The existing worker's non-atomic sampling, lack of actor attribution, and
CPU/GIL or blocked-output limits still apply. A positive value sample is not a
lease, input authority, power-loss durability guarantee or general task oracle.
The frozen Calc experiment remains unchanged. This extends actual current-stack
evidence to a second saved-effect task; it does not establish human-like tempo
or broad domain coverage.

Next reduce duplicated planner-facing evidence while preserving the pending
query identity, UNKNOWN semantics, saved-effect scope and access to raw records.
Measure actual model tokens and decisions on fixed contexts before adopting a
compact representation. Issues #24, #34 and #39 remain broader than this result.
