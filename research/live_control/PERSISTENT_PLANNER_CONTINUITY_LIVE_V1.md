# Frozen persistent planner continuity probe

One preregistered Luna-low allocation sent two structured turns through one
capability-minimized app-server process and one ephemeral thread.  The first
turn included a one-pixel local image, stored `cobalt-seven`, and returned
`{"value":"stored"}`.  The second turn did not repeat the nonce and returned
`{"value":"cobalt-seven"}`.  Both answers had distinct typed turn IDs, exactly
one completed agent message, and passed the controller-side schema check.

The turns took 2,655.464 and 2,643.947 ms end to end.  The second turn's last
usage was 7,782 input tokens, including 6,912 cached input tokens, plus 37
output and 18 reasoning tokens.  Cumulative usage after two turns was 15,531
input, 6,912 cached input, 52 output, and 18 reasoning tokens.  The protocol
journal contains two starts, two matching usage notifications, two matching
completions, no interrupts, and no MCP startup notifications.

Thread creation took 441.617 ms in this run, outside the three minimal startup
samples in the command-free comparison.  That does not negate capability
suppression, which still emitted zero startup notifications, but it shows that
three startup samples do not describe the latency distribution.  Persistent
operation amortizes this one-time setup rather than assuming a fixed 94 ms
cost.

This proves the live transport and ownership path needed for integration:
local-image input, schema-constrained output, persistent conversational context,
per-turn IDs, and usage accounting all work together.  It is a two-turn nonce
task, so it does not establish GUI judgment quality, general latency, or a token
advantage.  Cancellation was tested separately only at immediate turn start.
The next experiment should invalidate a turn after generation has actually
begun, verify that its output is never eligible, and measure partial usage
without claiming saved tokens from an unmatched run.
