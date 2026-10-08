# Issue #6710 — independent controller-law replay

## Disposition

Allocation 01: **`STOP_AUDITOR_FREEZE_KEY`** before the frozen input was read. Its one auditor invocation is preserved and was not retried.

Allocation 02: **`PASS_AUDIT_REPLAY_SCOPED`**. A separately authored discrete-event replayer exactly reconstructs all **36 policy runs** (9 traces × 4 policies) from the immutable #6650 fixture and original RAW, with **0 field differences**; all **9/9 mutation controls** are rejected. Candidate executions=0, independent auditor executions=1, retries=0 for allocation 02.

This verifies conformance of the retained finite-trace result to the reconstructed controller law. It does not change the predecessor's `FAIL_HYPOTHESIS`: on `sustained_overload`, fixed generation delivered 13 stale optional requests, queue-length delivered 3, and age-persistence delivered 6. It is not a positive efficacy result or evidence to deploy the throttle.

## Lineage and scope

This is an audit-only successor to #6650 / merged PR #6670. The predecessor fixture and raw output remain byte-identical and read-only. The replayer does not import or execute predecessor `candidate.py` or `auditor.py`. It reconstructs event arrival order, per-session eligibility, optional-request ordinals, pending-age and queue-length signals, dwell/recovery transitions, suppression decisions, FIFO service admission, generation-at-start, deadlines, and terminal results. Full expected request/service/state/transition objects are compared with retained RAW.

The method covers authored synthetic traces only. No new candidate, model, GUI, human, user data, live task, or runtime controller was executed.

## Preserved allocation 01 STOP

The first frozen auditor source expected `fixture_sha256` as a top-level key, while its freeze manifest stored the value under `inputs.fixture_sha256`. The container exited 1 with `KeyError` before opening fixture or RAW. This is `STOP_AUDITOR_FREEZE_KEY`, not a scientific mismatch. Its stdout/stderr, original freeze, sources, and exit are retained under `formal_01/`. Allocation 01 is not retried or relabeled; allocation 02 has a distinct ID, freeze, and output directory and changes only the freeze-key lookup.

## Allocation 02 formal evidence

- Container: OrbStack Docker Engine 29.4.0, `linux/arm64`, image `python@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0` (Python 3.13.15).
- Command used `--network none`, read-only container root, read-only full-source bind mount, separate writable output mount, dropped capabilities, no-new-privileges, `--cpus=0.5`, `--memory=536870912`, and `--pids-limit=64`.
- Docker events retain container ID `4a40ce2cf157ae32db1773b3f68a76254ffbf69697bc11e548741b5a432ab873`, start, exit 0, and destroy.
- A separate post-run runtime diagnostic container observed cgroup v2 `memory.max=536870912` and `cpu.max=50000 100000`. This reports the observed boundary for that diagnostic container only; it is not a claim about host-wide or every-container enforcement.
- Independent formal audit: 36 policy replays, mismatch count 0, nine named mutations rejected, exit 0. Machine-readable receipt: `formal_02/AUDIT.json`.

## Construction and delivery checks

Focused host construction suite: 4/4. All selected Analysis Index workflow suites pass locally (96 tests total), including the new #6710 suite. The two suites that pin the historical workflow source were run after emulating Actions' exact pre-test restoration of commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd`; the current workflow was restored immediately after those tests and includes the new focused suite.

Repository Analysis Index: 517/517. Research workspace index: 156 top-level namespaces. Public Navigation: 26 documents / 1,485 repository-relative links. Python compilation and the changed-path whitespace check pass. The frozen allocation-01 preregistration retains its original Markdown hard-break spaces, as required by its recorded SHA-256; the only `git diff --check` findings are those three intentional lines in that immutable source. All other changed paths pass whitespace checks. The original #6650 T0 result remains unchanged.

## Limits

Exact conformance to the authored traces does not establish that the model matches real queues, that the simulator's policy specification is complete, or that persistence gating improves GUI-agent quality, correctness, latency, token use, user value, or safety. The predecessor hypothesis remains failed under its frozen primary comparator.
