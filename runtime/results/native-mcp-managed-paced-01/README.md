# Managed MCP explicit pacing: primary Calc repeat

The primary assistant repeated Calc seed 991122 (A1=300/A2=758) through managed
MCP startup with --text-gap-ms 2. The initial request bytes exactly match the
earlier zero-gap run, which visibly entered 30 and required correction. This
run showed 300/758 before format confirmation and saved both values correctly
without repair. The assistant observed the format dialog before choosing Excel
format and finish_after. Two action programs completed with verified release;
cleanup completed and owner 18480 exited 0. Relay exec 68176 also exited 0.

The policy is evidenced at three boundaries: allocation metadata, launch argv
and the harness text-policy.json. The recorded entry program contains the six
characters 300758 separately and four explicit 2ms waits. Existing admission,
operation limits and release checks remain in use. Post-dialog feedback still
reports needs_review; saved-file scoring and cleanup outcomes are separate.

Run `python3 runtime/results/native-mcp-managed-paced-01/audit.py` with openpyxl.
It checks 59 manifest entries, exact MCP images, both immutable requests,
identical initial request versus the retained zero-gap request, actual pacing
operations, saved A1/A2/B1 and terminal owner. PLAN.md precedes allocation.
The manifest includes audit.py but predates this README. relay.py is a temporary
driver from the unmerged relay branch with its server path redirected; it does
not add that relay to the production change. The original zero-gap trial remains
on commit 242f6950b in runtime/results/native-mcp-relay-calc-01.

This is a single ordered repeat, not a randomized reliability or latency study.
Host load, setup and assistant timing are uncontrolled. It supports working
configuration integration on this task, not proof of the loss mechanism or a
universally safe 2ms delay. Default remains zero; model token/cost and general
speed gains are unmeasured. No sensors were developed or used for this change.
