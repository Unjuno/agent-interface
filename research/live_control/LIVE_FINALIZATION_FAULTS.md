# Live finalization output faults and read-only status

Test-only finalization_fault_entry wrappers inject one-shot errors into the actual
interactive process, while private X11 xterm executes a scripted type/Return task.
Three cases run against interactive_v20 and then interactive_v21:

| Fault | Supervisor sees score event | Retained state |
|---|---:|---|
| Raise before score JSON write | 0 | publish error, computed task success retained |
| Flush bytes, then raise | 1 | publish error, output completion unconfirmed |
| Evaluator raises | 0 | evaluate error, evaluation unknown |

All six saved text files independently contain t991024 and terminals verify release.
The scorer-exception case still records evaluation=null: supervisor knowledge of
the saved file must not be substituted for the failed runtime evaluator. Eighteen
exact frames plus runtime and injection-wrapper hashes were checked.

The flush case deliberately proves that visible bytes and confirmed publication
are different. The supervisor receives the score event, but its delivery ID has
no successful flush receipt. The system must not automatically rerun input or
scoring to resolve that uncertainty. These are injected stream exceptions, not
physical disk/network outages or permanently blocked writes.

Experimental interactive_v21 advertises `finalization_status`. The request has
no input action: it snapshots the retained finalizer outcome and returns available,
pending or not_requested. The snapshot cannot reopen admission, re-evaluate the
task or change the historical output status. The finalizer assigns it before
best-effort status-file persistence. After each injected fault, two queries return
identical outcomes and original timestamps; score-event counts remain unchanged.
Results are in live-finalization-faults-02, with baseline faults in -01.

The test supervisor polls the local status artifact to coordinate fault assertions;
that is test machinery, not a controller capability or an extra oracle input.
The query itself returns through the normal output lane and can fail or block if
the lane remains broken. A returned original output_flushed=false remains historical
even when the later status response is successfully flushed. Neither is model ACK.
Only completed-status queries are live-tested here; pending/not_requested branches
and malformed query fields are not fully qualified. Default entrypoints remain
unchanged; no live speed or token improvement is claimed from these fault tests.

The final-scoring request boundary now has success, cancellation and one-shot
output/error evidence. Next focus on reducing the earlier modal decision gap with
ordinary fresh admission, rather than expanding this benchmark-only oracle into
a control policy. Keep production semantic feedback distinct from privileged scoring.
