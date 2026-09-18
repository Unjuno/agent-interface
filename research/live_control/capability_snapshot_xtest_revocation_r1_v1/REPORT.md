# Capability snapshot XTEST revocation R1 — retained formal stop

Issue #1927. Parents #1910/#1919. Umbrella #40.

## Scientific disposition

**NONE — STOP_FORMAL_OUTER_TIMEOUT_NO_RESULT**

The excluded two-pair construction passed, but the first/only frozen 16-pair formal invocation exceeded the45s outer command envelope before producing a result file.

- formal invocations: **1**
- reruns/replacements/tuning: **0/0/0**
- FORMAL_RESULT.json: absent /0 bytes
- formal stdout/stderr:0/0 bytes
- formal Python/Xvfb/Tk processes remaining after kill:0
- formal display sockets1340..1355 remaining:0

No scientific PASS/FAIL/HOLD is inferred from partial execution.

## Construction evidence

After an excluded fixture-lifecycle repair,2 fresh epoch pairs /10 rows reached PASS_CONSTRUCTION_ELIGIBLE:

- E default Xvfb XTEST present;
- E process death + display socket disappearance;
- D same-display restart with `-extension XTEST`, XTEST absent;
- E fresh snapshot -> DIRECT XTEST_INPUT;
- E wrong-surface reuse -> no selection;
- old E snapshot against D generation -> no selection;
- D fresh snapshot -> FALLBACK CORE_INPUT_FALLBACK;
- D wrong-surface reuse -> no selection;
- candidate/oracle mismatch0;
- authority/task-input/XTEST-action calls0;
- focus/capability changes0.

Construction is excluded and is not promoted into a formal result.

## Retained preformal incidents

1. First construction process had a Tk/Xlib XIO fatal error because the parent Python process owned the Tk display connection across Xvfb restart. formal0. Fixture lifecycle packaging only was repaired by placing Tk A/B in a child process and terminating/waiting it before Xvfb shutdown.
2. The manually relayed Base64 source bundle did not reproduce its local Git blob. formal0. That bundle is non-authoritative. Formal source authority was rebound to seven individual Git files and read back7/7 exact.

## Formal source authority

- PLAN `7110cdc83d893cbe2970ad9cb5216194b0055d00`
- snapshot `07f091a8aa34c7f52364717fc3f03be04ca726ea`
- oracle `3da3f564f739dc7c61a2a28c8fdb811dd1374324`
- runner `af1e70b839bbc004452d8b2185da0c86431da88d`
- Tk fixture `7522eb434c440e6fd5b8e218c6644d01c3223ba6`
- audit `7599551c55c500d53d80d77ee98c7a5d759a36fa`
- independent audit `6bed284eda34032fb6e5edb968819de45272cf54`

## Successor boundary

Do not rerun #1927. A successor may change **only execution/result durability packaging**—for example immutable bounded batches—while preserving the frozen scientific runner/snapshot/oracle semantics, five scenarios, generation rules and decision gates. Use fresh formal pair IDs and do not pool any unmaterialized #1927 partial work.
