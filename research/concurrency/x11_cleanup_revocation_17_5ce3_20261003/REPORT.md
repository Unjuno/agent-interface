# Cleanup-only composition fails queued-input revocation

Issue [#7010](https://github.com/Unjuno/agent-interface/issues/7010), bounded
successor to closed #6999 under #17/#57. Result:
`FAIL_CLEANUP_ONLY_COMPOSITION_LATE_INPUT_SCOPED`. The minimal research-only
before-positive-key-state gate is supported for this exact finite exposure.
No production source was modified or adopted, and no public cancel API bug is
claimed. The full roadmap remains open.

| Arm | Cells | At +150ms | F9 after revocation | Public result |
| --- | ---: | --- | ---: | --- |
| Healthy cleanup-only | 3 | neutral, program complete | no revocation | completed |
| Healthy reference gate | 3 | neutral, program complete | no revocation | completed |
| Blocked cleanup-only | 3 | neutral, PNG/program pending | 3/3 | completed |
| Blocked reference gate | 3 | neutral, PNG/program pending | 0/3 | execution_failed at op3 |

All six fault cells independently confirmed initial F8 release in2.397–2.885ms.
Nevertheless, the cleanup-only program emitted the queued F9 after persistence
resumed; owned-window press receipts were405.200/409.982/411.614ms after the
declared revocation. Independent logical F9 readback had11/13/13 samples in those
three cells. The reference refused its F9 call before native emission, retaining
completed prefix[0,1,2] and verified release. All six healthy controls admitted
both keys and completed the exact four press/release events, so the reference
does not simply disable F9. All12 terminal whole-keymaps/buttons were neutral.

The one formal candidate collected12fresh cells,1,183 independent query samples
and42 app key events in4.43s. One separate saved-only formal auditor exited0
with the scientificFAIL above; reruns0. Scientificnegative outcome and execution
success are distinct. Original raw SHA256
`b42229da97099f37b23041e31d0bd4cea5473e94261ea678c2f606f89040bd0a`.
All12 PNGs, source stacks, query brackets, input/release calls and exact public
session results are retained. First metadata/source/input/image hashes were
fixed by `FREEZE.json` and Issue comment5968463992 before collection; all24
frozen files still match, with seven runtime files byte-identical to selected
main8d89dcff4508fac19945731ddf46ffb4d5092d8c.

## What the counterexample establishes

The release primitive successfully did its documented job. It is not a
revocation primitive. A safety-plane composition must revoke/suppress queued
positive input as well as release currently held controls. The successful
release-only boundary in #6999 had no later positive input and remains unchanged.
This result rejects promoting that narrower composition to #17's no-late-input
requirement, not the prior PASS or the public adapter's documented contract.

The Event and gate wrapper are probe-owned. The reference checks only these
key_state operations and is not production cancellation, an independently
supervised broker, atomic cancellation across check/use, generalized text/
pointer/chord revocation, a hardware watchdog or a supported task runtime.
XQueryKeymap/QueryPointer report logical X-server state, not hardware sensing;
app receipt timestamps include receiver scheduling. The query-start/end bounds
and serialized owner emission chain are checked, not exact injection instants.
The source's `program_emissions` counter spans all same-backend emissions while
execute runs, including auxiliary cleanup; input/release logs separate those
roles instead of treating that counter as pure program-thread attribution.

GetImage and encoding returned before the injected persistence pause; Event.wait
releases the interpreter. No stalled X reply, CPU-bound encoder, real disk/fsync,
host/compositor failure, natural incident rate, model/game/useful task effect,
latency/token benefit, real cancellation API or general reliability is tested.
Three repeats per arm are a finite discriminator, not a population estimate.

## Verification and preserved qualifications

14 hand-derived saved-oracle tests pass. Initial unimplemented-ValueError
construction attempt had1ERROR and11 vacuous refusal passes; it is not counted
as negative-control proof. A corrected stub produced12 properRED failures before
implementation; extra missing-release/owner-counter joins produced2RED failures
before being added. All first records remain in `construction/`.

After collection,14 different in-memory corruptions of actual saved rows were
all rejected; original raw hash unchanged. The new oracle also binds summaries
to `execution.observations`, public/cleanup release calls, query-start brackets
and serialized owner counter changes—the prior #6999 review's Minor is addressed
in this new method without modifying its old frozen verifier. Two saved replay
tests reproduce the decision and decode/hash-check all12 PNGs.

Local host CI40/40 (14oracle+2saved+22workspace+2scorer replay), immutable-image
package CI16/16 and top-level namespace Git-tree check pass. Git-dependent
workspace tests run on the host because this cached science image lacks Git;
the known preceding #6999 container-CI failure was not repeated. These are
applicable bounded checks, not all repository experiments/workflows; no archived
formal/native producer was replayed. Actual commands/versions/output are saved.
Nonfatal unresolved XF86keysym warnings in all12 Xvfb logs are retained.

The prospective description allowed HOLD for other coherent contrasts. The
frozen checker is stricter: it recognizes this exact discriminator or records
STOP_INVALID_EXPOSURE for failed trace gates; it has no general alternative-
contrast/HOLD classifier. None of the current12 rows took that branch. Preserve
this implementation limitation rather than change the frozen oracle or result
after observing the data; other contrasts would need separate adjudication.

Only our named private Docker/VM was used. Full container creation flags,
terminal inspections and actual cpu/memory/swap/pid cgroups are retained. The
guest has normal-mode host integration, not an independent security boundary.
Ownership/terminal stop readback and independent review accompany this package;
no shared engine, other guest, GPU, user desktop or prior allocation was touched.

## Handoff

Use PLAN/FREEZE/source for method identity, runs/ for original outcomes,
RESULT for derived counts, validation/ for tests/corruptions/cleanup, and FILES
for package byte identity. Do not rerun the consumed candidate/auditor or alter
its first FAIL. The next integration requirement is a real authority owner that
revokes the queued suffix and independently confirms release, together with
useful feedback/bounded recovery under matched conditions; this package does not
close #17/#57 or authorize a model/game/shared allocation.
