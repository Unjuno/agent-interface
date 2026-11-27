# Experimental eventfd in owned Fake X caller: r543

One fixed-order isolated Linux container run connected the experimental
one-shot eventfd notification to the actual owned-process MCP path, using a
spawned Fake X owner and fixture-injected parent UNKNOWN. Four cases produced:

| Case | Observed |
|---|---|
| Known parent | synthetic target effect present; control passed |
| UNKNOWN before parent RPC check | refusal and no synthetic effect; passed |
| UNKNOWN while pipe send was gated | refusal and no synthetic effect; passed |
| UNKNOWN after child check | synthetic target effect present; regression failed |

The parent/child clock records in the final case show the effect after the
injected transition; more fundamentally, fixture gates enforce that order. The
effect is a synthetic pixel receipt for one fake key event. No real X input,
user GUI, actual cancellation, key-up, task completion or MAP01 was tested.
The last failure is retained rather than omitted. The overall unittest exit is
1, as recorded in `raw.zip`.

`raw.zip` (SHA-256
`5925af0b51523c625b852ee0e88ed37d8a158d292fb42437055a7788c52dfb2d`)
contains the pre-run conditions, base commit, exact working-tree patch,
captured unittest output and four synthetic case directories. Zip integrity was
checked after creation. The output reports the test result; image digest and
Docker flags in the conditions are not independently attested by the JSON.

This prototype has no descriptor lifetime management, safe error handling or
proven semantics for repeated signals, draining, fd loss/reuse, process death
or write saturation. Eventfd readiness after admission does not revoke a
running operation or drain display-server queues. A successful pipe-send case
is not a general fence or finite-recovery proof. The source remains a draft.
Review also found that a failed notification can occur before the parent stores
its UNKNOWN flag, and that the prototype treats any poll event as readiness,
including invalid-descriptor events. Artifact references inside captured reports
may still point to the original container temporary path; the archived files
must be inspected from their own extracted location.
