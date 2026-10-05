# Freeze — Issue #59 V39 renewal invalidation A01

- **H:** During a renewable-cover wait, a policy-invalidation observation may be dequeued before the matching submit acknowledgement. If the renewal is rejected, it was never admitted: interrupt/discard the dependent planner answer, send no cancellation for that ID, and retain the previously terminaled, verified-empty cover. If accepted, cancel the new ID and require verified empty release plus its cancelled terminal.
- **T:** Source-extracted FIFO controls: (1) invalidation → stale-sequence rejection; (2) invalidation → accepted → cancelled terminal with verified empty release. Assert planner interruption, IDs, cancel writes, and retained/replaced terminal.
- **D:** Baseline source is PR #7904 commit `1403c822609395f9ab21e0cdbb36b7b4c8ee044d`; predecessor renewal-only accepted path lacked admission resolution. Candidate is the follow-up branch’s V39 controller and regression tests. Exact local Windows SHA-256 at freeze: controller `F98D668B2997A692FB397C1E82F63A4793DED0E7FCA7E5601DAD12E6D8941F4C`; controller test `F6675328CE3B07AFCAC1E5A09047D147B9A605F21AC7CC6B94AB092A30793B2B`.
- **C:** Python 3.11 host source-extraction of the actual renewal invalidation branch against both FIFO controls. Baseline run was RED at an unmatched terminal wait on rejection; reconstructed candidate was GREEN 2/2. Syntax compilation passed for the controller and regression module. No import of the full controller runtime was possible in this resource window.
- **U:** Synthetic source/control-flow evidence only. No container, game, model, GUI, OS input, frequency, timing, live effect, or full current-main composition claim. This branch is stacked on #7904, not a refreshed main integration.

## STOP record

At 2026-10-05 05:09 UTC, C: reported 0 bytes free. Read-only `wslc list` did not return within 30 seconds and was interrupted; no WSLc container was launched. The candidate remains draft pending workspace capacity recovery and full focused-suite/current-main validation.
