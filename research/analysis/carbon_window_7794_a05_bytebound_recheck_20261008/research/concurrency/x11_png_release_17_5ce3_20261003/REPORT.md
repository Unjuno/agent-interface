# Result: a public-X11 persistence/release coupling boundary

Issue [#6999](https://github.com/Unjuno/agent-interface/issues/6999), successor to
closed [#810](https://github.com/Unjuno/agent-interface/issues/810), under #17.
**PASS_PUBLIC_X11_PNG_RELEASE_BOUNDARY_SCOPED**. This is a private Xvfb integration
witness; not a completed production safety plane or main research goal.

| Arm | Cells | State at request +150ms | First independent confirmed-up, fault cells |
| --- | ---: | --- | --- |
| Healthy coupled | 3 | up, writer and program complete | not a fault comparison |
| Healthy separate | 3 | up, writer and program complete | not a fault comparison |
| Blocked coupled | 3 | down, writer and program pending | 402.813, 403.171, 404.460ms |
| Blocked separate | 3 | up, writer and program pending | 3.074, 2.824, 2.683ms |

All 12 fresh cells ended with a neutral whole keymap/button state and exactly
one application KeyPress/KeyRelease pair. No additional press was observed.
The public session admitted/completed every fixed four-op program and verified
terminal release; all 12 exact PNGs are saved, decoded and hash-checked. The
actual checkpoint times, samples, release calls and source-writer stacks are
retained; sampling confirms an upper observation bound, not the exact release
instant. Write resume was fixed at request +400ms before collection.

## Evidence and interpretation

`FREEZE.json` was witnessed in Issue comment5968145748 before the scientific
candidate. All 24 frozen files remain unchanged; the seven runtime source files
matched main c52f021d9779e72b89a936ceb1dbc92b6ae145f5 byte-for-byte.
Candidate1 collected 12 cells in 4.22s; separate auditor1 consumed only saved
rows/PNGs, both exit0/terminal/not OOM. Scientific reruns0. `RESULT.json` derives
the summary from `runs/auditor/AUDIT.json` and immutable first `raw.jsonl`
(SHA256 f94c0fbb2fcd28ad01978b7366a7495c3d3ba33a08a122e64b7b4e7679daa9f2).
Creation flags, terminal states and actual cgroups are in stage receipts and
`runs/candidate/evidence/ENVIRONMENT.json`.

The hypothesis is supported only at this actual public backend boundary:
synchronous PNG persistence can hold up its queued release even though input
and X server remain responsive; a cleanup-only thread using the same owner and
serialized primitive can independently confirm release before persistence
finishes. This justifies keeping release independent of presentation work in a
future integration. It does not choose threads over the independent process
owner of #810 or invalidate that historical result.

GetImage had already returned before the injected write. Event.wait releases
the interpreter. No active Xlib reply, CPU-bound encoder, arbitrary Python
callback, server failure, concurrent new input or transport deadlock was tested.
The long lease only protects admission; there is no production cancellation API,
watchdog, hard deadline, reliability rate or useful task-feedback claim. A blank
owned window supplies genuine image/input events, not semantic task success.
The three repeats are a finite discriminator, not a population benchmark.

## Local validation, including failures

- Saved oracle construction: initial RED7 failures, then GREEN7; added identity
  binding RED5 failures, then GREEN12. Hand-derived records only, no X server.
- Same-image import/schema/12 construction tests passed before freeze.
- After collection, 12 different in-memory copied-record corruptions were all
  rejected; original raw hash unchanged. This measures oracle sensitivity, not
  scientific replication. Two saved replay tests check the exact decision and
  all 12 PNG identities/dimensions.
- First container local CI ran 38 tests but failed (1 failure/18 errors) because
  this immutable scientific image contains no Git. The 14 package tests and two
  scorer replay tests passed there. The failure/terminal receipt is retained;
  no image/source mutation or scientific rerun was used to repair it.
- Same complete 38-test suite passed locally with Git (12 oracle +2 saved replay
  +22 workspace +2 scorer replay); top-level namespace Git-tree check passed.
  Host bundled CPython3.12.14/Pillow12.3.0 and container distro versions differ;
  each exact command/output is saved. Not all repository workflows or unrelated
  formal experiments were run, and skipped remote jobs are not proof.
- Initial setup routing used an unmaterialized old sparse-checkout helper and
  exited before image build or scientific cells. `setup/SOURCE_ROUTING_STOP.md`
  retains that STOP. Docker legacy-builder warnings are not scientific results.

## Handoff and next gate

No production file, shared output, predecessor package, other agent branch,
default Docker engine, other VM, GPU or personal display was changed. Main
roadmap #17's independent physical safety/release plane plus useful feedback
and bounded recovery still needs integrated evidence. A successor should use
an actual independently supervised cleanup owner with the production control
request, keep per-key/readback evidence, and test other blocking boundaries;
do not rerun this consumed candidate or silently broaden this PASS.

Read `README.md` for the exact H/T/D/C/U and limits, `PLAN.json`/`FREEZE.json`
for prospective method, `runs/` for first raw/PNGs/receipt/audit, `validation/`
for failed and successful local checks. Independent code review and PR/merge
receipt are added separately so the prospective files remain immutable.
