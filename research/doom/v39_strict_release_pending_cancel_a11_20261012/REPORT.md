# V39 strict release + pending-turn cancel composition A11

**Result: `PASS_CONSTRUCTION_ONLY`.** The PR #8835 strict release predicate composes with the exact PR #8843 authored paired-HUD invalidation/pending-turn cancel path. A complete terminal receipt lets the cancel helper return. Four incomplete/adverse release variants are accepted by current main's legacy cancel predicate but rejected by the PR #8835 candidate. The composed health 70→64 crossing invalidates cover, writes and flushes executor cancel before planner interrupt request/ack, and leaves a subsequently completed old turn `answer_eligible=false` with no answer.

## H/T/D/C/U

- **H:** Strict known-empty release receipts preserve the pending-turn cancel ordering while refusing incomplete knowledge of held/unknown keys or key-state errors.
- **T:** Exact main, PR #8835, and PR #8843 source blobs were frozen; one delayed-planner composed case plus a four-pattern legacy/candidate receipt comparison were run in WSLc, normal and optimized CPython. A separate raw-only audit verifies source identities, outputs and scope.
- **D:** PASS only if the complete receipt returns, all four incomplete/adverse receipt variants are accepted by legacy main and refused by strict candidate, the observed ordering is `executor_cancel_write → executor_flush → planner_interrupt_request → planner_interrupt_ack`, and the late old answer remains ineligible. Both runs passed.
- **C:** Synthetic planner/executor and terminal fixtures cannot represent OS scheduling or owner-thread physical release.
- **U:** No physical per-key release, live timing, useful feedback, recovery benefit, threat response, game outcome or MAP01 completion is established.

The first A10 used only `verified`, empty keys and empty buttons. This successor explicitly supplies the additional empty `keys_unknown` and `key_state_errors` fields required by PR #8835. It does not rerun or alter A10.

Exact source copies, Git blob IDs and SHA-256 values are in `SOURCE_MANIFEST.json`. Raw stdout and exit records for both interpreter modes, image identity and post-run container inventory are retained under `raw/`. The independent saved-artifact audit reports 24/24 checks passing in `AUDIT.json`; it recomputes source SHA-256/Git blob IDs and checks the saved outputs, runtime identity, requested limitations and container inventory.

WSLc emitted a host warning that swap limit capabilities are unsupported. Memory was requested at 512 MiB; swap enforcement is not claimed. No formal/live resource allocation was used, and the evidence does not close [Issue #59](https://github.com/Unjuno/agent-interface/issues/59).
