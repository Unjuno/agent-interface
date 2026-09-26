# Issue #3188 audit-v3 control-schema successor — runner successor preregistration

Allocation: `issue3188-audit-v3-control-schema-20260921-02`

This is a distinct successor to allocation `...-01`, whose first outcome `STOP_TEST_HARNESS_IMPORT_ERROR` is preserved under `results/allocation-01/`. The auditor and unittest source remain byte-identical to the already frozen v1 sources. Only the external host test loader changes.

## H / T / D / C / U

- **H:** The exact frozen v3 audit and test suite will validate the unchanged formal-02 raw and reject the named-control swap, Boolean-to-integer substitution, and truth-table mutation.
- **T:** Use the exact frozen v3 source SHA-256 `3839e9c47e3f8cd59901b7cc99a9fdacda3ece6ed3b873c4bf1692c000c96f76` and test SHA-256 `1ce5e9fe5b8198156221a58b8b2f4b965d42a1f02b56dec3723716f448421070`. Verify the unchanged raw/run/candidate-audit inputs against allocation-01's freeze. The custom import loader must implement both `create_module()` and `exec_module()`; its exact source and hashes are frozen in `FREEZE-02.json`. Invoke the same five-test suite once. No source edits or formal raw writes.
- **D:** Same scoped decision gate as protocol v1: baseline passes and all mutation tests reject for the exact expected reason. The v1 STOP remains retained; this new allocation has its own first outcome. Container validation remains separate.
- **C:** Host CPython 3.12.10 only; no model/game/GUI/X11/input/network request. No Docker/OrbStack result is claimed.
- **U:** This is a new test-runner allocation for a finite auditor construction boundary; it neither retries allocation-01 under its ID nor changes formal-02's `HOLD_FROZEN_AUDITOR_DEFECT`.

## Runner change and freeze

The previous STOP occurred before test discovery because a custom `importlib` loader omitted `create_module()`. This allocation changes only that host harness requirement. The corrected runner must return `None` from `create_module(spec)`, execute the byte-identical frozen module in `exec_module(module)`, verify all frozen payload hashes before discovery, and record one suite invocation with five tests. The source/test files and H/T/D gates are not retuned.
