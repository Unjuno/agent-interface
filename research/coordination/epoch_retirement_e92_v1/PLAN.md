# Epoch retirement before exclusion GC — Issue #4344

Allocation `epoch-gc-e92-20260925-01`; intake main `9bc9343564a1522df2cf62f4c5cfcdb38194b7c4`.
Owned path `research/coordination/epoch_retirement_e92_v1/`; branch `research/epoch-gc-order-20260925-e92`.

## H / T / D / C / U

H: changing only the order of two committed maintenance operations can preserve old-request rejection across process exit. FENCE_FIRST installs the new current epoch before deleting old exclusions; DELETE_FIRST reverses them. Keeping obsolete exclusions temporarily is safe but does not complete reclamation. This is a known persistence-ordering principle, not a new database mechanism or alleged production defect.

T: six schedules BASELINE, FIRST_UNCOMMITTED, BETWEEN_COMMITS, SECOND_UNCOMMITTED, COMPLETE, FOREIGN_EXPECTATION; two policies; two fresh technical repetitions, 24 cases. Initial current epoch7; exclusions (7,A),(7,B),(7,C). Install epoch8, remove only epoch7 records. An abrupt owned-process os._exit(23) occurs at each declared cut, not a power interruption. Every case uses a separate maintenance process and a fresh reader against the same private database. Reader probes old-excluded(7,A), old-unseen(7,D), new(8,A), future(9,A) without making an application change. No in-flight body grants or transport are involved.

D: require all24 records,48 child exits,six completed supervised batches, full raw byte/state/SQL/process reconciliation, old-excluded eligibility DELETE_FIRST4 and FENCE_FIRST0, unchanged stable/complete/foreign controls, future rejection everywhere, new-epoch eligibility only after committed installation, and12/12 effective evidence-corruption rejections. A complete semantic contradiction is FAIL; incomplete evidence, unexpected exit/timeout/source mutation or ineffective control is HOLD/STOP. Never infer missing process status. Overall PASS requires both main audit and controls. Freeze precedes formal batch0; each schedule is one immutable four-case batch, once, in order0..5. Stop after unexpected batch failure; no rerun, replacement, exclusion or post-result tuning.

C: a trusted monotone installer, successful SQLite commits, no reset/rollback of epoch, one owner and quiescent maintenance are assumptions. An epoch switch also rejects previously unseen old-epoch work: deliberate retirement, not unlimited liveness. Obsolete rows left by interruption count as unreclaimed storage. Logical row deletion is not VACUUM or a measured filesystem saving. An atomic combined transaction is an alternative, not tested here. #4037 owns concurrent single-epoch prefix compaction; #4332/#4335 own per-payload receiver persistence. Their sources/results remain unchanged.

U: no concurrent admission, authentication, split brain, outstanding grants, distributed coordination, power loss, DB rollback/loss, repeated epoch installation, actual application effects, model/token/latency/energy benefit, natural failure probabilities or runtime promotion. Same-author separate code/process audit is not independent human review. No calibrated physical uncertainty or coverage factor is estimated.

## Variables and implementation assumptions

| Symbol / field | Meaning | Unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| E / current_epoch | currently installed namespace | 1 | single durable meta row | 7 initially,8 after installation; never reversed | integer scalar |
| H / excluded | retained request exclusions | 1 | SQLite rows keyed by(epoch,id) | initial three rows; removal restricted to epoch7 | finite set |
| e / request epoch | namespace named by a probe | 1 | first component of probe | 7,8,9; equality required | integer scalar |
| id | request identifier within namespace | 1 | second probe component | A or D; initial exclusions A/B/C | string |
| eligible | proposal-admission outcome only | 1 | current epoch and no exclusion | never action authority or task success | Boolean |
| policy | maintenance order | 1 | DELETE_FIRST or FENCE_FIRST | both use two transactions | enumeration |
| schedule | declared interruption point | 1 | six cases above | no natural race sampling | enumeration |
| repetition | independent technical replica | 1 | fresh DB/actors | 0 or1, not population sample | integer scalar |
| pid,exit | observed process identity and return status | 1 | Popen.pid and returncode | expected writer23 at cuts, otherwise0 | integer scalar |
| start_ns,end_ns | local process observation brackets | s, stored in ns | monotonic_ns readings | same host, diagnostic only | integer scalar |
| bytes | retained file length | B (8 bits) | length of exact DB/journal bytes | not reclaimed disk space | nonnegative integer |

Unit check: epoch/identity equality and record membership are dimensionless; this study makes no time-to-byte conversion. Clock differences would use 1 ns = 10^-9 s, but no timing endpoint is a promotion gate.

SQLite: DELETE journal, synchronous FULL, timeout0, explicit BEGIN IMMEDIATE/COMMIT. Connection reopening can roll back an unfinished transaction. Before-reopen DB and journal bytes are both saved; audits reconstruct them in fresh temporary copies, never modify original evidence. The supplied execution container has no Docker image attestation. Environment details are recorded, not inferred from earlier studies.

## Conditional proof from initial state to every cut

The target invariant is: the old excluded request(7,A) is never eligible after reopening.

Initially E is7 and(7,A) belongs to H, so the request is excluded. Before the first FENCE_FIRST commit, the only changed state is uncommitted; reopening restores E7 and the original H, so exclusion remains. After that first commit, E is8. Every epoch7 request now fails the equality check, whether H is present or absent. The second operation removes only old H rows and cannot change E. If interrupted before its commit, old rows remain; if committed, they disappear, but E stays8. Thus both possible persisted states after the first commit reject(7,A). The baseline and wrong-expected-epoch paths perform neither operation and preserve initial exclusion. These cases cover all scheduled cuts. If each future retirement uses the same fence-before-delete rule and fresh monotone epochs, the same argument applies inductively, provided epochs and retained fence storage are not rolled back. This is conditional on the stated storage and admission semantics, not a crash-proof hardware claim.

Counterexample: DELETE_FIRST commits deletion while E is still7. Exit between commits, or before the second commit, leaves E7 and no(7,A) row. The same reader therefore returns ELIGIBLE. A correct individual SQL transaction does not make an arbitrary two-transaction ordering safe.

Availability/storage tradeoff: after the candidate's first commit, new(8,A) is eligible even with all3 obsolete rows retained; old-unseen(7,D) is intentionally rejected. After complete maintenance, both arms reach E8,H empty. Identical final states do not imply identical intermediate restart behavior.

ERROR CHECK: the proof does not depend on callback timestamps, treats uncommitted writes through rollback, preserves the distinction between fence installation and completed deletion, and does not infer new authority from eligibility.

## Construction, evidence and roadmap

Separate excluded construction ran schedules0,2,4 (12 cases/24 children). Eight unit methods and12 effective controls passed. Construction outputs remain construction even where the unchanged auditor emits its scoped decision string. The preliminary supervisor lived one directory above the sources; the retained formal supervisor has the equivalent source-root resolution colocated with experiment.py. No construction row is pooled into formal.

Retain full stdout/stderr and argv/PID/exit brackets; JSON records embed exact initial, pre-reopen and post-reopen DB/journal bytes, lengths and hashes. Also retain all mutation inputs and outputs, construction and first formal outcomes. The complete archive stores actual recorded bytes; it does not regenerate outcomes. Publication uses readable source plus a lossless capsule and exact Git-object readback. Only after applicable exact-head CI and scoped review may the evidence PR merge. Global ROADMAP and #24/#544/#57 remain open in their wider scope.

Primary implementation background: https://www.sqlite.org/atomiccommit.html and https://www.sqlite.org/lang_transaction.html (accessed 2026-09-25). These explain storage semantics, not evidence of this experiment's results.
