# Python-Xlib query-keymap prefetch diagnostic A04

A04 is a new, one-shot isolated Xvfb diagnostic following retained A01–A03 evidence. Its narrow question is whether a synchronous `query_keymap()` can leave the matching client event already in Python-Xlib's internal queue while the X socket is not readable. It does not test V39, a game, a model, task effect, threat response, or MAP01.

A01 and A02 stopped during guest setup and invoked no candidate. A03 setup passed, but its one candidate exited 1 with `AttributeError('detail')` before recording edges; its auditor was skipped. A03 did not prove that events were absent or undelivered. A04 changes measurement only: it serializes arbitrary events with optional `detail` and window fields, preserves intervening noise, and searches a bounded interval for the exact expected client event. The three predecessors and their raw evidence are copied intact under `predecessor/`.

The candidate is eligible once after the frozen bundle preflight and exact environment check. The raw-only auditor runs only after candidate exit 0. No retry is allowed. Guest and outputs must remain isolated and uniquely identified. See `PLAN.md`, `COMMANDS.txt`, and `FREEZE.json` for the predeclared protocol and execution record.
