# Notification predicate holds the shared Condition

Decision: PASS_SCOPED_PREDICATE_CONDITION_BOUNDARY for #17 claim5967858817 / freeze5968039811. One new ordinary native Linux-pipe construction, four first cells, producer and saved-data auditor each1/1 exit0, no replay or retries.

The exact current research client lets an arbitrary notification predicate hold its shared Condition. The reader can record a healthy response before the request deadline while being unable to publish that response; the already-waiting request also cannot reacquire the Condition when its deadline expires. Moving predicate and truth conversion outside the Condition removes this cross-caller blockage in this pure directed fixture. The comparator is not a production repair.

| Cell | Exact request return (ms) | Predicate duration (ms) | Request pending at held checkpoint |
|---|---:|---:|---|
| baseline-healthy | 3.979644 | 0.009041 | None |
| candidate-healthy | 5.970528 | 0.013458 | None |
| baseline-held | 404.478981 | 401.446217 | True |
| candidate-held | 2.145927 | 402.021344 | False |

The held original checkpoint was250.571ms after predicate entry and202.7ms beyond the actual internal request deadline. The response had already reached the unchanged journal, but the reader was at shared Condition publication and the caller at Condition.wait reacquisition. It returned the exact queued response404.479ms after request start once the owner released the callback. This is the observed queued-response race outcome; the frozen checker also permits an original post-release TimeoutError.

The held comparator returned the exact acknowledgement2.146ms after request start; at its250ms checkpoint notification and callback were still pending and the release event unset. Both held notification calls ultimately took about402ms despite their nominal50ms timeout. No callback or notification hard deadline follows. Healthy requests returned exact in3.980/5.971ms; n=1 per arm/condition does not establish throughput, a latency distribution or superiority when healthy.

Comparator membership/lost-wake controls are separate in-memory construction: identity recheck rejects a consumed selection even when an equal-by-value distinct object remains, and queue-change recheck rescans an arrival during false evaluation. Both predicate invocation and truth conversion are outside the Condition. Callback ordering/fairness/reentrant mutation are not preserved in general. Seven memory controls and eight parser refusals passed under Homebrew3.14.5. The native four do not execute those race schedules.

The independent checker was frozen before collection and ran once under the pinned native Linux CPython3.12.15 image. It reads records and source bytes only. Ten actual copied-data controls reject pending candidate, acknowledgement after checkpoint, non-overdue original deadline, wrong reader frame, already-set release, late response record, Boolean ID, unclosed pipe/journal and nonzero first exit. Their stdout/receipt/collection joins were rebuilt, so these refusals do not rest solely on stale outer hashes. Full actually checked copies are in copied-controls-data.tar.gz with a370-file inventory; no client/peer rerun. Saved-record consistency is not authenticity or complete adversarial resistance.

Custody: prospective source2b45ed7/tree75ed84fa and FREEZE SHA c79dded9 bind30 inputs/133866B. Guest source readback proves exact30 original inputs plus freeze before collector launch. All Python is archived as .py.txt, byte-identical; original execution names in freeze map to that suffix. Selected native image/kernel/Python/threading/subprocess, actual cpu100000/100000, memory268435456, pids64 and matching CLOCK_MONOTONIC clocks are retained. This is not full transitive/kernel closure. Native output export92160B SHA f9a9dcd6… unpacked exact53170B. No models/network/GUI/input.

All4 peer processes exit0, all reader/caller threads retire, journals close; the driver separately closes the three handles and obtains EBADF for12 FDs. Library close leaves those wrappers open; driver cleanup is not a source repair or physical release. All three environment/collector/auditor containers are terminal exit0/non-OOM and retained. The identified own guest is stopped; other guests are untouched.

First resource '--' argv error and first publication full-index write-tree lazy fetch/SIGTERM/earlyEOF/refspec failure are retained. Publication v2 uses missing-ok metadata and does not replay science. No source imports/default discovery/workflow/global index/catalogue changes; one additive navigation bullet only.

Current original source at e54128b and fresh e685a79b applicability has the same6194B SHA6032c0dd. Known production caller predicates are pure field comparisons. This constructed arbitrary callback establishes no observed production lag, physical cancel/release reachability, useful task feedback, Codex/provider/model/game result, cross-platform guarantee, #17 promotion/#59 completion or main integration. No vote/apply identity/main send exists.

For review, copy archived checker and five source text files to a fresh scratch directory with their original .py names. Execute only the saved checker against raw/ with --source-root that directory. The checker never imports the other source files. Source/producer/native/allocation replay is outside this review. The data-only copied-control script may be examined as text; all first checker receipts are retained.
