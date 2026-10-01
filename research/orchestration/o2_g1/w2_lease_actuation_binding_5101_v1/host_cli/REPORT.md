# Frozen W2 full-CLI lineage probe — host reproduction

Issue #5116 / successor to #5101. This is a separate appended host-CPU observation; it does not replace or relabel either the original #5101 finding or the construction test in the parent directory.

## H/T/D/C/U

**H.** The frozen W2 verifier and independent raw auditor do not bind the actuation ID on input edges to the actuation ID on the matching lease-open event.

**T.** On the exact frozen eight-case fixture, run the original verifier CLI and independent auditor CLI for both baseline and a one-field mutation of `release-before-terminal`: set only `LEASE_OPEN.lineage.actuation_id` from absent to `FOREIGN-ACTUATION`; edge records remain bound to A4. Preserve all four CLI outputs, input bytes, return codes, and hashes.

**D.** A valid reproduction requires baseline verifier/auditor exit 0, 8/8 baseline cases, and then the mutant verifier and independent auditor also exit 0 while the mutated target remains authorized. If either rejects it, this counterexample is not reproduced. The auditor must report raw audit errors separately.

**C.** Synthetic trace only. Event order, all edge rows, timestamps, clocks, lease ID, inputs, and every other byte remain unchanged. The local frozen verifier, auditor, schema, and fixture exactly match the Git blob IDs frozen from main. No code modifications are made to those source files.

**U.** Windows host Python 3.12.10 CLI reproduction only, not Docker/formal evidence. This establishes neither live unauthorized input nor a runtime vulnerability or task effect. The binding candidate/oracle tests in the parent package remain construction-only. Lease interval validity, owner/session binding, and cross-clock semantics are outside this one-field test.

## Result

`PASS_HOST_CLI_COUNTEREXAMPLE_REPRODUCED` (scoped reproduction of the frozen checker boundary, not a product PASS/FAIL):

| Input | Verifier CLI | Target row | Independent raw auditor CLI |
|---|---|---|---|
| Frozen baseline | exit 0, `PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED 8/8` | `COMPLETED_RELEASE_BEFORE_TERMINAL`; authorized occupancy 298 ns guaranteed / 302 ns possible; unauthorized=false | exit 0, `PASS_RAW_TRACE_AUDIT_SCOPED cases=8 numeric=5 mutations=7/7`; errors=[] |
| Foreign lease-open actuation | exit 0, `PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED 8/8` | same `COMPLETED_RELEASE_BEFORE_TERMINAL`; 298/302 ns; unauthorized=false | exit 0, same raw-audit PASS; errors=[] |

The raw-only auditor therefore accepts the same altered trace independently of the verifier's output. Its seven built-in unrelated corruption controls still reject 7/7, so those controls do not cover this lineage-binding mutation.

## Provenance and files

Frozen current-main Git blob IDs rechecked locally with `git hash-object --no-filters`:

- verifier `d8f4221811b160e5714d2d6e4154c82af94d633e`, SHA-256 `6bf7c2c2fc4b221a51ddd8a615777ddf11617c4ece4a03465e3bbbbf3b724c35`;
- auditor `1942546e60ad7e6cb56b9a383830033db14d0397`, SHA-256 `f00677e91ceb3a67bddff0d941e076649c8da759f422c3a193725b2e897eacb7`;
- schema `ebc424d2df631aa74c6d9aee4699c595a27ed589`, SHA-256 `3ca91926d9e362e02dd0272a03b67e2d65b46199bcfb1bb8f55c29cfe92f6d76`;
- fixture `0a49a00567c25766495cd332be50f6c2946781f7`, SHA-256 `6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f`.

The altered fixture changes only the lease-open lineage binding; its SHA-256 is `599ebc828183bc454d36a3b6db7007a3e65de41561ff0b746c7a235fa316b011`. Raw output hashes are in `RESULT.json`. Commands are reproduced by `../run_full_cli_probe.py`; output paths must be new/empty.

No Docker container was launched and no sibling container was inspected or modified. The shared resource remains unassigned to this lane.
