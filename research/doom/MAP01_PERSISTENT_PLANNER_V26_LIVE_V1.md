# Frozen MAP01 persistent planner v26 integration

The first preregistered v26 allocation ran four Luna-low decisions in a normal,
continuously advancing Freedoom 2 MAP01 process.  It retained one app-server
process and one planner thread while assigning four distinct turn IDs.  All
four turns completed with one schema-admitted answer, and the protocol emitted
four matching usage notifications and zero MCP startup notifications.

The four model intervals were 5.641, 3.282, 6.982, and 4.751 seconds, totaling
20.655 seconds.  Cumulative usage was 39,154 input tokens, including 26,112
cached input tokens, plus 707 output and 373 reasoning tokens.  The growing
per-turn context and cache are measured facts here; this single run does not
establish whether or when context compression improves the controller.

Four cover programs and five plan programs were admitted.  Every one reached a
terminal event with verified empty key/button release.  One `use` command had
no visible effect and its preplanned forward fallback was admitted 78.597 ms
after the effect observation, with no extra model call.  The run stayed alive
and unfinished with zero kills and no exit.

The health ROI never invalidated, so the allocation is retained as
`RETAINED_LIVE_INTEGRATION_UNEXPOSED_TO_INVALIDATION`.  It verifies the normal
persistent controller path, typed ownership, structured admission, protocol
accounting, local feedback, and release.  It does not verify the newly joined
interrupt path inside a running controller and makes no gameplay, speed, token
efficiency, reliability, or MAP01-clear claim.

The next construction test should inject one deterministic observation
invalidation while the real game and planner are both running.  That test must
keep the visual guard's authority one-way and verify the exact same obligations
as a natural trigger: one matching interrupt, planner terminal completion,
cover terminal release, zero plan input, and zero inherited `next_cover`.
Natural health changes can remain the benchmark condition after the wiring is
proven deterministically.
