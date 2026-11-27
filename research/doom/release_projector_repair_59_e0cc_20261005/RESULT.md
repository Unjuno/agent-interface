# V4 release projector: one-to-one matching and producer compatibility

2026-10-05, worker e0cc, FINAL-v5. **Scoped repair candidate; not merged.**

The old helper could report `measurement_ready=true` for admissions A and B plus two releases of A, leaving B unmatched. It also rejected normal V12/V4/batch output because its fixture supplied two fields absent from the producer: admission `operation=down` and complete-batch `owner_sample_after_batch_available=true`.

The repair validates identity types before dictionary access, consumes each admission exactly once, and requires complete batch position coverage within an owner/token/program/step group. It accepts omitted down-operation and availability fields only alongside the real batch schema, ordered sample timestamps, matching owner/token flags and verified key-up/empty owner state. Admission acknowledgement and the common deadline are exact integers with ordered clocks. Output retains the acknowledgement time; application consumption stays `unobserved` and physical authority stays false.

This helper deliberately supports unambiguous **same-step, same-deadline key pairs**. Cross-step holds, repeated admissions for the same identity and renewal across a pair remain unready; they need stronger admission custody. This limitation is in source and a negative composition test. It is separate from #8108's direct-receipt analyzer and #8094's V39 adapter projection.

## Evidence

- Original review probe: frozen #8119 head `3ceac8ba779b7b8a43c7a29f135e040dc637b1f8`; duplicate release reproduced, preserving input, result, source and receipt in `original-review/`.
- Ordinary regression base: current main snapshot `1703ec621dbe12a8be5fc808e9e3d1f77b775829`. This already includes #8127's concrete deadline and retry-continuity checks; those are preserved.
- `red-v1`: 16 test methods, 25 failed assertions/subcases and 20 malformed-identity TypeErrors; exit 1. The actual normal and retry producer cases both returned unready. Original logs and every source snapshot are retained.
- `green-v1`: the same 16 methods pass, exit 0. Only the projector source changed between these two runs; test/fixture/dependency snapshots match exactly. Normal and one-retry two-key batches project A and W. Cancellation, cross-step input and duplicate releases remain unready. Test cleanup verifies each fake owner thread stopped and its fake key set is empty.
- Syntax compilation and scoped source/authored-document whitespace checks pass. The full archived patch check reports preserved trailing spaces in original unittest stderr and diff-context lines; these inert raw records are retained unchanged (`full-whitespace-check.txt`, `final-precommit-checks.json`). No project-level linter/typechecker configuration exists at the root or touched directories. Optional remote CI and broad repository suites were not run.
- Separate nonauthor technical review found no material defect in this scope, checked the exact source hashes and retained results, and confirmed the direct-raw composition boundary (`review-v1/`). It is not a quorum vote or current-main integration approval.

The composition uses actual V12 owner threads, V3/V4 wrappers, batch `raw`, batch flush, receipt join, state sampling and publication. Xlib and the unused ancestor backend initializer are synthetic. It does **not** run the Session, typed program executor/lowering, full V39 loop, ViZDoom, models, live X11 or a container. Monotonic nanosecond fields come from local Python; they are not a latency benchmark or a physical/application-effect observation.

The separate #8132 exact-integer attempt-ordinal finding and repair are credited to that worker: head `c405b129e83c613e815160f841070ed68267be1d`, [coordination comment](https://github.com/Unjuno/agent-interface/pull/8132#issuecomment-5991537846). Its author requested carrying the regression into this broader repair. The predicate and regression property are included here; its original one-shot formal probe is neither replayed nor counted as a new discovery. That PR and evidence remain intact.

## Scope and next step

This repairs the offline measurement gate only. Full V39-to-V15 control-loop validation, private-game allocation, live input release, useful feedback during model latency, recovery, matched resource benefit and MAP01 completion remain unestablished. #59 is not complete. No input authority, main merge, protection bypass or merge quorum is claimed. Technical review is recorded separately from content votes and current-main integration approval.

Publication retains inert `.py.txt` source snapshots and raw-to-public hash mappings. Public logs normalize the private workspace path; original bytes remain in the dedicated local work directory. Reproduction commands and environment are in each run's `receipt.json`; the recorder is retained as `run_checks.py.txt`.
