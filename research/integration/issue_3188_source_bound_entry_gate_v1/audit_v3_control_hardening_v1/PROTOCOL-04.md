# Issue #3188 audit-v3 control-schema successor — allocation 04 preregistration

Allocation: `issue3188-audit-v3-control-schema-20260921-04`

Allocations 01–03 terminated before unittest discovery and remain preserved as typed STOPs. This fresh allocation keeps the frozen auditor-v3, test suite, and runner-v2 byte-identical. It corrects and freezes only the host payload mapping.

## H / T / D / C / U

- **H:** The frozen audit-v3 passes the formal-02 baseline and rejects all three named mutations: swapped `missing_receipt` guard, Boolean false replaced by integer zero, and truth-table value mutation.
- **T:** Verify exact frozen hashes before the suite. The runner's required payload key set is exactly `{runner, protocol, auditor, tests, raw, run, candidate_audit}`; map the pin sources to those names and assert exact set equality before invoking. Pass the verified freeze object separately. Use runner-v2's complete `create_module`/`exec_module` loader and invoke the unchanged five-test suite exactly once.
- **D:** `PASS_AUDIT_V3_CONTROLS_SCOPED` requires five tests, zero failures/errors, unchanged formal raw, and all source hashes matching. Mapping/integrity/setup failure is STOP; a unit assertion miss is FAIL; incomplete output is HOLD.
- **C:** Windows CPython 3.12.10 host-only; no model/game/GUI/X11/input/network call. Docker/OrbStack validation is still outstanding; this run is not container evidence.
- **U:** Finite auditor-construction evidence only. Preserve all predecessor STOPs and formal-02 `HOLD_FROZEN_AUDITOR_DEFECT`; do not claim broad auditor soundness, runtime/gameplay, or product success.

## Pre-suite invariants

Before the only suite invocation, require: (1) runner source hash equals `FREEZE-04.json`; (2) freeze runner path/hash names align with runner source; (3) payload keys exactly match the seven names listed above; (4) each payload hash matches freeze; (5) test module and audit module both use the frozen-byte loader implementing `create_module` and `exec_module`. If any check fails, preserve STOP and do not invoke the suite.
