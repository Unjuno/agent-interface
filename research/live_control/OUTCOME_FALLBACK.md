# Bounded status fallback in the caller

outcome_fallback_v2.wait_with_status performs at most two exchange calls:
one request-scoped outcome read, and only after an outcome timeout, one
request-scoped finalization_status command. Each invocation generates a fresh
status query ID. It sends no input command, never rescores, and does not loop or
retry on transport exceptions. All attempted requests and received replies are
returned in a transcript, including the uncertain request on an exception.

Available status must identify the expected final_program independently of query
identity. Direct outcome/effect records must also name that program. Finished
status requires boolean evaluation success, closed admission and flushed output.
Finalization errors retain their evidence but leave task_success unset. Pending
status returns pending; not_requested returns unresolved. Gaps, malformed results
and identity/program mismatches require reconciliation. A batch limit continues
through the original read policy and does not trigger a status query.

The first measured candidate omitted the independent program check on the direct
outcome path. Its source and passing narrow tests remain preserved as v1 evidence.
The v2 candidate adds that check. Ten injected-exchange controls pass, including
direct correct/wrong-program outcomes, pending status, false evaluation,
wrong query/program, status timeout, transport exception and batch limit. These
are control tests, not live pending-to-available transition measurements.

Live socket v11 / runtime v27 evaluator-fault probes verify the fallback itself
uses two calls and one original submit. The v2 run retrieves the retained error
234.408 ms after terminal, including a deliberate 200 ms outcome timeout. Three
exact frames, verified input release, unchanged repeated retained status,
concurrent query matching, no replayed query resend, and returned prefix slices
are audited. Both measured candidates and their manifests are retained under
results/outcome-fallback-live-01 and -02. The live probe additionally performs
status-correlation checks after the two-call fallback; those extra calls are not
included in its two-call count. This is scripted fault injection, not assistant
latency or a causal speedup comparison.

The bound is a call-count bound plus requested server waits, not a hard wall-time
deadline: the injected exchange implementation must bound connection and I/O.
The tested socket exchange has an eight-second timeout. No automatic polling,
durable session identity, authentication, lost-publication reconstruction or
process-restart recovery is provided. A returned pending state does not itself
grant a retry or fresh input authority. Intervening records are retained in the
transcript; callers must inspect them, and should not interpret cursor progress
as interrupt acknowledgement. A final result could race with the status query
and appear earlier in its batch; this conservative helper retains that batch
but interprets the scoped status snapshot only.

Next exercise live pending-to-available snapshots and actual assistant self-use
through this helper. Model-side tokens, costs and human-tempo claims remain
unmeasured. The v2 helper is a candidate, not a default promotion.
