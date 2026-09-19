# Core-v1 HINT lineage bridge integration result

Task `CORE-V1-HINT-LINEAGE-BRIDGE-20260917-001`, Issue #773.

## Decision

**`PASS_CORE_V1_HINT_LINEAGE_BRIDGE_SCOPED`.**

The promoted `runtime/core_v1` dependency is held byte-exact at Git blob `a16620b65d22757ca9160d68feb1381306cc6ac3`, SHA-256 `268cf282c02f9e2dd38a8c45a36378049443ef2a2431063359011d0552b9c37c`, 13,869 bytes. It was not modified.

One bridge factor was compared over one frozen deterministic 22-row formal matrix:

- `naive`: constructs an ordinary core-v1 pointer program from target evidence while accepting caller-supplied source sequence/revision numbers;
- `typed`: requires a CURRENT `ADMISSION_DEPENDENCY`, or an exact CURRENT revalidation receipt bound to the original HISTORICAL HINT identity and target.

## Key discriminator

The authored historical HINT points to `[120,140]` at observation/binding `10/3`. Current state is `20/5`, and an explicit current revalidation points to `[420,280]`.

`naive + hint_laundered_current_numeric` preserves the historical point `[120,140]`, substitutes only program source `20/5`, and promoted `core_v1.admit_program()` returns **accepted=true**. Core numeric freshness alone therefore does not establish evidence lineage.

The same weak HINT under the typed bridge is refused before program construction as `HINT_REQUIRES_CURRENT_REVALIDATION`.

An exact HINT→CURRENT revalidation creates a distinct current admission dependency at `[420,280]`; the typed bridge constructs the program and core accepts it.

Stale current revalidation is not numerically refreshed by the bridge: observation 19 is constructed as 19 and core returns `STALE_OBSERVATION`; stale binding similarly returns `STALE_BINDING`.

A forged in-place HINT mutation to `ADMISSION_DEPENDENCY/CURRENT` fails receipt digest validation. Existing core lease and capability controls remain unchanged (`LEASE_EXPIRED`, `UNSUPPORTED_CAPABILITY`).

## Integrity

- formal invocation: 1;
- formal reruns/replacements: 0;
- formal rows: 22;
- frozen audit: PASS, errors 0;
- postformal source identity: exact;
- copied-evidence/source corruption controls rejected: 4/4.

## Interpretation

Evidence-role lineage must be enforced before or alongside program construction; the current promoted core-v1 numeric freshness/binding fields cannot, by themselves, distinguish a current target from historical target evidence whose source numbers were rewritten by an adapter.

This does **not** require changing core-v1 in this experiment. The result is an additive integration boundary showing that a lineage-aware pre-admission bridge can preserve the already-promoted core checks while preventing authority laundering.

## Limits

Deterministic no-GUI fake-backend fixture. Receipt roles/digests are authored and unauthenticated. No claim of complete role taxonomy, secure receipt authenticity, GUI semantic identity, model/token/latency benefit, cross-platform execution, or production ABI promotion. A later architecture decision must choose whether lineage belongs in a stable adapter contract or a future program schema; this result does not make that product decision.
