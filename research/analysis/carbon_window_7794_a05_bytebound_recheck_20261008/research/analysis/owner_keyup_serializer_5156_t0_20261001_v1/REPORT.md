# Issue #5156 — joined-release serializer T0

**Disposition: `PASS_SERIALIZER_CONSTRUCTION_ONLY`.** This narrow T0 addresses the exact serializer exception that stopped Allocation 04. It does not repair, complete, audit, or relabel that consumed X11 allocation.

## H / T / D / C / U

- **H:** The Allocation 04 runner failed when it added a top-level `event="joined_release"` to a row that already contained `event="owner_key_release_bracket"`. A serializer that explicitly moves the nested label to `owner_event`, then writes the joined label, can preserve all owner/caller fields and emit a complete row without changing input behavior.
- **T:** Freeze source main `4808f1ec2e45f99bd711e27be5cce4bf476c3c8e`; bind the exact predecessor runner/raw/stderr Git blobs in `FREEZE.json`. Write the consumer-visible test first. Against the retained defect-shaped expression, the provenance test failed with the expected duplicate-key `TypeError`; the malformed-event test was separately corrected to fail only on the intended contract. Implement the explicit event mapping. Run focused tests, then one candidate CLI invocation over three synthetic explicit-release rows, followed only on exit 0 by one separately implemented raw-only audit. No retry. The local auditor's mutation suite covers eight copied-raw corruptions.
- **D:** **PASS_SERIALIZER_CONSTRUCTION_ONLY.** Candidate exit 0 emitted 3 ordered rows. A separate process accepted pristine raw with `errors=[]`; all 8/8 corruption controls were rejected. The focused suite passed 5/5 and `py_compile` passed. The three rows preserved their owner/caller fields, nested event provenance, owner/intent identities, caller/request/XSync time ordering, and false authority/physical-key claims.
- **C:** This validates only local serialization of synthetic records and the audit contract. It does not test the real Allocation 04 raw or invoke the formal auditor. It is not X11, Xlib, Xvfb, owner-thread, key-up timing, physical key state, safety, task-effect, or MAP01 evidence.
- **U:** The Allocation 04 raw ends with `runner_failure` before joined-release rows were serialized. The existing formal auditor was correctly not invoked after the runner's nonzero exit. A future fresh X11 allocation must use the repaired serializer and re-run the full fixture plus its formal audit; the prior formal allocation remains consumed.

## Retained predecessor evidence

Allocation 04's exact failure remains on main under `research/live_control/owner_keyup_formal_x11_5156_20260930_04/results/allocation-04-fail/`. The runner source was Git blob `a83beffe3c2e0e432862bcdda100f9762022590d`; the unchanged incomplete raw is blob `c11d740f5f37dc538490c235b117013067a52a36`; stderr is blob `3473226a0bf77c26a0d806817e6a697e6477e922`. Its runner failure was `TypeError: dict() got multiple values for keyword argument 'event'`. Those artifacts were read only.

The first TDD red run reproduced that exception from the exact expression shape. The green correction leaves the original `event` visible as `owner_event`, sets the envelope `event` to `joined_release`, and refuses unexpected event/caller-context collisions. Tests use synthetic timestamps and never send input.

## Execution and resource accounting

Host: Windows x64, CPython 3.12.10. The unit suite was run before freeze as a construction preflight and re-run after candidate/audit; both were 5/5. Candidate CLI: one invocation, exit 0, 3 rows. Independent raw-only audit: one invocation, exit 0, 3 rows, zero errors. Candidate raw SHA-256: `f6ae0667e7f108e1a14fa2846073d48ede11204852a10e750bba5cc7fd413e94`.

Docker Desktop `desktop-linux` (Docker 28.5.1, linux/amd64) was available, but **not used**: the current #5085 record contains a bounded shared CPU reservation/competing work and no assignment for this T0. This run used zero containers, zero network, zero model/GPU/GUI/input, and no formal X11 invocation. No shared allocation was assumed from an idle `docker ps` result.

The independent audit receipt is `results/AUDIT.json`; exact commands and counts are in `results/EXECUTION.json`. `FREEZE.json` binds the source, fixture, predecessor Git blobs, decision gate, and no-retry rule.
