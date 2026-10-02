# Archival qualification: current-main source audit STOP

Prepared 2026-10-02 from original PR #5966 head `c05303650a8671087e649f2e618190361c71c665`.
This is preservation of a consumed source-audit attempt, not a new source inventory or live allocation.

## Retained outcome and missing evidence

`STOP.json` records `STOP_RUNNER_REPO_ROOT`, candidate invocations 1, independent auditor invocations 0, process exit 1, and no retry. The retained account says the relative repository-root argument overshot the checkout before the preregistration or expected source blobs were read. Scientific source inventory remains `NOT_EVALUATED`.

The original PR description and `RUN.md` say that the full traceback is retained in `STOP.json`; the committed file actually contains a structured failure summary, not a traceback. The nine-file original package contains no raw candidate stdout/stderr, full traceback, `candidate_output.json`, or `audit.json`. Those missing artifacts have not been reconstructed or manufactured. `REPORT.md`'s reference to raw candidate/audit output and the `Pending` audit section in `RUN.md` do not establish such output or a runnable continuation. This consumed attempt remains terminal and is not retried.

`RUN.md` reports an initial 2/4 construction-test failure, a fixture correction, then 4/4 passing construction tests, compilation and diff checks. These are historical author-reported checks; this archival review did not rerun or import the candidate, auditor, or tests and does not independently reproduce those behavioral results.

## Fresh static verification

At the original head, all nine package files reconstruct their published Git blob identities. All eight SHA-256 manifest entries match the retained bytes; uppercase hexadecimal in the original manifest is equivalent to lowercase hexadecimal. The three Python files parse as syntax and the two JSON files parse as data. Parsing and hashing do not execute archived source or validate its behavior.

The original package and its manifest are retained byte-for-byte. This separate qualification does not rewrite the frozen record or add itself to the historical manifest. At main `e97d21bb6142b3ed0be00744671d3b16f5cde5bb`, all nine package paths were absent, so this is distinct STOP preservation rather than already-main administrative closure.

## Source and owner boundaries

The historical preregistration `research/doom/map01_measurement_integration_live_v2_prereg.json` has Git blob `88dddea060ad1434a8bc7d67469382928a70ddd7` both at the attempt's frozen snapshot `b54ec8fac5d005d510a5787d98b9ad7a24d96923` and the inspected main snapshot. That limited identity check is not the unperformed union-of-source-hashes audit and does not refresh the retired `map01-measurement-integration-live-02` allocation.

The [owner's STOP notice](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-5929181343) retains this failed attempt without retry. Issue #59 remains open; preservation does not establish live telemetry, physical occupancy, useful feedback, recovery efficacy, task completion, or MAP01 exit. Any future audit requires its own fresh additive allocation and source freeze. No resource lease, run permission, source execution, container, model, GPU, GUI, input, or Actions dispatch is implied by this archive.
