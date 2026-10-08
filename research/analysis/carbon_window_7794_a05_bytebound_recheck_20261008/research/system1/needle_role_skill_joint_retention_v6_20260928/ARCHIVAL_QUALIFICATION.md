# Archival qualification: v6 role-skill contract and thread instrumentation

## Disposition and identity

This package preserves all 29 original files (204,457 bytes) from [source PR #5226](https://github.com/Unjuno/agent-interface/pull/5226), head `269431aed4e2aa80b8a86551b002fbba9d6aaddb`, with their exact Git blobs, original paths, byte content and historical chronology unchanged. The original directory tree is `ed70394be41900fc13584581126f6465c977a758`. This separate note supplies limits recorded outside the package reports; it does not repair source, rerun an experiment, validate a formal gate, or change a historical decision.

At archival review on 2026-10-01, source PR #5226 remained open/Draft and [owner issue #5081](https://github.com/Unjuno/agent-interface/issues/5081) remained open. The owner's [latest drift checkpoint](https://github.com/Unjuno/agent-interface/issues/5081#issuecomment-5914724050) explicitly says to keep the existing PR/branch as historical/additive evidence and not merge it or treat old-main construction as current-main Stage-0. This separate preservation does not change that restriction or the source PR's readiness.

## What is preserved

- The zero-fit contract suite, exact argv/lease/comment binding, launcher and watchdog preparation, source freezes, and append-only host construction chronology. The final host record reports 27/27 fixtures; earlier 8/8, 16/16, 17/17 and other counts apply to their recorded revisions and are not new results here.
- The single host two-thread boundary probe's original raw record, audit, source, freeze and plan. Its retained decision is `PASS_HOST_THREAD_OVERLAP_INSTRUMENTATION_SCOPED` with the narrow scope below.
- The historical Windows Docker fixture stdout, realized argv, prelaunch path STOP, initial failed audit and receipt, and separate corrected v2 receipt/auditor/output. The original `HOLD_AUDIT_INTEGRITY` is not overwritten by the corrected construction receipt.
- The copied v5 lineage files. The predecessor's `HOLD_AUDIT_INTEGRITY` and quality-gate miss remain unchanged; v5 is not evidence that the unrun v6 formal succeeded.

These are attributed historical records. No original source, test, auditor, runner, model, optimizer, seed, Docker command or experiment was executed during archival preparation. Verification was limited to read-only repository metadata/content, byte hashes and retained-data inspection.

## Docker coordination deviation remains controlling

The retained `construction_runs/20261001-docker-stage0/REPORT.md` reports 27/27 protocol fixtures and a corrected independent audit with 25 passing checks in the cached pinned Windows Docker Desktop image. Its folder name and `PASS_DOCKER_CONSTRUCTION_FIXTURES_ONLY` receipt do not establish the authorized Stage-0 gate.

The owner's [coordination disclosure](https://github.com/Unjuno/agent-interface/issues/5081#issuecomment-5914203826) and [source PR comment](https://github.com/Unjuno/agent-interface/pull/5226#issuecomment-5914204213) explicitly record that this Windows invocation lacked the coordinator release required by the frozen #5081 allocation. A distinct host and an empty local container inventory did not supply that release. Preserve the run as an **out-of-lane construction observation**, not an authorized Stage-0 result, formal result, or permission to advance.

The raw Docker stdout SHA-256 is `299b414adbca9e22ccc370aa4ef288711cdfcc25e4cc0f7aa8e9cfc9e088cf6f`. Its exact committed bytes match this digest. The initial audit's missing `--` token comparison and one-character receipt-digest transcription error remain visible in the unchanged first auditor, receipt and output; the separate v2 artifacts record the correction. Hash identity is not resource authorization.

The [queue refresh](https://github.com/Unjuno/agent-interface/issues/5081#issuecomment-5914309593) retains `STOP_RESOURCE_GATE` for any new v6 Docker invocation or formal seed access. The later [CI/validator fixture note](https://github.com/Unjuno/agent-interface/issues/5081#issuecomment-5914623747) is expressly separate reproducibility evidence and does not resolve the coordinator gate. No archival action grants a resource lease or retries a historical invocation.

## Thread-only placeholder and source-flow scope

The boundary raw record captures one process with two distinct threads. Its query is a barrier-blocked placeholder and its trainer interval is an empty critical section. The reported 56,400 ns intersection supports only this captured event-ordering/instrumentation observation. It is not a model-forward/optimizer overlap, separate-process result, PyTorch/GIL guarantee, latency benefit, online adaptation result or role-retention PASS. The raw and audit SHA-256 values are respectively `f3c7582bda84279a48821b91c5e8d4386239cc291c4ef2ea41890612092ca611` and `53ae516627838f529ab55abbf07571acf282d82a7c4be580d8baa500076f99c7`.

The later [pre-formal source-flow audit](https://github.com/Unjuno/agent-interface/issues/5081#issuecomment-5914388125) further limits the proposed v6 runner:

- The intended ordering starts a query thread, waits for its first call to begin, then generates a synthetic feedback row and includes it in the optimizer batch; the raw auditor requires every feedback update interval to overlap a retained individual inference-call interval. This is static contract/control-flow evidence, not an observed runtime overlap.
- Both workers are threads in the same PID. Validators require unequal worker-ID strings, not unequal process IDs. No separate-process claim follows.
- A query uses a cloned fixed adapter snapshot for that entire query. Updates affect the selected live adapter and later query snapshots, not the in-flight query's predictions.
- Feedback is deterministic synthetic data from `feedback_row(seed, arrival)`, not feedback generated by that query, a model response or a user.

The static review does not pass Stage-0, spend construction/formal seeds, or turn the placeholder probe into an executed model study.

## Exact source identity and lineage caveat

Data-only reconstruction verified all 29 original Git blob IDs and the original directory tree. All nine current `CONSTRUCTION_FREEZE.json` source SHA-256 entries bind the exact retained package files. That consistency applies to the v6 copied files, not every upstream identity assertion.

In particular, the retained `lineage/runner.py` and `lineage/audit.py` Git blobs are `2744394c992e158bcc14f5948a57f6e99e136081` and `030d115457189ed85be2cc562102aae5aa2531bd`. The freeze's `lineage_git_blob_sha_from_github_main` records the different historical upstream blobs `367cf88448130ce997f55c02edb653a30d1176fe` and `c6be7b103cdc989fdac1e7cfa12657818fa5c03e`. Their non-trailing-whitespace text compares equal, but their exact Git identities differ. Do not describe all vendored files as byte-identical upstream originals. Preserve both the declarations and original copied bytes without normalization.

## Main coverage and remaining gate

At reviewed main `24f6b7d5f9395105807f981d48db212e6692a6f4`, the v6 package directory was absent. A complete, untruncated `research/system1` tree read found exact matches only for the two lineage freeze/sidecar blobs already retained in the v5 package; it did not supply the other 27 exact v6 blobs. Existing v5 and sibling studies therefore do not justify exact-superseded closure of #5226.

Formal v6 remains **UNRUN / STOP_RESOURCE_GATE**. The reserved construction seed `9980514` and formal seeds `9980211`, `9980311`, `9980411` are not consumed or authorized by this archive. Any future assigned Stage-0 requires a newly collision-checked allocation, exact then-current-main/source freeze, named coordinator grant and fresh ownership/inventory checks as specified by #5081/#5085. A path-only drift check or historical branch merge cannot substitute for that freeze.

The preregistered role-retention, comparator improvement and strict update-latency gates remain untested by this preserved package. There is no scientific v6 PASS, natural-language role recognition, model-quality result, live GUI/input authority, production claim, runtime promotion, source PR readiness change or owner-issue closure.
