# Live evaluation exception and retained-status recovery

A test wrapper replaces only the evaluator entry with an injected RuntimeError.
Frozen socket v10 / interactive v26 still execute ordinary private X11 xterm
input, admission, release and finalization. The scripted controller submits the
correct token once, waits for terminal, then requests the shared outcome boundary
with a 200 ms timeout. No effect or independent evaluation event is emitted.

The outcome helper returns pending with task_success unset. A subsequent
finalization_status command retrieves the retained finalization_error with
failure_stage=evaluate, evaluation=null, admission_closed=true and
output_flushed=false. Repeating the status query returns the same retained
outcome without rescoring or resubmitting input. Task success remains unknown;
an evaluator failure does not imply that the application action failed.

Measured terminal-to-retained-error time is 19.587 ms. Terminal-to-first-status
socket return is 235.190 ms, including the deliberately chosen 200 ms outcome
timeout and query overhead. This is a single injected-fault measurement, not a
recommended universal timeout or model-side latency estimate.

Audit verifies one submit/accepted program, verified input release, three exact
AIT/PNG frames, the complete received record prefix, unchanged repeated status,
the matching persisted finalization result, and frozen runtime source hashes.
The saved token is correct when inspected after cleanup; that post-run audit
does not retroactively create a runtime independent evaluation. The runtime
exits zero and its socket is removed. Normal process exit is therefore also
insufficient evidence of task evaluation success.

Current limitation: finalization_status events lack request correlation. This
probe deliberately has a single session, one final program and sequential status
queries, and checks final_program explicitly. It does not establish safe matching
of concurrent status queries or cross-session recovery. The generic outcome
helper is unchanged and does not automatically issue this fallback command.
Before automating it, the status response needs explicit query identity and
matching rules; a snapshot can also legitimately be pending while finalization
is still running. No input replay should follow from either pending or error.

Evidence: results/failed-outcome-wait-01, probe_failed_outcome_wait.py,
failed_evaluation_entry.py and failed_socket_entry.py. Runtime records, request
responses, failure marker, saved token, frame artifacts, stderr and source hashes
are preserved. This is scripted fault injection, not actual assistant self-use
or proof of general recovery from broken output pipes, process death or hangs.
