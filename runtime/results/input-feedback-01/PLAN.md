# Explicit input and existing title feedback integration

Seed 1001068. One allocation each: matched, rejected, pending. Public MCP guarded
input with caller-selected feedback. Primary sees original initial/final images;
points are chosen after review. A Tk canvas Save app delays its app cue 600 ms
(matched/rejected); pending delay 5000 ms exceeds the explicit 1000 ms feedback
budget. Independent event scoring is read only after the owner and children exit.
No retries, sensors, extra model, automatic action, authority renewal, or task
success inferred from the cue. No latency/token/cost gain claim: this functional
integration study does not supply an equivalent route comparison or whole model
usage/billing measurements. All input receipts, cue samples, images and failed
results are retained. Fixed title is a convention and may predate input.

Preparation failure: the preimplementation regression test failed for all four
cue verdicts because the existing public schema rejected feedback before opening
the bridge (IndexError in opened[0]); this was before any live allocation.

Preparation check failure: attempted nonexistent runtime.cli_v1.test_receipt_references; 38 other tests passed and one loader error. Corrected scoped commands use the actual two modules. No live case was allocated.
