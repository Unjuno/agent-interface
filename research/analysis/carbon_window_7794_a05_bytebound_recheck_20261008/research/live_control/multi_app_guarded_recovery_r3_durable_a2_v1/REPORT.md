# Durable A2 repeated mixed-app guarded recovery — formal result

Issue #1798, successor to #1769's `STOP_FORMAL_WRAPPER_NO_DURABLE_ROWS`.

## Decision

**PASS_MULTI_APP_GUARDED_RECOVERY_R3_DURABLE_A2_SCOPED**

The scientific `common.py` is byte-identical to #1769 (SHA-256 `64fe895362ceb1bd5b66fafb64460b6ffa5ce14cc06d371d76a46b6380582cdb`). The only changed factor is formal result durability: four immutable session batches are fsync'd and atomically published before aggregation.

## Formal discipline and result

Logical formal allocation1; batch invocations exactly 1/1/1/1; reruns0; replacements0; tuning0.

All 4/4 fresh private-X11 sessions passed three consecutive cycles:
- stale-refusal task-input unchanged **48/48**;
- fallback intended-active target **48/48**;
- exact task effects **48/48**;
- adjacent replacement validity **12/12**;
- terminal key/pointer neutral **4/4**.

Batch SHA-256:
- 1: `4baf43a67512f933f4039c3b00f7d1100ba324b1bd3d6fc3a4819cd145831211`
- 2: `92df5a69e0617eba603dad8dbb928f5f7d6c979febfcacdb86ce9abeb55344b9`
- 3: `4435cec038021e9e7fddd0340a216b8930de12f614a0e35cb90dac9b58c1dd00`
- 4: `54fb26f446dfeb17239116e410ebf72f10d2ed23e020281155bf5a47f5edb83f`

Independent audit PASS/errors[] with 8/8 corruption controls.

## Retention

`FORMAL_EVIDENCE.tar.gz.b64` losslessly retains BATCH_1..4, RESULT and AUDIT.

- result SHA-256: `652f48b004cc395b1cc388d1abb8bbb13a233cdb3f5b415d8fd09006c180169d`
- audit SHA-256: `138f7ce2b9539686c79d8c73fc9a07d159d6810691d93a988a5f79da42a7760d`
- gzip SHA-256: `22831c77130b786cb7ae55c6a298aaaa9c1c4bfcd645dffdaebacffcc8e09eff`
- canonical b64 SHA-256: `ec83ec3887dc2cb8010042f520b7b31dfaeea01d69215bd647634f8e67fe3f0b`

## Interpretation

This repairs #1769's execution/retention defect and evaluates the originally frozen R3 science without reconstructing or rerunning any #1769 row. The finite three-cycle result supports repeated fail-closed/recovery correctness in this private X11 Chromium+XTerm fixture.

Construction of #1769/#1798 descriptively observed raw X11 window-ID reuse across non-consecutive Chromium generations. That was not a preregistered R3 decision gate; this PASS does not establish raw-XID identity safety. Historical generation/incarnation evidence should be consulted before any new ABA experiment.

## Scope

Three deterministic cycles per session are still not an endurance test, arbitrary application workflow, model-in-loop result, latency/token claim, or cross-backend guarantee.
