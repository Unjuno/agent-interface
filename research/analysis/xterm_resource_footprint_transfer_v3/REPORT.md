# #1751 retained XTerm resource-footprint transfer

Decision: **PASS_RESOURCE_FOOTPRINT_XTERM_TRANSFER_SCOPED**.

## Provenance
#1739 remains retained as `FAIL_INTEGRITY` because its local classifier bytes did not match the frozen Git object and its wrapper continued after the mismatch. #1746 remains `HOLD_ENVIRONMENT` because the container could not resolve github.com during git clone. Neither predecessor is relabeled.

For this successor, GitHub MCP returned the exact frozen UTF-8 sources already retained on main. Before scientific execution, the fresh container recomputed Git blob object IDs and matched all three:
- fixture `a5c2fd9ce302ffb0faf514c03b3bcb153c28c919`;
- classifier `90827b87cb7cfa178701e59b7d3fff6b1644e2c5`;
- auditor `7e76168255b9f11b5bf0916e739df0afdad016bf`.

The classifier was then invoked exactly once; the auditor did not rerun it.

## Result
The #1730 read/write conflict predicate classifies the retained #1707 arm semantics as follows:

| retained condition | classification | retained published direction |
|---|---|---|
| independent XTerm A/B | `OVERLAP_ELIGIBLE` | overlap ends `A_DONE/B_DONE` |
| shared-file A/B | `SERIAL_CONFLICT` | deliberately unsafe overlap ends `B_DONE/B_DONE` |
| unknown footprint | `SERIAL_UNKNOWN` | fail closed |

Two discriminators behave as required:
- deleting `shared_file` from the declarations makes the unsafe shared arm falsely `OVERLAP_ELIGIBLE`, showing completeness matters;
- aliasing `surface_A` and `surface_B` makes the independent pair `SERIAL_CONFLICT`, showing canonical resource identity can conservatively remove overlap.

The independent gate audit passes every retained check.

## Interpretation
The analytical #1730 contract transfers to this narrow retained real-XTerm example: a known independent pending tail can be distinguished from a known shared-file conflict by explicit resource footprints. Surface identity alone is not the deciding object; resource identity is.

This does **not** repair or relabel #1707's original audit failure. #1710 remains the sole owner of its timestamp-audit successor.

## Limits
The footprints were manually declared from known command semantics. No automatic dependency discovery is demonstrated, and hidden resources can still make a declared-independent pair unsafe. This is posthoc applicability evidence only: no new X11/XTEST/task input, no new timing sample, and no model/token/human-tempo/cross-platform claim.

## Next discriminator
The next useful rung is automatic or semi-automatic footprint acquisition: determine whether a bounded runtime can conservatively derive file/surface/process/global-resource dependencies for a small real application workflow without requiring app-specific privileged APIs. Until then, resource-footprint scheduling is a safe contract only when the dependency declaration itself is trustworthy.
