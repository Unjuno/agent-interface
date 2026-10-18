# Ordinary decoder recursion repair

Claim and pre-result gates: Issue #6869 comment5964980152. Same owned branch,
starting source b1ebb2f. No historical formal allocation is replayed.

H: json.loads recursion-limit failures escape current request admission and can
terminate the persistent relay before it refuses the line. This is a transport
continuity/correctness gap, not a useful-task or speed hypothesis.

T: fixed depth4096 array/object strings, before the first accepted call and after
one accepted call, with depth32 array/object forwarding controls. The portable
committed-source process additionally receives native-tool, overflow, duplicate
and deep-JSON refusals before current-ID list/validate/close. Only the decoder's
RecursionError is added to the existing pre-SDK refusal handler.

D: refuse with dispatched:false and unchanged next ID, never invoke the inert
SDK client for the refused line, and permit the subsequent current-ID request.
Accepted SDK uncertainty must still consume ID and forbid replay. A failed
reproduction means no source repair; test failures remain evidence.

C: interpreter recursion limits are finite and differ by environment. Returning
a typed refusal does not introduce a fixed depth cap or make arbitrary nesting
supported. The legacy research relay is unchanged.

U: bounded ordinary tests only. No memory-exhaustion guarantee, general malformed
stream recovery, nonreturning backend behavior, clock/physical release, GUI,
useful effect or latency/efficiency conclusion.
