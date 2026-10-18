# MAP01 live threat-guard evidence family

**Status: active research; six open PR packets indexed, none disposed by this note.**

Issue [#59](https://github.com/Unjuno/agent-interface/issues/59) asks whether
the current integrated real-time path can react usefully to a threat while a
model response is pending, survive bounded recovery, and reach an independently
checked MAP01 objective. A clean exit or a bounded, well-isolated failure can
change the next research direction. A live run that does not expose the relevant
threat/feedback condition remains HOLD. This family does not replace #59's
parent question or authorize another allocation.

The following are distinct preserved packets, not duplicates: they identify
different live attempts and cover conditions. The table was checked against
GitHub on 2026-10-18 at 14:38 UTC, current main
`c72c9b186dac29c57ed0d63d92748bfc7ba4d971`. Each PR remains open and has no
GitHub assignee. That does not prove the author released the work. The
`ahead/behind` values compare each exact head with that main; they are
diagnostic only and do not establish mergeability or evidence validity.

| PR | Packet and retained result | Draft | Exact head | Base at PR | Current-main comparison | Disposition |
|---|---|---:|---|---|---|---|
| [#8678](https://github.com/Unjuno/agent-interface/pull/8678) | A01 prelaunch STOP plus A02: four low-effort turns, health 97→91→85, authored hard floor not crossed; cleanup stopped on an active-input-lease `ValueError`. A later audit reproduced the committed audit. | yes | `7551424026375469f609754140250f89bf09cad4` | `1ece47014d05db898bf73afcd722a14524462e15` | diverged; +1 / −478 | Preserve. Audit the frozen source and whether the lease-cleanup finding was resolved downstream; do not repeat A02. |
| [#8701](https://github.com/Unjuno/agent-interface/pull/8701) | A03–A07: ten turns, alive but unfinished, zero kills and no exit; no hard-health guard/useful scorer condition occurred. Initial audit FAIL retained; additive reconciliation and later audit corrections are part of the packet. | no | `44f15471bd07705f1bbe565c017b6f9df29e87ec` | `1ece47014d05db898bf73afcd722a14524462e15` | diverged; +19 / −478 | Preserve. Read the latest audit counterexamples and corrections before any integration decision; do not rerun these attempts. |
| [#8749](https://github.com/Unjuno/agent-interface/pull/8749) | A09: ten decisions; typed health crossed 100→88 while inference was pending, cancel discarded the stale answer, and a newer observation was used. Two kills, no death/exit. Original frozen auditor FAIL remains; a later review found a reconciliation defect. | yes | `3e170476db3cc8e2798f33884925f33845b398c3` | `1ece47014d05db898bf73afcd722a14524462e15` | diverged; +4 / −478 | Preserve. Audit the latest reconciliation finding and independently inspect the packet; do not infer an adoption-ready pass. |
| [#8759](https://github.com/Unjuno/agent-interface/pull/8759) | A10: stopped at death after 13 turns, one kill, no exit; preregistered live threat-guard condition was not exposed. STOP; body says not to retry. | yes | `d31c85116df463039219368c2b64e986f9d9dd55` | `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36` | diverged; +3 / −857 | Preserve STOP and original-audit FAIL. Public aggregate says 13/13 cancellations accounted after reconciliation, but exact freeze/raw/first audit remain local and are absent from PR/current checkout; #8763's later repair does not change A10's result. Keep draft/unmerged pending owner-attested custody; no retry. |
| [#8782](https://github.com/Unjuno/agent-interface/pull/8782) | A11: 32 turns, alive, two kills, health 64–100, ammo 32–52; joint hard-health/useful-feedback/recovery condition not exposed. HOLD, no exit. | no | `9efecd6d5bb46d924ccdf79df53e6e8ed3727553` | `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36` | diverged; +2 / −857 | Preserve HOLD and sanitized evidence. Audit source closure and latest custody; no efficacy inference. |
| [#8790](https://github.com/Unjuno/agent-interface/pull/8790) | A12 startup STOP plus A13: ten turns; a 1.008 s hold did not overlap the sole useful scorer event, which came 49.277 ms after the controller interval. Timing gate HOLD; one recovery was right-censored at the cap. | no | `db6ca09d10abaf3d0e8aaf5ad3f3f9f67555b763` | `a6343bb76e4dc0a4afa32a29c8a485a617faeff8` | diverged; +5 / −855 | Preserve timing HOLD/censoring. Public summary lacks hash-bound full raw/treatment-audit receipt; see the 2026-10-19 recheck. Keep unmerged pending owner-attested custody; do not rerun or reinterpret the delayed event. |

## What this organization establishes

The six PRs cover unique packet directories and distinct attempt identifiers;
the open-set metadata alone does not prove two packets duplicate one another.
Several packets share auditor/reconciliation code and every head predates the
current main by hundreds of commits. The bodies/comments also retain failed
audits and correction findings. Therefore, an automatic merge, close, rebase,
or branch deletion would risk dropping unique evidence or hiding unresolved
audit work. None is performed here. An empty reviewer/assignee field or an old
update time is not treated as owner release.

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

## Read-only packet recheck — PR #8790 (2026-10-19)

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

Disposition: keep #8790 open and unmerged pending an owner-attested retained
raw/treatment-audit packet or equivalent hash-bound custody evidence. Do not
rerun A12 or A13. This read-only recheck changes no Issue state, allocation, or
result classification.

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
