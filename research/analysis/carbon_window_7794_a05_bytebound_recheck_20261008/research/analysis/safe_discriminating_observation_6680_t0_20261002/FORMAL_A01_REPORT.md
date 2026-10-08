# Issue #6680 OrbStack A01 — bounded discriminating observation

**Disposition: `PASS_METHOD_SCOPED`.** The fresh OrbStack allocation completed one candidate invocation and one separate raw-only audit invocation, both exit 0 with OOM false. The auditor reconstructed 20/20 unique case-policy rows and reported zero errors. The prior `HOLD_RESOURCE_BEFORE_FORMAL_START` allocation remains unchanged; A01 is a new successor allocation.

## Formal result

For the two frozen identifiable synthetic worlds (c01/c02), `bounded_diagnose` selected the oracle-matching recovery in both cases: 0 wrong recoveries, 0 post-recovery residual recurrences, and 2 useful effects. Each fixed baseline (`always_reobserve`, `always_reset`) had 1 wrong recovery and 1 recurrence over those same two rows. `immediate_yield` had 0 wrong recoveries and 0 useful effects. The worst-case release latency was 0 ticks, equal to the immediate-YIELD comparator.

The diagnostic policy YIELDED without consuming a probe on the mixed/non-identifiable case c03, the ineligible-probe case c04, and the unsupported-observation case c05. These control worlds remained separate from the identifiable comparison; fixed baseline policies kept their frozen behavior.

The formal candidate raw hash is `bd14e74b03246d306e89f1f042842914ba468798449877c0e80a2f6a4f803020`; it happens to equal the deterministic v4 construction raw hash. The formal auditor hash is `30ad9893a9ef5a6581fdcc7f17a8ef23ac91bfd1f2d095ea55cbbc2f37d56267`, also equal to the v4 construction audit hash. These are newly executed container invocations with separate container IDs and timestamps, but byte-identical results are not an additional independent scientific replication.

## Execution and integrity

- Preregistration was posted and read back on Issue #6680 before either formal invocation: [comment](https://github.com/Unjuno/agent-interface/issues/6680#issuecomment-5959408389).
- Candidate container `45f62a9cee06d00ddb48d32ac9e3365a7402a81446ed48d43d8653793f73f84d`: started `2026-10-02T19:03:24.475886054Z`, exit 0, OOM false.
- Auditor container `caf5115ebf3149a6509961169d9423c33ffbf56d4024fcc18463d4481ff1505b`: started `2026-10-02T19:03:38.747677255Z`, exit 0, OOM false.
- Dedicated OrbStack VM `research-6680-a01-20261003`: Ubuntu 24.04, linux/arm64, 1 vCPU and 1536 MiB configured VM cap. Separate in-VM Docker Engine 29.1.3, cgroup v2; no pre-existing containers. OrbStack version 2.2.3.
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/arm64).
- Each container was configured with network `none`, 0.25 CPU, 256 MiB memory and memory-swap, 32 PIDs, read-only root, read-only source, UID/GID 1000, dropped all capabilities, and `no-new-privileges`. The candidate output was mounted read-only to the auditor; candidate and audit outputs were separate mounts. Both output directories were newly created on the clean VM; the audit output was explicitly verified empty before auditor launch. These are configured limits, not a separate measurement of effective host cgroup enforcement. Full Docker inspect and OrbStack VM records are retained beside the raw outputs.
- Frozen source SHA-256 values: candidate `a2edee3964f28e2e9044e2a06f3acbb911ad0168a48f36f69e7522600d2157f4`; auditor `cb75345d519e9c32ac425a4f9785973a1779d032b01bbbf01b67d57dd6a6b2ef`; fixture `aaa3ff20a97f27489105d4c9125993eaf8f4c50c95cd2081f5487ccbef109ec8`; oracle `b735853126d38f37a4a62498e46ed89878fcc36727920aed87d74d4b3d043a23`.
- Preformal construction suite: 28/28 passed on the refreshed branch; it is separate from the formal candidate/auditor invocations. No formal retries or replacements.

## Limits

This is an exhaustive authored finite fixture, not a sample or estimate. The apparent policy advantage depends on the fixture's signatures and hidden effect oracle. It does not establish real fault identifiability, causal benefit in a GUI, model behavior, user benefit, natural rates, runtime safety, or product readiness. The old allocation's resource hold remains a historical fact and is not rewritten as a result.

Raw, audit, exact commands, logs, container inspection, VM metadata, and checksums are in [`formal_a01_orbstack_20261003/`](formal_a01_orbstack_20261003/). The exact H/T/D/C/U and one-shot stopping rule are in [`FORMAL_A01_PREREGISTRATION.md`](FORMAL_A01_PREREGISTRATION.md).
