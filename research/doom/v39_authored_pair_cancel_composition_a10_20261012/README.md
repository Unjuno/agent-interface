# A10 — paired HUD invalidation through pending-turn cancel

This companion experiment advances A09's monitor-only boundary through the current-main wait/cancel and planner-adapter logic. It freezes main `f185a9059d485a4f8d5a65e9e7f6782897f67eae` and exact Git blobs for the V39 controller, `ObservableSignalGuard`, and `PersistentPlannerAdapter`.

One WSLc case passed. A real health guard crossed its 65 floor; the controller wait closure emitted policy invalidation; `cancel_invalidated_cover` wrote and flushed the executor cancel before sending planner interrupt. The fake server then reported the prior turn as completed, but the production adapter returned `answer_eligible=false` and `answer=null`. The cancellation helper accepted the queued terminal only with `verified=true` and empty key/button sets. The independent audit checks all source blob IDs, SHA-256 hashes, test and Containerfile hashes, transcript, structured receipt, and expected ordering without rerunning the test.

The executor and planner transport are deterministic fakes. The empty-release receipt is fixture data; no OS input was sent and no physical key release was observed. This does not establish live cancellation timing, GUI/model behavior, useful feedback, bounded recovery, gameplay effect, or terminal success. The full live threat gate and computer-control goal remain open.
