# MAP01 live threat-guard evidence family

**Status: active research; eight allocation packet groups indexed through A15. Two result PRs remain open (#8759 A10 and #8800 A14); #8678/#8701 are closed after tracked-file preservation, and #8749/#8782/#8790/#8810 result packets are merged. #8818 is the merged A15 custody-manifest follow-up. Issue #59 remains open.**

Issue [#59](https://github.com/Unjuno/agent-interface/issues/59) asks whether
the current integrated real-time path can react usefully to a threat while a
model response is pending, survive bounded recovery, and reach an independently
checked MAP01 objective. A clean exit or a bounded, well-isolated failure can
change the next research direction. A live run that does not expose the relevant
threat/feedback condition remains HOLD. This family does not replace #59's
parent question or authorize another allocation.

The following are distinct preserved packets, not duplicates: they identify
different live attempts and cover conditions. This table is a historical snapshot
checked against GitHub on 2026-10-18 at 14:38 UTC, current main
`c72c9b186dac29c57ed0d63d92748bfc7ba4d971`. At that snapshot each PR was open
and had no GitHub assignee. That did not prove author release. The `ahead/behind`
values compare each exact head with that historical main and do not establish
mergeability or evidence validity. Later 2026-10-19 custody/integration updates
supersede this table's workflow statuses; the table remains an immutable record
of its 2026-10-18 snapshot.

| PR | Packet and retained result | Draft | Exact head | Base at PR | Current-main comparison | Disposition |
|---|---|---:|---|---|---|---|
| [#8678](https://github.com/Unjuno/agent-interface/pull/8678) | A01 prelaunch STOP plus A02: four low-effort turns, health 97→91→85, authored hard floor not crossed; cleanup stopped on an active-input-lease `ValueError`. A later audit reproduced the committed audit. | yes | `7551424026375469f609754140250f89bf09cad4` | `1ece47014d05db898bf73afcd722a14524462e15` | diverged; +1 / −478 | Preserve. Audit the frozen source and whether the lease-cleanup finding was resolved downstream; do not repeat A02. |
| [#8701](https://github.com/Unjuno/agent-interface/pull/8701) | A03–A07: ten turns, alive but unfinished, zero kills and no exit; no hard-health guard/useful scorer condition occurred. Initial audit FAIL retained; additive reconciliation and later audit corrections are part of the packet. | no | `44f15471bd07705f1bbe565c017b6f9df29e87ec` | `1ece47014d05db898bf73afcd722a14524462e15` | diverged; +19 / −478 | Preserve. Read the latest audit counterexamples and corrections before any integration decision; do not rerun these attempts. |
| [#8749](https://github.com/Unjuno/agent-interface/pull/8749) | A09: ten decisions; typed health crossed 100→88 while inference was pending, cancel discarded the stale answer, and a newer observation was used. Two kills, no death/exit. Original frozen auditor FAIL remains; a later review found a reconciliation defect. | yes | `3e170476db3cc8e2798f33884925f33845b398c3` | `1ece47014d05db898bf73afcd722a14524462e15` | diverged; +4 / −478 | Preserve. Audit the latest reconciliation finding and independently inspect the packet; do not infer an adoption-ready pass. |
| [#8759](https://github.com/Unjuno/agent-interface/pull/8759) | A10: stopped at death after 13 turns, one kill, no exit; preregistered live threat-guard condition was not exposed. STOP; body says not to retry. | yes | `d31c85116df463039219368c2b64e986f9d9dd55` | `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36` | diverged; +3 / −857 | Preserve STOP and original-audit FAIL. Public aggregate says 13/13 cancellations accounted after reconciliation, but exact freeze/raw/first audit remain local and are absent from PR/current checkout; #8763's later repair does not change A10's result. Keep draft/unmerged pending owner-attested custody; no retry. |
| [#8782](https://github.com/Unjuno/agent-interface/pull/8782) | A11: 32 turns, alive, two kills, health 64–100, ammo 32–52; joint hard-health/useful-feedback/recovery condition not exposed. HOLD, no exit. | no | `9efecd6d5bb46d924ccdf79df53e6e8ed3727553` | `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36` | diverged; +2 / −857 | Preserve HOLD and sanitized evidence. Audit source closure and latest custody; no efficacy inference. |
| [#8790](https://github.com/Unjuno/agent-interface/pull/8790) | A12 startup STOP plus A13: ten turns; a 1.008 s hold did not overlap the sole useful scorer event, which came 49.277 ms after the controller interval. Timing gate HOLD; one recovery was right-censored at the cap. | no | `db6ca09d10abaf3d0e8aaf5ad3f3f9f67555b763` | `a6343bb76e4dc0a4afa32a29c8a485a617faeff8` | diverged; +5 / −855 | Preserve timing HOLD/censoring. Public summary lacks hash-bound full raw/treatment-audit receipt; see the 2026-10-19 recheck. Keep unmerged pending owner-attested custody; do not rerun or reinterpret the delayed event. |

## Separate source-level pending-ammo packet — PR #8854 (merged 2026-10-19)

PR [#8854](https://github.com/Unjuno/agent-interface/pull/8854) was merged at
`d25b497cc8a05d45158a81c038ee15e03aabdddc`. Its packet is kept separate from
the six live threat-guard allocation packet groups in the historical table above: on frozen source from
`f185a9059d485a4f8d5a65e9e7f6782897f67eae`, a synthetic soft-ammo change
6→4 queued a soft event without cancelling a pending turn, while ammo 0
triggered the hard-floor cancellation path. A follow-up composition probe
showed the authored cover schema/loop can allow repeated fire pulses below the
immediate-action floor; it does not show a live model authored that cover or
that the behavior harmed a task.

The exact packet SHA-256 manifest matched 17/17 files. Local Windows Python
3.11.9 checks passed 8/8 in normal mode, 8/8 under `-O`, and 34/34 in the
independent audit; GitHub `replay-gate` passed. This is source-level synthetic
evidence only: no live game, model, OS input, physical release, task effect,
or MAP01 outcome. #59 remains open, and this packet does not consume or release
any live allocation.

## Separate stale-action revalidation packet — PR #8853 (merged 2026-10-19)

PR [#8853](https://github.com/Unjuno/agent-interface/pull/8853) was merged
at `91d8859530e9c65e7f24fb4843d4cbeef3a9ece6`. Its saved one-run WSLc A14
construction packet uses a deterministic fake client: after the pending
planner turn receives a newer ammo observation (6→4), fresh action admission
rejects the minimum-ammo-5 response; with ammo unchanged, the response reaches
executor-ready only, without input authority. We independently confirmed this
packet is not present in the unrelated, conflicted large PR #8842.

No WSLc run was repeated. The retained source test passed 2/2 in normal and
optimized Python, its independent audit passed, all 22 manifest checksums
matched, and the exact-head GitHub replay-gate passed. This validates only the
synthetic stale-action predicate, not model behavior, game progress, OS input,
physical release, useful task effect, recovery, or MAP01 completion. #59 remains
open; this packet neither consumes nor releases a live allocation.

## What this organization establishes

The six PRs in the historical table cover unique packet directories and
distinct attempt identifiers; later A14/#8800 and A15/#8810 add two more
allocation groups, with #8818 as A15's custody-only follow-up. Open-set
metadata alone does not prove two packets duplicate one another.
Several packets share auditor/reconciliation code and every head predates the
current main by hundreds of commits. The bodies/comments also retain failed
audits and correction findings. Therefore, an automatic merge, close, rebase,
or branch deletion would risk dropping unique evidence or hiding unresolved
audit work. Later packet-specific integrations preserve each result boundary
below. An empty reviewer/assignee field or an old update time is not treated as
owner release.

## Finite, parallel read-only work

Workers may independently inspect one packet group below. Each report should
cite exact source/result/raw hashes, the latest audit finding and correction,
current-main source drift, and a disposition recommendation. It must not rerun
the live allocation, rewrite its raw, or edit the shared agenda. The family
integrator compares the reports, checks whether the packet is already preserved
on main, and then updates this index and Issue #59 with any verified disposition.

| Work key | Scope | Output boundary |
|---|---|---|
| `map01-a01-a02` | PR #8678 A01/A02; source, host/image custody, active-lease cleanup stop, audit reproducibility | New packet audit note under a distinct `research/audit/` path |
| `map01-a03-a07` | PR #8701; original FAIL plus reconciliation chain and latest counterexamples | Same; retain original and corrective audit outcomes separately |
| `map01-a09` | PR #8749; health-floor crossing, stale-answer rejection, reconciliation review finding | Same; verify the latest reviewed head, not just the initial result |
| `map01-a10` | PR #8759; STOP before target gate, no retry | Same; custody and source-dependency inspection only |
| `map01-a11` | PR #8782; sanitized HOLD packet and custody state | Same; distinguish a live episode from exposure of the joint gate |
| `map01-a12-a13` | PR #8790; startup STOP, delay timing HOLD, right-censored recovery | Same; keep timing and recovery censoring separate |

These are work suggestions, not assignments, locks, new resource allocations, or
merge approval. If a group has an active owner or a newer head, coordinate with
that owner and inspect the live state before proceeding. Only the integrator
edits this shared family index, `docs/ideas/README.md`, and the parent agenda.

## Read-only packet recheck — PR #8790 (pre-integration snapshot, 2026-10-19)

The live PR remains open at head `db6ca09d10abaf3d0e8aaf5ad3f3f9f67555b763`
against base `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`. Its published result
retains A12 as a startup STOP and A13 as a timing HOLD: the useful scorer event
occurred 49.277 ms after the controller interval, while the 1.008 s relay hold
did not make that event controller-visible. One recovery is right-censored at
the ten-decision cap. Preserve the HOLD and censoring; do not call this a causal
latency result or task success.

The review thread's final correction resolves the `key_state_errors` predicate
concern for source-conforming V12 receipts: V12 sets `verified=false` when that
field is nonempty, so synthetic malformed-receipt acceptance is not evidence
that any retained A13 cancellation was misclassified. It still does not
reconstruct the allocation's actual rows. `A13_RESULT.md` says the full
`results-local/doom/map01-v39-live-threat-guard-a13-delay-a01-20261009/`
package, including `A13_TREATMENT_AUDIT.json`, remains local; the public PR
contains a summary JSON with `independent_audit_pass: true` but no hash-bound
full raw or treatment-audit receipt. The exact allocation path was absent from
this checkout during the recheck, so local raw custody and reproducibility
remain unverified; this is not evidence of global loss.

At the time of this recheck, disposition was to keep #8790 open pending an
owner-attested retained raw/treatment-audit packet or equivalent hash-bound
custody evidence. Do not rerun A12 or A13. This read-only recheck did not
change the then-current Issue state, allocation, or result classification.

### Later integration status

PR #8790 was subsequently merged at `20a17d8b99879f7804a679d2dc2927d5e6b4cb3a`.
Its 23 A12/A13 tracked files were matched to the main blobs. That integration
preserved the sanitized public result and its HOLD/censoring; it did not supply
the local full raw requests/responses or treatment-audit file, so those remain
unverified from this checkout. The merge does not upgrade the result or
authorize a rerun.

## Read-only packet recheck — PR #8759 (2026-10-19)

The live PR remains a draft at head `d31c85116df463039219368c2b64e986f9d9dd55`
against base `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. Public A10 records a
62.396 s episode ending in one death, one kill and no map exit; the hard-health
gate and useful scorer-during-inference condition were both unexposed. The
original audit is `FAIL`; public reconciliation reports 13/13 cancellations
accounted (3 active leases with token-matched releases and 10 no-input cases
with verified-empty terminal receipts). Keep the original FAIL and derived STOP
separate. Merged [#8763](https://github.com/Unjuno/agent-interface/pull/8763)
repairs the broad controller cleanup receipt but does not rewrite this run.

The PR explicitly says the exact execution freeze, first audit, raw output and
manifest remain local. Its public freeze/result are sanitized projections, and
the exact `results-local/doom/map01-v39-live-threat-guard-a10-20261009/` path
was absent from this checkout. Thus the public summary is not independently
reproducible from this packet. This bounded absence does not show global raw
loss. Keep #8759 draft/unmerged pending owner-attested raw/freeze/audit custody;
do not rerun the consumed A10 allocation.

## Current-main evidence-custody recheck — A01/A02 (#8678), 2026-10-19

At main `a6741224fad3cfd29de7bd4becac9cc207490242`, all 29 tracked files on #8678 head `7551424026375469f609754140250f89bf09cad4` remain unique to that PR. Its frozen source commit is reachable from main. A01 is a prelaunch STOP; A02 is a retained runtime failure with a failed cleanup terminal, despite empty keymap snapshots. Hard-health guard exposure and task success remain untested. The PR's 976-entry manifest points to an ignored `results-local/...` bundle not found in the current checkout or any of 15 registered worktree roots; only Git-tracked custody can be completed from this host state.

Evidence-only PR [#9146](https://github.com/Unjuno/agent-interface/pull/9146) merged the complete 29-file Git-tracked A01/A02 diff from #8678 byte-for-byte. Main readback verified all 29 blobs against #8678 head `7551424026375469f609754140250f89bf09cad4`; #8678 was then closed and its remote branch deleted after author, dependent-PR, and worktree checks. The 976-entry ignored raw-output bundle remains unlocated on this host, so complete raw-image custody is still unknown and is not claimed. This closes only the tracked PR-diff loop.

#8701's A03–A07 files are a distinct later allocation series, not duplicate evidence: its 41 research paths do not overlap A01/A02, and it also changes `CURRENT_GOAL.md`. Keep those attempts separate, leave Issue #59 open; its bounded outcome/custody update is [comment #6259320132](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6259320132). Do not rerun any consumed allocation. A02 remains a retained runtime failure with incomplete cleanup; no physical release, hard-guard response, bounded recovery, or task success is established. See the [custody review](../maintenance/pr8678-evidence-custody-20261019.md).

## A03–A07 tracked custody completion — 2026-10-19

Evidence-only PR [#9148](https://github.com/Unjuno/agent-interface/pull/9148) merged the 41 A03–A07 research files from #8701 byte-for-byte. Main readback matched all 41 blobs to exact head `44f15471bd07705f1bbe565c017b6f9df29e87ec`; #8701 was then closed and its remote branch deleted after author, dependent-PR, and worktree checks. A03–A06 remain setup STOPs. A07 remains overall HOLD: ten turns, no hard guard/useful scorer exposure, and no MAP01 completion. The separate `PASS_CUSTODY_RECONCILED_SCOPED` result has `formal_pass=false` and does not prove physical input or game effect. The PR body reports a 2,358-entry ignored raw bundle, but that directory was not found in the current checkout or 15 registered worktree roots; its external custody is unknown and is not claimed by the tracked transfer. The separate A09 `CURRENT_GOAL.md` hunk maps to #8749's existing family entry; #8749 had already merged at `2bdb16d38f84ff58602eb777b34d7f02c77373a8` on 2026-10-18. Its A09 packet remains distinct. See the [custody review](../maintenance/pr8701-evidence-custody-20261019.md). No consumed allocation was rerun; Issue #59 remains open, with the scoped update in [comment #6259414298](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6259414298).

## A11 sanitized evidence packet integrated — 2026-10-19

PR [#8782](https://github.com/Unjuno/agent-interface/pull/8782) merged at `65f3dd3f7aea88af7c249d58f430e72e83a3c92e`, adding its 20-file sanitized public packet. A11 remains allocation-scoped **HOLD** and the original frozen audit remains **FAIL**: 32 turns, two kills, no deaths, no MAP01 exit, and no observed joint hard-health/useful-feedback/recovery gate. Additive reconciliation accounts for all 32 cancellations (six active-input leases with matching token-bound owner releases and 26 no-input cancellations with verified-empty terminal receipts). The packet intentionally omits raw transient intent tokens and per-key identities; the exact freeze/raw output remain local and were not independently re-read here. Its post-run public runner/auditor are publication copies, not the executed copies. No game/model/allocation was rerun. The repository's original replay-gate passed; on this Windows checkout, 16 portable tests passed and the one POSIX fixture-path assertion did not apply because this checkout is not mounted at the experiment's dedicated `/mnt/source/results-local/doom/a11-source` path. This local limitation is not reported as a packet pass or as a new experiment result.

## A13 delay-result packet integrated — 2026-10-19

PR [#8790](https://github.com/Unjuno/agent-interface/pull/8790) merged at `20a17d8b99879f7804a679d2dc2927d5e6b4cb3a`. Its 23 A12/A13 files were byte-matched from the PR head to main. A12 is a prelaunch startup STOP and was not retried. A13 remains **HOLD** for its timing gate: the tenth completion was delayed 1.008 seconds without reissuing the model request, and the only useful scorer event arrived 49.277 ms after the controller interval ended. Two hard-health guards occurred; one recovered within two decisions, while the final-turn guard is right-censored by the decision cap. The episode ended with one kill, no death and no MAP01 exit. The independent packet reports 11/11 matched cancellations accounted and 35/35 per-key release transitions matched to owner-thread key-up receipts. The original audit result remains retained; this does not demonstrate inference-latency improvement or causal task benefit.

The public result is an aggregate summary. Full raw requests/responses and images remain local and were not re-read during integration. The PR's replay-gate passed. In this Windows checkout, 26 of 27 unit tests passed; the remaining exact guest-mount-path test is tied to the original POSIX `/mnt/source/results-local/doom/a13-source` fixture and could not be satisfied here. The allocation was not rerun.

## A14 recovery follow-up and A15 custody repair — current disposition

Open PR [#8800](https://github.com/Unjuno/agent-interface/pull/8800) retains A14's 12-decision live result: no preregistered hard-health guard occurred, no useful scorer event fell inside a model interval, and MAP01 did not exit. The original audit remains **FAIL** and the allocation remains **HOLD**. Its additional post-hoc reconciliation reads a local-only `episode/report.json`, which is absent from the public packet; keep #8800 open pending raw-backed verification and do not rerun A14. This absence is scoped to the available checkout, not a claim of global raw loss.

Merged PR [#8810](https://github.com/Unjuno/agent-interface/pull/8810) retains A15's public HOLD and original audit FAIL. Its merged custody follow-up [#8818](https://github.com/Unjuno/agent-interface/pull/8818) adds a 3,859-entry path/size/hash manifest and hash-bound author-side readback, but does not copy raw prompt, image, or protocol contents to main. The manifest and public-summary digest were independently checked; the full raw-custody pass was not reproduced here. Preserve that limit and do not rerun A15.

## Current packet disposition — 2026-10-19

Eight indexed allocation packet groups now have distinct workflow states: A01/A02 (#8678) and A03–A07 (#8701) have their tracked files preserved and original PRs closed; A09 (#8749), A11 (#8782), A13 (#8790), and A15 (#8810) are merged. A15's #8818 follow-up adds its custody manifest and hash-bound author-side readback, but raw prompt/image/protocol contents are not in main and the local raw-custody pass was not independently reproduced here. A10 (#8759) remains draft because its exact raw/freeze/first-audit custody is absent from the public packet. A14 (#8800) remains open because its post-hoc reconciliation depends on a local `episode/report.json` that is not included in the public packet; its original audit remains FAIL and its live result remains HOLD. These are PR states, not completion of Issue #59. No allocation was rerun during these custody and indexing updates.
