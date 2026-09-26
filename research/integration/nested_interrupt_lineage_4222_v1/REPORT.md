# #4302 — nested interrupt completion lineage

**PASS_NESTED_INTERRUPT_LINEAGE_SCOPED**

The public source freeze `6a1f9d5c2001f5f322b6665f164d2a23551fa67b` preceded all formal input. Allocation `nested-lineage-4302-20260924-n7c2` completed 24/24 fresh private Tk/Xvfb sessions in two immutable12-case batches. Batch invocations/reruns/replacements/exclusions/post-result tuning: **2/0/0/0/0**. Actual launcher exits0/0; frozen audit and controls exits0/0.

## First outcomes

| Schedule | COUNT_ONLY_POP (2 sessions) | LINEAGE_BOUND_POP (2 sessions) |
|---|---|---|
| NORMAL | root ab,2/2 | root ab,2/2 |
| DUPLICATE_CHILD | suffix b reaches still-live parent,2/2 | duplicate ignored; root ab,2/2 |
| OLD_GENERATION_CHILD | suffix b reaches still-live parent,2/2 | old C1 rejected against C2; root ab,2/2 |
| FOREIGN_SESSION | suffix b reaches still-live parent,2/2 | foreign receipt rejected; root ab,2/2 |
| WRONG_PARENT | suffix b reaches still-live parent,2/2 | parent mismatch rejected; root ab,2/2 |
| MISSING_CHILD | no suffix, unresolved,2/2 | no suffix, unresolved,2/2 |

Candidate: **10/10 recoverable completions,2/2 intentional unresolved stops,0 premature/wrong-surface suffixes**. Weak comparator: **8/8 directed wrong-surface suffixes**. Its root remains a in those cases; the retained parent Entry contains b. Missing-child refusal is not counted as successful task completion, even though the fixture eventually closes its windows.

All24 final X-server keymaps/buttons are neutral; all24 app and Xvfb exits are0; owned sockets/locks removed. Every process stderr is empty. App-owned KeyPress/KeyRelease/value/close journals independently locate the actual suffix effect before or after parent close. No direct Entry insertion or scorer-controlled input occurs.

Frozen raw-only audit: **970 checks, errors=[], integrity_errors=[]**. Effective corruption controls: **12/12 rejected** (missing/duplicate case, wrong effect, held key, missing process exit, authority escalation, wrong acceptance, foreign identity, Boolean generation, missing release, wrong input destination, missing notification). These mutate parsed evidence independently of outer file hashes. Eight I/O-free policy unit tests also pass. The separate auditor was authored in this same session; this is not an independent human/agent review or authentication of cooperative receipts.

## H/T/D/C/U and interpretation

**H:** matching each completion to the current top frame's exact session, interrupt ID, generation and parent prevents another frame from consuming that completion.

**T:** actual two-level Tk Toplevel lifecycle and XTEST prefix/suffix input, six directed notification schedules, two policies and two fresh repetitions. Same root continuation and task dependencies. Policy sees only saved frames and delivered receipts; the independent application journal is not candidate input. Supervisor authorization covers only this disposable fixture; authority=false is not a claim that no experimental input occurred.

**D:** all frozen gates pass. A counter/pop that ignores completion identity is rejected for this nested contract. Exact lineage matching is retained as a necessary bounded correlation mechanism; it is not by itself a complete recovery policy.

**C:** the weak policy is deliberately incomplete, not alleged deployed behavior. Receipts/identity fields are cooperative rather than authenticated. Directed delays/corruptions are not natural incidence samples. The two repeats establish exact finite fixture behavior, not population reliability. Current root target/queue/source/result state is held fixed; missing notifications sacrifice liveness rather than imply completion.

**U:** arbitrary-depth stacks, crash/reconnect, real OS dialogs, malicious receipts, out-of-order valid completions, transport replay across a new root task, focus check/use atomicity, changing root semantics, model usefulness, tokens, latency, other platforms and production integration remain untested.

## Integration handoff

For #2869/#2789 recovery, completion of child C must never stand in for completion of parent P. The reusable pure function is `policy.Continuation.deliver`; its output is eligibility only. Pair it with #4222's current task liveness, pending-result, freshness, queue and target revalidation before any real continuation is admitted. Do not turn a stack pop into authority, or missing completion into automatic retry. This study closes the nested-completion correlation question only; it does not run that full composition or the #57 same-model integrated-efficiency comparison.

## Preservation and execution boundary

#4222/PR #4278 and all older evidence are untouched. Excluded construction retained in CONSTRUCTION.md and the lossless archive: initial metadata/flag failures before any app, a controls-CLI argument failure, attempt02 before auditor hardening, final attempt03 and unit tests. None is pooled into formal24. Public Git blob readback matched all10 preformal files. No source or decision-gate changes occurred after formal input.

Source files are directly readable in this additive directory. The evidence capsule retains all exact raw journals, rows, batch records, source copies, construction artifacts and launcher/audit/control outputs. `verify_publication.py` restores to a new temporary directory and reruns only read-only auditing, controls and unit tests; it never invokes the GUI runner.

Scientific work has stopped at the declared allocation boundary. Publication, review/CI, main readback and dependency-safe owned-branch cleanup are separate delivery steps. Global ROADMAP/#57/#2789 remain open. No process continues in the background.
