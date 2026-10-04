# Rescue of #6930: relay reply-reader failure without replay

Source branch `fix/relay-reader-errors-01a0ff58-20261003`, head
`575bf53bc449fc3c09b61610e6e51a16dab76e19`, original delivery PR #6930.
Preserve all 53 predecessor packet files (52 manifest entries) unchanged under
`research/integration/relay_reader_error_57_20261003_01a0ff58`. Complete source
history is archived at `archive/recovered/pr6930-source-575bf53-20261004`
before retirement. Historical Windows results, first failures and publication
repairs remain qualified exactly as recorded; no old content votes are revived.

## Adopt the useful missing implementation

The existing child-stdout Readline Interface has no error listener. A genuine
stream error can terminate the host instead of reconciling the pending request.
The missing source change is one line: `reader.on('error', fail)`. This invokes
the existing blocked-state handler, rejects the same outstanding promise with
delivery uncertainty, prevents new sends, and preserves an already returned
result. No replay, cancellation protocol, backend cleanup or GUI release is added.
The four original regressions are appended unchanged to current main's existing
test module; later exit-journal tests are retained. Current capacity preflight,
exit-journal error retention and public capture-review logic are not overwritten
by old source. No workflow change is needed: this module is already selected.

## Fresh executed local evidence, 2026-10-04 JST

macOS Node26.7.0, actual inert Node child pipes and private files:
`node --test --test-name-pattern='reply reader' runtime/host_v1/test_relay_client.mjs`
first produced three FAIL/one positive control PASS. All three failures show the
unhandled Interface error and child-host exit1, not missing imports. After the
one-line correction, all four pass. See untouched `node-red.log` and
`node-green.log`. TDD verified the missing error handler before implementation.
The full 14-module Node selection from current Native MCP workflow passes
199/199, zero skips/cancellations; see `node-selection.log`. This includes later
exit-journal regressions and the independently rescued busy-response test.
Node22/Linux/hosted execution remains a separate gate, not inferred from Node26.

`test_archive.py -v` passes two tests normal and optimized Python3.14.5:
53 original Git blobs, 52 manifest hashes, 47 original/public mappings, base and
source Git pins/OIDs, four historical check receipts and copied source witnesses.
Historical RED and green-01 setup failure exits stay1; green-02/coupled exits stay0.
No archived capture/repair/producer/native Windows experiment is executed.

The shared project integration command was also executed once locally using
task-owned Python3.12.14 with the workflow dependency pins (mcp1.30.0,
Pillow10.2.0,numpy1.26.4,python-xlib0.33), not a global installation:
`python runtime/integration_checks/native.py --output <fresh task-owned directory>`.
It exited1: protocol426 tests, four FAIL/six ERROR/five skips; harness205 tests,
31 ERROR (including subtests). `native-pinned-result.json` and complete
`native-pinned-protocol.stderr.log` / `native-pinned-harness.stderr.log` retain
every failing method/subtest, exact traceback and path. The four assertions are:

- `test_final_image_uses_new_call_root_without_extra_observation`
- `test_mutated_image_preserves_result_without_rendering`
- `test_digest_resume_rejects_noncanonical_bytes_and_read_race`
- `test_failed_process_reports_bounded_stderr_without_relaunch`

Linux `/proc` dependencies are visible in several errors; this does not classify
all four assertion failures as environmental or prove they are harmless.
No broad local-native PASS is claimed. The Node correction remains subject to
ordinary hosted required checks; failures cannot be bypassed or rewritten.
Docker image inspection again STOPs with daemon blob `operation not supported`.
No shared VM/daemon reset, image prune, allocation or repeat bypass was attempted.
Raw log whitespace is preserved by archive-local attributes, not normalized.

## Integration and retirement gates

Normal PR integration must precede exact main packet/sibling/production checks,
remote full-history tag readback, fresh paginated open head/base dependencies,
unchanged/unprotected source and descendant checks. Source and rescue refs may
then be retired only with exact SHA leases under the user's rescue/cleanup
instruction. Main preservation is stronger than merely keeping a tag: the
useful error handler and original regression behaviors are actually adopted.
No parent research issue, GUI/task/model result, physical release, live backend
reader-loss cleanup or full-platform research goal is declared complete here.
