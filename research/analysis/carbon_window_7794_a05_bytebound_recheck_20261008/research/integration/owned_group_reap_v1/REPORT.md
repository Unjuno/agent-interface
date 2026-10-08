# Issue 3982: launcher exit, live descendants and unreaped zombies

**PASS_OWNED_GROUP_REAP_BOUNDARY_SCOPED.** Research evidence only; no production
runtime, public CLI, GUI input or application-effect claim.

## Result

One frozen allocation `owned-group-reap-3982-20260922-01` completed four
immutable six-case batches. All 24 first outcomes and actual outer/batch/case
exit receipts are retained. No formal case was retried, replaced or excluded.

| Policy | Normal controls (2) | Orphan cases (6) | Candidate observation |
|---|---|---|---|
| LEADER_ONLY | 2 absent | 6 live | Waiting for the launcher did not stop its helper. |
| GROUP_SIGNAL | 2 absent | 6 zombies | Group TERM/KILL stopped execution but did not reap the helper. |
| GROUP_REAP | 2 absent | 6 absent | Explicit adopted-child wait removed the remaining process identity. |

Orphan schedules were ordinary launcher exit, injected launcher SIGKILL after
a ready barrier, and ordinary launcher exit with a TERM-ignoring helper.
Each schedule had two fresh repetitions per policy. NORMAL_TREE required the
launcher to wait its normally exited helper before exiting itself. Every
sentinel in a different process group survived the candidate observation;
common rescue then removed all recorded supervisor/launcher/helper/sentinel
identities in all 24 cases. The two group policies escalated to SIGKILL in the
TERM-ignoring cases. Actual wait statuses, including signal exits, reconcile.
A zombie is not executing; it is unreaped lifecycle/accounting residue.

## H / T / D / C / U

**H.** Direct-launcher completion, cessation of descendant execution and full
reaping are distinct completion contracts. Group signalling and adopted-child
waiting should distinguish them for an explicitly enumerated local tree.

**T.** Three policies, four scenarios and two repetitions, in four immutable
batches with fixed forward/reverse arm order. All policies use the same Linux
subreaper setting. An independently executing observer records raw /proc stat
identity/state before the event, after candidate cleanup, and after rescue.
The supervisor is held at a barrier while the candidate snapshot is taken.
PID/start-ticks, parent, process group and session records bind observations;
actual waitpid/Popen results and raw response bytes are retained. Construction
has 12 separate excluded cases. The complete preformal plan is PLAN.md in the
verified archive; no scenario label is inferred from a desired outcome.

**D.** All 24 unique rows, source hashes, four prefix-bound batch receipts and
actual exits must reconcile. NORMAL_TREE must be empty for every policy; the
18 orphan cases must show six live / six zombie / six absent helpers for the
respective policies. Sentinel survival and final empty cleanup are mandatory.
A complete contrary pattern is FAIL; missing process/source/terminal evidence
is STOP/HOLD. The separate raw-only auditor reproduced the full pattern with
zero errors and rejected all 12 semantic/type/lineage corruption controls.

**C.** Adoption is not cancellation. The experiment keeps the supervisor alive,
uses one known helper that does not daemonize or change its group, and records
common rescue only after the candidate observation. Rescue cannot be used to
turn the baseline's residual into candidate success. This is not a duplicate
of #3961's independent-supervisor survival probe or #3644/#3657's live Calc
lifecycle allocation. No old image-cost experiment was rerun or completed.

**U.** No claim about supervisor death, unregistered/escaped descendants,
arbitrary forks, PID-reuse races, cgroup containment, uninterruptible kernel
sleep, power loss, physical input neutralization or semantic application
rollback. No model, task, latency, token, human-tempo or product improvement.
Two repetitions per cell provide finite scenario coverage, not population
reliability. The auditor is a separate implementation/process by the same
author, not an independent person or external review.

## Environment and units

Provided Linux 6.18.44 x86_64 execution container, glibc 2.41, CPython 3.13.5.
Docker CLI and pinned image identity were unavailable; this is not a Docker
Desktop/OrbStack replication. No package installation, network experiment,
credentials, model/provider, GUI or OS input. Signals affect only the newly
created private fixture processes; the unrelated sentinel tests that boundary.

CLOCK_MONOTONIC nanoseconds and /proc birth ticks are distinct units. The
100,000,000 ns TERM grace is 0.1 s; birth ticks use SC_CLK_TCK=100. The plan's
variable table specifies identity, state, status and time fields. Requested
100 ms grace, 18 s batch wait and 25 s tool envelope are operational targets,
not hard-real-time guarantees; no timing benchmark is claimed. Calibrated
combined uncertainty and a coverage factor are unavailable, not invented.

## Source-first evidence and retained setup failure

Before the first formal Python invocation, GitHub commit
`f1e2e23c8358f9d7c41fcef2ee71bb6f80511ebe` published FREEZE.json and its six
source/plan/environment digests. The exact bytes were read back. Issue #3982
comment 5766600099 records the freeze and construction result. Full executable
source bytes are delivered with this evidence archive, not claimed to have
been publicly uploaded before that hash commitment.

The first shell wrapper tried to redirect stdout into an absent formal/
directory and exited 1 before Python started. Inspection found no formal
directory, consumed marker or case. PRELAUNCH_STOP.json and comment 5766611171
preserve this failure. Only the wrapper log destination was corrected; frozen
sources, schedule and decision rules were unchanged. The four actual Python
batches then ran once each; all outer and child exits were observed as 0.
This is a retained prelaunch setup failure, not a scientific row or hidden retry.

- FREEZE SHA256: 279b4684c909f852e0175275d75ae918a0334f004f4179768ba57bf8b941cf65
- AUDIT SHA256: 9c608976cfba54b4caa8285b669f0a8086b2b28837ae97d5dc85f5cb06eb7b4a
- Construction audit SHA256: f21740c5bf779f3a94461210c6648bd2f20c45bcdddd4fc2704102dbf1c52436

AUDIT.json lists the exact SHA256 of every formal RAW.json. Source and raw
bytes were unchanged by auditing. An additional read-only check confirmed all
four outer stdout receipts match EXECUTION.json, stderr is empty and actual
outer exit files contain 0. Repository-wide tests were not run locally; PR
checks are a separate integration gate.

## Preserved predecessor STOP

The prior #1564/#2561 cost supplement stays
STOP_EXTERNAL_EXECUTION_ENVELOPE_PARTIAL_EVIDENCE / STOP_EVIDENCE_INTEGRITY:
155/168 pairs and 4,185/4,536 timing calls, missing launcher terminal status,
one invocation and zero retries. No missing cases were filled or pooled.
Its exact historical REPORT.md is included separately in this archive. The
complete unchanged 226-file ZIP remains a conversation artifact, SHA256
34f2999b4794f230e8f725eddcc3a712a855e6747afaafd652486ad21e12c6ac,
371,480 bytes. This PR does not claim to host that entire predecessor ZIP.
That limited historical transfer is explicit; all new #3982 evidence is included.

## Integration handoff and roadmap

The concrete #57/#2789 recovery question addressed is what a bounded mechanism
may truthfully report after its launcher ends. A parent exit alone is not an
empty-owned-tree receipt; an empty process group still does not prove physical
input release or application rollback. The measured candidate assumes a
surviving supervisor and enumerated non-daemonizing children. Do not promote
it into production without testing the actual runtime ownership boundary.

Completed: intake/collision review, successor #3982, excluded construction,
remote hash freeze, four first-outcome batches, independent raw audit and
corruption controls, retained setup incident and complete source/evidence
packaging. PR/main delivery and branch cleanup are recorded separately after
their actual completion. #2561/#3657/#2789 and the global ROADMAP remain open.

The smallest next integration question is whether the actual runtime can
provide separate receipts for child exit, owned-process absence, physical
input release and application-effect disposition when its supervisor dies.
No such experiment or guarantee is claimed here.

## Read-only reproduction

From this published directory, choose a new destination:

```sh
python -B unpack.py /tmp/issue3982-review
python -B /tmp/issue3982-review/audit.py /tmp/issue3982-review > /tmp/issue3982-review-audit.json
```

The unpacker verifies every fragment, archive and member hash, rejects unsafe
members and refuses an existing destination. It never starts an experiment.
The expected raw-only audit is exit 0, PASS_OWNED_GROUP_REAP_BOUNDARY_SCOPED,
24 rows and 12 rejected corruptions. Compare its output SHA256 to AUDIT.json.
Do not invoke the consumed formal batches in observe.py. Original runtime
paths in process records are historical provenance, not live endpoints.
