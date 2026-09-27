# Confirmation recovery, actual lease expiry and an evidence retention failure

The assistant used the shared v28/v12/v6 interface in a new private browser
fixture. An initial POST without confirmation returns a visible page saying
nothing has been saved, preserves the typed value and adds a confirmation
checkbox. Only a POST with confirm=yes stores the value used by the ordinary
independent evaluator. The server does not know the task's expected token.

This confirmation behavior was designed by the assistant for the study; it is
not an unseen challenge or a general recovery benchmark. The actual lease expiry
described below was unplanned. Initial image 001.png, form 005.png and confirmation
page 013.png were viewed before choosing their next inputs. Reports and original
images were returned in the same outer tool result. To reduce the displayed text,
observation records were shown with event/sequence/image/context/semantic status;
all other records were shown fully. Full raw reports remain on disk. This projection
is not a validated general compression policy and has no measured token benefit.

## Actual sequence and checks

1. Navigate to the form and inspect the existing draft.
2. Request replacement and submit using terminal mode, leaving input admission open.
   This request is rejected before execution because its 30-second lease expired.
3. Read a new clock after the explicit rejection and issue a newly chosen program.
   Reuse the historical form observation with the returned matching sequence;
   no new image capture or automatic lease renewal is claimed. Runtime admission
   still checks validity. The rejected request has no accepted, observation or
   terminal event; it was not an uncertain transport result being blindly retried.
4. The replacement program completes, but the page says nothing was saved and
   requires confirmation. The caller has not requested final task evaluation.
5. Inspect that page, use Tab/Space/Tab/Return to check confirmation and save.
   This final program requests outcome mode. Independent evaluation confirms
   exactly value=t991029. Finish cleans up the session, which exits successfully.

The audit verifies three admitted programs, one explicit rejection, 21 exact
reconstructed frames, verified input release, assistant-declared evidence,
request lineage, the full 38-record delivered prefix and one final evaluation.
There are six socket calls before cleanup, including the rejected call and clock
refresh. All timestamp differences use the matched runtime/caller clock domain.

| Observed interval | Duration |
|---|---:|
| Form result flush to expired caller main | 35691.644 ms |
| Rejected caller flush to new attempt main | 32354.942 ms |
| Confirmation-page result flush to next main | 16702.036 ms |
| First capture to final caller flush | 128967.289 ms |

The long outer boundary caused a real expired request and extra recovery work.
These timings retain that cost rather than reporting only the successful path.
They include assistant/tool/orchestration time, not separately measured model
thinking. This run does not demonstrate human tempo or a causal speedup.

## Retention failure and bounded fix

The v1 fixture wrote submission-attempts.jsonl beside the application output in
its temporary directory. Runtime cleanup copies only the final submitted.txt;
the auxiliary HTTP attempt log was deleted. Reading it after cleanup raised
FileNotFoundError. The audit explicitly records missing_http_attempt_archive=true.
Do not claim a retained independent HTTP attempt count or reconstruct missing
records from source code. The viewed confirmation page, runtime trace and final
submitted value/evaluation remain available.

confirmation_browser_entry_v2.py writes that log directly under the explicit
runtime output directory. confirmation_socket_entry_v2.py selects this fixture
for future runs; the measured v1 source is preserved. A separate HTTP-only probe
checks an unconfirmed request leaves no saved file, a confirmed request saves
the value, and both log entries survive deletion of the temporary application
directory. This does not retroactively recover the GUI run's log, and v2 has not
yet had a full GUI integration run. No change to runtime admission or scoring.

## Architecture implication

Keep terminal completion and task completion separate when the application may
ask for another visual decision. Finalizing at the first submit would close input
admission before this confirmation could be handled. The current experiment
deliberately deferred finalization because the fixture behavior was known; it
does not solve deciding when an unfamiliar application has truly finished.
Likewise, extending all leases would hide this failure without solving the outer
latency. Next test admission-preserving evaluation/continuation against a clearly
defined result contract before changing the public runtime protocol.

Evidence: audit_confirmation_self_use.py, results/confirmation-self-use-01,
probe_confirmation_archive.py and results/confirmation-archive-01. Model timestamps,
actual tokens/cost, held-out recovery and cross-domain generalization remain open.
