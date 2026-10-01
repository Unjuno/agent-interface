# Issue #3188 audit-v3 control-schema successor — allocation 03 preregistration

Allocation: `issue3188-audit-v3-control-schema-20260921-03`

This is a distinct successor to allocations 01 and 02. Their STOP records remain immutable under `results/allocation-01/` and `results/allocation-02/`. The frozen audit-v3, test suite, and runner-v2 source bytes are reused unchanged; only the manifest schema is repaired and explicitly preflighted.

## H / T / D / C / U

- **H:** The exact frozen v3 auditor will pass the pinned formal-02 baseline and reject the swapped `missing_receipt` vector, `false→0` type mutation, and truth-table mutation.
- **T:** Verify the exact hashes for protocol, runner-v2, auditor-v3, test suite, formal raw, candidate run.py, and candidate audit.py. Parse `FREEZE-03.json` and assert its `runner.path` / `runner.sha256` keys match the runner's contract before suite import. The runner must implement both `create_module()` and `exec_module()`. Invoke the unchanged five-test suite once; formal raw remains read-only.
- **D:** `PASS_AUDIT_V3_CONTROLS_SCOPED` only for baseline PASS, all five tests pass (including all three mutations), zero failures/errors, and identical raw SHA before/after. Hash/schema/setup issue is STOP; assertion failure is FAIL; incomplete output is HOLD.
- **C:** Host CPython 3.12.10, no game/model/GUI/X11/input/provider/network calls. No Docker/OrbStack result claimed; separate container validation remains open.
- **U:** This allocation is finite auditor construction evidence only. It does not change formal-02's `HOLD_FROZEN_AUDITOR_DEFECT`, prove arbitrary auditor soundness, or support runtime/gameplay/product claims.

## Frozen runner contract

`runner_v2.py` requires top-level freeze keys `runner.sha256`, `protocol_sha256`, `auditor_sha256`, `tests_sha256`, and `frozen_inputs.raw/run/candidate_audit`. This allocation's freeze manifest must satisfy those exact keys and hash values before the suite is invoked. Do not alter the runner or tests after freeze.
