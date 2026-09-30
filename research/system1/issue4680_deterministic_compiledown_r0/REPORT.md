# Issue #4680 — deterministic compile-down boundary, allocation 01

## Disposition

**HOLD_INDEPENDENT_AUDIT_AND_ACTIVATION_RECEIPT_INCOMPLETE.** The one frozen Docker study invocation reported `PASS_DETERMINISTIC_COMPILEDOWN_EQUIVALENCE_SCOPED` for 256/256 rows with zero reported mismatches. The separately invoked v1 audit exited 0 and reported `PASS_INDEPENDENT_AUDIT`. Post-run review found that this audit only compared the three decision strings already present in `RESULT.json`; it did not independently derive the expected action for each row. Also, the failed-candidate/ACTIVE-preservation control is retained only as a boolean, not the before/after bytes or independently checkable digests. Therefore neither the experiment's semantic agreement nor the active-snapshot guard is independently established to the frozen standard. Preserve both raw files unchanged; do not promote the runner's PASS as the allocation's accepted result.

## H / T / D / C / U

- **H:** A compiled finite decision table can preserve the frozen deterministic policy across its entire declared finite input space and fail closed on invalid/stale/forbidden inputs without replacing ACTIVE on candidate rejection.
- **T:** One Docker study invocation compared direct evaluator, compiled lookup, and a code-separated reference oracle on all 256 combinations. A separate Docker audit process checked row cardinality, recorded agreement, control booleans, source identities, and scope fields.
- **D:** Raw runner disposition `PASS_DETERMINISTIC_COMPILEDOWN_EQUIVALENCE_SCOPED`; raw v1 audit disposition `PASS_INDEPENDENT_AUDIT`; accepted research disposition **HOLD** because v1 audit did not recompute row semantics, and ACTIVE preservation lacks a retained byte-level receipt.
- **C:** A distinct implementation of the expected policy does exist in `oracle.py`, but the auditor never calls/reimplements it. The v1 audit therefore verifies internal consistency of reported decisions, not correctness against the policy. A passing boolean from the same runner is not independent evidence of activation behavior.
- **U:** Synthetic deterministic policy only. No Needle adaptation, Astra demonstrations, learned selector, GUI/effect path, latency, amortization, or general integration claim. #4205 adaptation prerequisite remains unmet (PR #4576 records 0/7 exact); #4203 fast-backend prerequisite remains unmet (PR #4584 is a pre-inference STOP).

## Frozen identity and execution

- Intake `main`: `89ca30f756704c9e378fc2cdde90a03c6a569c03`.
- Freeze branch: `research/issue4680-deterministic-compiledown-20260927`.
- Freeze commit: `222d614d390c8f444b452bdaaa1e61410e84f5d6`.
- Frozen readable package: `research/system1/issue4680_deterministic_compiledown_r0/`.
- Docker Desktop 28.5.1; image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64; in-container CPython 3.12.14.
- Network disabled, read-only root/source, one CPU, 512 MiB, 32 PIDs. No model/provider, GUI, OS input, external network, or workflow/Actions.
- Study invocation count: 1; study exit 0. Separate v1 audit invocation count: 1; audit exit 0. No retry, replacement, exclusion, or post-result tuning.
- Excluded construction syntax check: `ast.parse` of the Python files in the same pinned Docker image; `CONSTRUCTION_AST_PASS`.

## Raw results

- `formal01/RESULT.json` SHA-256: `0d6c75e32d1efa6a2b365df0bccf6b100d197dbd8c157879bfd9db9cdd643f71`.
- `audit01/AUDIT.json` SHA-256: `efde8d5d847a81b806228050e97c99cda945c978d4c81d067e5212a83c309d48`.
- Runner: 256 rows, 256 unique states, 0 recorded mismatches; recorded actions: CONTINUE 2, CORRECT 2, WATCH 2, NO_ACTION 8, YIELD 242. These are runner-reported counts, not independently reconstructed in v1.
- V1 auditor: `errors=[]`, rechecked 256 rows and five source files, and bound the raw result hash. Its limitation above invalidates treating that as a semantic independent audit PASS.

## Next evidence needed (not performed in this allocation)

A separately frozen, independently implemented posthoc verifier could reconstruct the expected action for all 256 rows and require the exact state-space set. A new allocation would be required to retain ACTIVE before/after bytes/digests and actual activation result, since those were not included in this raw result. Neither step may overwrite this allocation's raw files or convert its initial outcome retroactively.

## Addendum — posthoc independent matrix audit v2

An audit-only successor was separately frozen and run after the initial report. It did not invoke the study or candidate. The independent verifier reconstructed the expected action for every state from the frozen policy description, required the exact 256-state Cartesian set, and checked each of the recorded \`direct\`, \`compiled\`, and \`oracle\` outputs against that reconstruction.

- V2 result: \`PASS_INDEPENDENT_MATRIX_AUDIT_SCOPED\`; 256 rows independently reconstructed; semantic mismatches 0.
- Ten copied-evidence corruptions (decision fields, match claim, missing/duplicate/changed row, scope, invocation count, image identity) were all rejected.
- Raw input binding: unchanged RESULT SHA-256 \`0d6c75e32d1efa6a2b365df0bccf6b100d197dbd8c157879bfd9db9cdd643f71\`.
- V2 audit output SHA-256: \`e82d87fba6016f2fc0e0deb5496ec74f772f4ee7b25ef76b03277b27e4eb9667b\`.
- V2 auditor source SHA-256: \`006f357895e1f64a5d2c2aff714d169f83b5ef434cf22975ae7559687fcddbc4\`; source and freeze were committed/read back before the audit-only invocation.
- V2 audit invocations: 1; study invocations by v2: 0; Docker exit 0.

This closes the independent-verification gap for the finite decision matrix only. It does **not** supply the missing ACTIVE before/after byte receipt, so the accepted disposition of the whole original allocation remains **HOLD_ACTIVE_SNAPSHOT_RECEIPT_MISSING**. The initial v1 audit output is preserved unchanged as historical evidence.
