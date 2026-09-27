# Explicit finalization failures

`finalization.py` separates close_admission, evaluate and publish. A close failure
prevents scoring. An evaluator exception or malformed result leaves evaluation=null;
it is not synthesized as task success=false. A publisher exception or unconfirmed
output retains the already computed evaluation and marks failure_stage=publish.
Successful finalization can legitimately contain task success=false.

Seven injected cases in results/finalization-01 cover successful and unsuccessful
tasks, admission-close failure, scorer exception, missing boolean success, publisher
exception and false publication confirmation. They verify stage ordering and absence
of downstream calls after failure. These are isolated callback tests, not seven live
desktop failure scenarios or timeout tests.

Experimental interactive_v20 uses the helper after the reserved final terminal.
Its emit reports whether stdout flush succeeded; receipt-journal failures propagate.
The helper's status is written to finalization-status.json after finalization returns.
If that write also fails, a best-effort stderr record includes the outcome. No
filesystem/pipe fallback is guaranteed if every output channel fails. No fsync or
crash-safe atomic persistence is claimed. Post-controller reservation still blocks
new programs. Legacy explicit-finish behavior remains unchanged.

Actual X11 subprocess cohort final-score-cancel-03 validates an invalid reservation
followed by an accepted final hold, explicit cancellation and independent task failure.
The terminal is cancelled with verified release, exactly one evaluation reports
false, and finalization status is finished with admission_closed/output_flushed true.
Source hashes and exact observation reconstruction were checked. This is scripted
integration evidence, not new actual-assistant performance evidence. I/O errors in
the live GUI path were not injected by this cohort.

The source terminal may be signaled even if output raises, allowing finalization to
observe worker shutdown. A permanently blocked callback can still block joining;
the helper provides stage classification, not deadlines or interruption. Partial
output followed by an error is ambiguous and must not be replayed automatically.
Output-flushed is not model delivery, ACK or comprehension. The default entrypoint
is unchanged. Next test live publication failures and expose finalization status
through a bounded status query, without rerunning an oracle or reviving authority.
