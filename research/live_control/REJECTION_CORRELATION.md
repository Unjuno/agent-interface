# Runtime receive identity for rejected commands

Candidate interactive_v24 assigns a monotonically increasing runtime_request_sequence
to every input line, before JSON parsing. Parsed command records and rejection
records share that sequence. A bounded declared_action_id is copied only from
submit/cancel commands; command_op is separately bounded. These are caller-declared
labels, not validated input authority or proof of action execution. The sequence
identifies a received line within this runtime process, not across restarts.

The command variable resets to None on every input line. Malformed JSON therefore
cannot inherit the previous parsed command's ID. Non-object JSON is explicitly
rejected. No request payload is copied into the rejection; existing command logs
retain their prior behavior.

Two live private-X11 xterm cohorts test five rejected inputs followed by successful
token entry and independent artifact scoring. Cohort 01's supposed stale case
actually fails evidence/expected sequence consistency; it is retained under its
original label with that limitation. Cohort 02 first advances the observation via
a settle program, then reuses the valid historical observation reference. This
reaches the real latest-observation admission rejection.

| Cohort 02 input | Receive sequence | Declared action | Rejection |
|---|---:|---|---|
| Historical observation | 3 | stale | latest observation required |
| Expired lease | 4 | expired | validity expired |
| Unsupported step | 5 | malformed_steps | unsupported operation |
| Malformed JSON | 6 | null | parse error |
| JSON array | 7 | null | command object required |

Only the observation-advance and final valid programs are admitted in cohort 02;
the final output is exactly t991024. Command/rejection sequence joins are checked;
the malformed-JSON line has a rejection but no parsed-command record. Raw runtime
sources, exact frames and owner close are audited by audit_rejection_correlation.py.
Evidence: results/rejection-correlation-01, -02, and rejection-correlation-audit.json.

This does not yet change socket v7's unattributed_rejection handling or correlate
its request IDs with runtime sequences. The same caller action ID can be reused
across rejected attempts, so action ID alone must not stand for request identity.
Concurrent readers, invalid UTF-8, process restart and transport/runtime identity
joins are untested. The five negative cases are scripted known inputs, not general
planner performance or actual token-cost evidence. No default promotion or freeze
credit. Next connect explicit runtime receive identity to the transport request
without guessing from arrival order or the currently active action.
