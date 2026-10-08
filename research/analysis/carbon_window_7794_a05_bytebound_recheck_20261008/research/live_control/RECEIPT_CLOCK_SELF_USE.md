# Use an existing terminal timestamp to omit one clock round trip

Actual assistant Calc self-use repeats frozen socket_v10 / interactive_v26,
seed 991022 and identical enter/save and confirmation step arrays. Instead of
requesting another clock before confirmation, the assistant sets the new absolute
deadline to the preceding terminal_ns plus 30 seconds. This historical timestamp
is not a fresh clock or renewed authority. It gives less remaining time at
admission; the unchanged executor still checks expiry, observation and focus.

The new confirmation is admitted before that deadline, saves [532,590] and returns
VERIFIED and independent success with the correct request identity. No runtime
code change is made for this usage experiment. Audit verifies the deadline equation,
accepted timestamp, twelve exact AIT/PNG frames, workbook hash, request lineage,
complete 23-record read prefix and replay suppression.

| Metric | Prior explicit second clock | Terminal timestamp reuse |
|---|---:|---:|
| Clock requests | 2 | 1 |
| Caller operations through final result | 5 | 4 |
| Modal terminal to confirmation admission | 24.658 s | 20.654 s |
| Initial capture to first admission | 31.524 s | 39.914 s |
| Initial capture to effect read | 57.082 s | 61.548 s |

The whole task did not become faster. One fewer clock boundary is demonstrated,
but uncontrolled assistant/tool time dominates. These are one familiar sequential
run per variant, not causal estimates. The second run includes a failed attempt
to open 007.png by assuming the previous run's image name. The actual terminal
receipt points to 006.png, which the assistant then viewed before confirmation.
The viewing failure is retained in viewing-note.json and remains in all timing.
No runtime action failed; no image-path guessing should be part of future clients.

If the historical timestamp is too old, obtain a new clock rather than adding
time to an expired request or bypassing normal admission. This experiment is not
a blanket recommendation to use 30-second leases or stale observations in dynamic
tasks. It preserves the existing bounded authority model for a known short save
operation only. Human-like tempo and actual model-token savings remain unproven.

Evidence: results/receipt-clock-self-use-01, receipt-clock-self-use-audit.json and
receipt-clock-comparison.json. compare_receipt_clock.py verifies identical step
arrays and separates initial/planner boundary intervals. Next reduce observation
handling mistakes and measure tool-return-to-next-submit timing explicitly before
attributing wall-clock changes to interface improvements. No default promotion
or freeze credit.
