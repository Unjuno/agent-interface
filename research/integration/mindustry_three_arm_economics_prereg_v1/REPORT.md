# Mindustry three-arm economics preregistration v1

Issue #1679. Decision: **PASS_MINDUSTRY_THREE_ARM_PREREG_SOURCE_CLOSED**.

This closes only the source/design boundary for #57 cell13. It performs zero live Mindustry, model, provider, X11 task-input, or user-data actions.

The plan preserves the retained Chromium `integrated_efficiency_protocol_v1` economics rather than inventing a second-domain-specific success rule:

- arms: `plain, ephemeral, persistent`;
- task layouts: `A,A,A,B,B,B`;
- task model calls: plain `1×6`, ephemeral `1×6`, persistent `1,0,0,1,0,0`;
- persistent routes: `cold,reuse,reuse,repair,reuse,reuse`;
- one fresh no-image schema preflight per arm, included in token/generation accounting;
- RETAIN logic remains: all arms correct, persistent old-target admissions0, repair succeeds, persistent final input tokens and planner generations beat both controls, token break-even by task<=4; wall-time faster-than-both remains descriptive.

Mindustry substitutions are limited to retained domain evidence: independent one-tile scoring before reset, canonical reset witness/epoch, exactly one A→B geometry mutation after A3 reset and before B1, and the #851 selective world-binding repair semantics. Controller-visible records remain free of engine/oracle/reset-private fields.

## Live start boundary

The preregistration **does not authorize** the three-arm live allocation. A fresh successor to consumed #908 must first retain `PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED` with exact:

- Mindustry v160.2 JAR: 87,022,576 bytes, SHA-256 `7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539`;
- canonical save SHA-256 `8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed`.

#908 remains a consumed materialization HOLD and cannot satisfy this gate retroactively.

## Audit

One container design-audit invocation, reruns0. Errors `[]`. Five corruption controls all reject: changed persistent call schedule, reset-before-score, oracle leak, relaxed token criterion, and removed live-smoke gate.

Preregistration SHA-256: `2d9cd5b9cfa920ebdd11beabfef6fcaaa8d6bd95a7cfc8c8ce68b23bf791d426`.

Scope remains one future six-task second-domain allocation after the live setup gate; no population/general speed or token claim is established here.
