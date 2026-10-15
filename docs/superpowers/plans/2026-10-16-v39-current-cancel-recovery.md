# Current V39 cancel/recovery qualification

**Goal:** Test current cancellation/fresh-observation/final-admission composition without rerunning the historical PR8792 producer.

**Base:** `35a137b4943eac1b44aac58b2d540ed2e7ff9173`.

**Architecture:** Ordinary regression module uses current real monitor/build/cancel/final-admission functions and exact nested wait AST, with queued synthetic observations, a recording in-memory process and planner callbacks. Retain health/ammo recovery and completed/expired/cancelled closure races; invalid/unknown release or failed cancel write must abort without admitting input. Preserve latest full observation for new planning while retaining old invalidation. No production edit unless a demonstrated defect needs repair.

**Constraints:** Local inert tests only, no native input/game/model/provider/WSL/container/allocation or old scientific producer. AST-extracted wait is named scope, not full main-loop/process integration; fixture release is not physical proof.

- [x] Add current-source composed tests and preserve raw rows; include positive no-invalidation control.
- [x] Run affected local selection normal/-O; directed dropped-invalidation control must fail; independently read retained authority/order/freshness evidence.
- [ ] Publish source/conditions/raw and limitations, review and integrate through current permissions.
