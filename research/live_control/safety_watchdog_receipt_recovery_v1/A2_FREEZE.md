# Safety watchdog receipt recovery v1 — A2 source-first freeze

Task `SAFETY-WATCHDOG-RECEIPT-RECOVERY-20260917-002`, Issue #827.

Immutable publication BASE: `40072ec1962afe9fe1a9f6ade79ce36a2e8cc93f`.

A1 is retained `STOPPED_FORMAL_HARNESS_OUTPUT_FRAMING` and is unpooled. A2 uses disjoint fresh IDs.

A2 formal rows before this freeze: **0/8**. Formal rerun budget: **0**.

Only repair from A1: parse the final nonempty watchdog stdout line as JSON so the preceding python-xlib warning is ignored as non-JSON diagnostic output. No watchdog/owner/receiver physical safety code, timing, scientific arm, thresholds, or auditor gate changed.

A2 exact source identities are in `source_hashes_a2.json`.
