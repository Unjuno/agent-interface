# Host timing of a real pre-dispatch relay refusal

The timing reader previously assumed every reply echoed `id` and `tool`. The
actual relay's pre-dispatch refusal has neither field: it returns `status=refused`,
`dispatched=false`, an unchanged `next_id` and an error. A real public MCP session
reproduced `KeyError: 'id'` in the reader after a valid refused reply. The retained
before.json and before-source.py preserve the failure at main 89f1784d0.

The primary host used the existing instrumented client to send an invalid
native-only tool to the public relay, then explicitly requested tool discovery,
then close. Local attempts were 1/2/3 while protocol IDs were 1/1/2. The actual
server stayed lazy: close reported no release attempt or connection-close attempt,
and no display or GUI allocation was opened. Transport exit was zero.

The corrected reader binds a refusal to its pending local attempt, request,
unchanged protocol ID and reply hash. Its call row records the relay refusal;
the interval is included in timing totals. Malformed refusal shapes, a consumed
ID, or a non-false dispatched flag are rejected. An ambiguous post-dispatch
outcome stays unknown and never becomes a pre-dispatch refusal. This is a
read-only measurement change, not permission to retry an uncertain action.

The new after.json summarizes all three actual replies. Normal completed-run
output remains unchanged: the frozen 29-call timing verifier still reproduces
its original report exactly. Unit tests now use the real refusal shape rather
than two fabricated successful replies with a repeated ID. The existing real
public-relay subprocess test also feeds actual emitted envelopes into the reader;
its synthetic timestamps test decoding only, not latency.

raw.tar.gz and manifest.json retain the actual host/server exchange, original
failure, corrected report, complete integration-check logs and tested sources.
Run `python3 -O runtime/results/host-timing-refusal-01/verify.py` from the repository
root to check hashes and recompute the actual report without running archived code.
This does not measure GUI performance, task success, model latency or token cost.

Validation: 262 protocol and 106 harness tests passed in WSL; full logs are archived.
