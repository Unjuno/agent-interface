# Issue #16 T4 — frozen-gate failure

**Disposition: `STOP_AUDIT_SCHEMA_AND_PLAN_COUNT`.** The host candidate invocation exited 0 and wrote 12 raw rows. The frozen auditor exited 1 with `KeyError: 'record_id'` on the final compensator-failure control, which the candidate had appended without that field. The preregistered row count was also wrong: the frozen schedule enumerates 11 strict prefixes plus one negative control (12 total), not 10.

A separately authored post-hoc reconstruction checker found zero semantic-classification errors across all 12 raw rows and rejected 3/3 mutations (changed outcome, dropped row, duplicated row). It also confirmed one schema error: the control row has no `record_id`. This supplemental audit does not change the frozen STOP into PASS.

On the synthetic schedule, five of six compensatable non-empty prefixes were classified `ABORTED_COMPENSATED`; the one deliberately failed-compensation control remained `ABORTED_PARTIAL`. Three prefixes containing irreversible `SEND` also remained `ABORTED_PARTIAL`. Historical applied-effect lists were preserved on all rows. No row claimed COMMITTED.

Raw SHA-256: `4373a75c846166309a183887a83937b3f2f9c7e948915eda42f9151495ee0204`.
Supplemental audit SHA-256: `7ae7dac5db9b218deb761c3a0dd3563b71c746089f0050ec63515e3c739266af`.
Frozen base: `7fcf30f37e122bc3fce7ab893aebd9bfa4a864a8`.
Frozen source commit: `2a21ca8d10b4834e98e854730e7b19fef1c0342c`.

This is a host-only deterministic simulator. No Docker/OrbStack call was made because no container allocation was assigned to this lane in #5085; no GUI, model, network, task input, or external effect occurred. The prior 45-session GUI allocation remains consumed and is not repeated. Preserve this STOP and raw as-is.
