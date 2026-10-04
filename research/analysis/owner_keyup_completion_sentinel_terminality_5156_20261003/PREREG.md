# Issue #5156 synthetic completion-sentinel terminality probe

Status: frozen before execution. This is a host-only synthetic JSONL audit-boundary experiment. It does not consume or resume any #5156 X11 allocation.

## H — hypothesis

The current #5156 T3 raw-only CLI auditor validates that exactly one runner_complete record compares equal to integer zero, but may not require that record to be the final raw row. The source runner emits runner_complete only after all case, release, cleanup, and terminal-state records, so accepting a success marker moved before later rows would leave an evidence-integrity gap in this formal-result gate.

This is separate from the already executed #5895 T6 experiment, which tested Boolean/float zero aliases and mixed completion exit codes against the same frozen auditor. Those outcomes will not be repeated here.

## T — test

Freeze source to current main f474970f82d68b6648aac64f99048ad0c2fd5732 and use the existing T3 audit_formal_x11.py, test_audit_formal_x11.py::fixture_rows, and EXPECTED.json unchanged.

Construct one positive control by taking the existing fixture rows, removing its single completion row, and appending that same row last with the exact raw_rows count the runner emits. This places the completion record after every other raw row, matching the frozen runner's actual emission order. Construct one treatment by moving that single completion object to row zero while preserving every other row's order and content. Invoke the frozen auditor CLI once for each JSONL file in synthetic-cli mode under the local macOS Python runtime; use no Docker, X server, GUI, input, game, model/provider, GPU, or network.

Retain both inputs, stdout, stderr, exit codes, exact commands, interpreter version, source identities, and a separate raw-only comparison audit. The audit independently checks that the control completion is last; the treatment differs only by moving that one row; the row multisets and all non-completion order are identical; and target results correspond to the frozen decision rule.

## D — decision

- If the control exits 0 and the treatment exits 1, record TERMINALITY_GUARD_ENFORCED.
- If the control exits 0 and the treatment exits 0, record FINDING_NONTERMINAL_COMPLETION_ACCEPTED.
- If the control fails, the source/fixture binding is wrong, or the one-row treatment is not exact, record STOP_INVALID_CONTROL_OR_PROVENANCE; do not reinterpret it as a target finding.

## C and U — scope

This tests only ordering validation in a deterministic synthetic CLI fixture, against the exact frozen source. It does not test the Docker runner, X11, physical key release, application consumption, MAP01, task effect, latency, safety, or product behavior. A finding would qualify only how this auditor treats a synthetic record sequence; it would not falsify any historical raw result or prove a formal X11 failure.

## Frozen identities

- Repository: Unjuno/agent-interface
- Branch: research/5156-runner-terminality-01a0ff51-20261003
- Additive result path: research/analysis/owner_keyup_completion_sentinel_terminality_5156_20261003/
- Main commit: f474970f82d68b6648aac64f99048ad0c2fd5732
- Auditor Git blob: da805fb83f70a57ad68a0768186e214524689d40
- Fixture-test Git blob: d1eb9a854cc810fa77ca173d7e2de287ee1bd64a
- Expected-input Git blob: 3d33bda096c4c8789e183e3f864ee7626e643a7e
- Runner Git blob: 47179500c978c0e690dc9ae01b91ab12837bc418
- Image/container allocation: none; the experiment is one local host-only synthetic probe.
- Consumed or prior allocation IDs: none; #5156 A07 and #5895 T4/T6 outcomes remain untouched.

No source repair is authorized by this experiment. Any future validator change needs its own reviewed patch and regression evidence.
