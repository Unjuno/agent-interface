# Current-main standard-caller recovery and XRes budget candidate

## Result

Candidate source revision: `f27b07c8a2af568f4fc5318ce12fd6380180cf21`. The XRes supervised query wait changed from 150 ms to 500 ms. The public caller response deadline, transaction deadline, fail-closed UNKNOWN semantics, and replay denial did not change.

The frozen standard MCP blocked-release test ran once normally and once under `python -O`; both unittest invocations exited 0. In both runs Xvfb provenance was captured, the owner was observed disconnected by XRes, and a separate parent client verified release. The 300 ms caller response returned `pending` after about 258 ms while the event-loop heartbeat maximum gap stayed below 4 ms. The eventual terminal preserved `runtime_failed`, `cleanup_status=UNKNOWN`, `release_confirmed=false`, and `replay_allowed=false` for the old operation.

The old task oracle failed in both modes: the effect count changed from 1 before cancellation to 4 normal and 19 optimized by the 8.5 s horizon. The event trace shows repeated A KeyPress/KeyRelease events while the old A obligation remained held through the deliberately withheld cancel acknowledgement; the scheduled delayed B KeyPress was not observed (`late_keypress_b_observed=false`). Thus the task failure is grounded in repeated held-A effects before verified release, not attributed to an unobserved B event. Both final keymaps were neutral. A distinct fresh session on another window completed its non-idempotent task exactly once; its independent task oracle passed while the old generation remained fenced UNKNOWN, and no old delayed input contaminated the fresh task.

The preceding diagnostic evidence is retained alongside this candidate: R02 had one optimized 150 ms timeout; R03 reproduced it 3/3 times; R04's one-second diagnostic returned XRes disconnection in 199.5 ms, while the one-second withheld cancel acknowledgement kept A held long enough for repeated effects (1→20); the scheduled delayed B request was not observed. This supports why 500 ms advances observation/release while preserving the task failure and UNKNOWN fence.

## Local verification

- Exact standard-caller Xvfb integration: 1/1 unittest normal and 1/1 under `-O`.
- XRes client-fence unit suite: 20/20 normal and 20/20 under `-O`.
- All attempts used image `agent-interface-xvfb-mcp:late-input-r19` (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`) with network disabled, read-only source/root, private tmpfs, and a private Xvfb display.

## Decision and limits

This is a bounded XRes observation/release improvement candidate, not an end-to-end task-success fix. It does not prevent repeated application effects while the old key remains held during cancellation acknowledgement; the scheduled server-delayed B request was not observed in these attempts. The old task correctly remains failed/unknown and unreplayable; the fresh task's pass is a separate generation-bound result. No live MAP01, real provider, matched efficiency, reliability rate, or research-preview acceptance is established. The candidate should not be promoted as “recovery complete” until delayed effects are excluded or their task failure and safe resumption are integrated into the public result contract.
