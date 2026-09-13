# Shared optional-effect / final-evaluation wait policy

Actual browser self-use exposed that Calc alone currently publishes early
effect_evidence. A caller waiting exclusively for that event unnecessarily times
out on Chromium even after a successful independent evaluation.

outcome_wait.py builds a read-only socket request for both effect_evidence and
independent_evaluation, scoped to the originating transport request. The first
available matching event ends the wait. If the result is an early effect, it
returns the explicit effect status plus a continuation waiting only for final
evaluation. A final evaluation directly ends waiting on adapters without early
effects. No runtime capability guess, command resend or lease renewal is needed.

| Received evidence | Caller state | Task success |
|---|---|---|
| Early VERIFIED / CONTRADICTED / UNKNOWN | effect_observed; continue to final evaluation | unset |
| Final evaluation with boolean success | evaluated | exact evaluation boolean |
| Timeout or bounded batch limit | pending; resume from returned cursor | unset |
| Stream closed without outcome | unresolved; no automatic continuation | unset |
| Gap, missing/conflicting identity, rejection | needs_reconciliation | unset |

An early VERIFIED effect is scoped evidence, not automatically whole-task success.
Program terminal records are retained in the batch but are not completion of the
task. Failure of evaluation is an evaluated false result; absence of evaluation
is unresolved. Callers must retain batches before continuing; the returned cursor
does not acknowledge or resolve any intervening interrupt.

probe_outcome_wait.py passes twelve cases in results/outcome-wait-01. Two replay
actual Calc/browser delivery streams through the existing EventCursor v4. Ten
controls cover terminal-only pending, later evaluation resumed without a command,
false/malformed evaluation, other/missing request identity, rejection, closed
stream, retention gap and UNKNOWN effect. Calc retains the full prefix across its
two outcomes; browser completes with final evaluation directly. Sources and
recorded inputs are hashed.

This is a local candidate read policy, not a default transport change. Tests use
recorded streams and injected cursor events, not a live delayed HTTP server.
The helper assumes the existing EventCursor batch contract and same-session
identity model; it is not an arbitrary-input validator or restart-safe protocol.
It does not automatically retry, poll forever, or recover from a missing final
publication. In particular, finalizer faults may require explicit status
inspection after timeout. Model latency, token use and causal speedup are not
measured here. Next integrate this policy at a live socket caller and exercise
an actual delayed or failed finalization path.
