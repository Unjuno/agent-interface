# A01 review reconstruction — frozen-trace output recovery

Status: RECONSTRUCTION PREREGISTRATION. This is not the historical stdout of either A02 run.
Purpose: add inspectable full 42-slot window and 84-slot availability evidence in response to PR #7518 review, without editing the historical A02 result/audit files.

## H/T/D/C/U

- **H:** Replaying the retained window candidate and independently rebuilding its availability-time grid from its immutable inputs will make all claimed slots and classifications inspectable.
- **T:** Execute the retained window candidate once as a reconstruction, and run the new candidate and separately formulated all-pairs auditor once each against the pinned report/events. Do no game, model, GUI, input, or live monitor work.
- **D:** Source commit 2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0; report blob bff2459036dcdcc44ed100b0c0bc657e1bb8e69a; event blob cbaeed9c7ba27b53cef9d10730ae33313371ad9a. Expected 634 event rows, 218 typed observations, six waits. Expected raw SHA-256 report 719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687; events 2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381.
- **C:** Frozen horizons 500,1000,1500,2000,2500,3000,4000ms. Availability clocks are the event's top-level capture_ns and its outer emit_ns. Verify top-level capture_ns equals nested health.capture_ns for every typed row before analysis. Baseline is the latest valid observed numeric health at/before model-wait start; adjacent decreases trigger on the second decrease when separated by no more than W; invalid/missing observations reset adjacency. Preserve all wait × horizon × clock slots and no-policy/authored-policy classification.
- **U:** Saved-trace reconstruction only. It cannot establish online monitor behavior, useful interruption, safety, task effect, or historical command stdout identity.

## Frozen execution / output handling

The historical window result.json and availability result.json/audit.json remain unchanged. The window rerun will be saved as window-candidate-reconstruction.json and explicitly labeled a reconstruction, not original stdout. The availability candidate and independent auditor source and complete outputs will be retained here. Candidate/auditor source SHA-256 values and raw inputs are recorded after freezing sources and before their execution. Frozen source SHA-256 before execution: candidate 003f997390d7cf6907965ed8084c2b4e7fdf9ce7f74db11e1bcc15cf735dd19c; independent auditor bf0c7944f426c351e4cf16df5d89e89463bc5e7db2d2176a55a151661fa7e58d. Preregistration SHA-256 before this source-hash annotation: a933f1aeee5d1dc58533c56626f724fbf6fc5cdca8be62080aab3df9aa8a8361. Window reconstruction scripts are existing frozen A02 artifacts pinned by their immutable branch tree entries: candidate.mjs SHA-256 250c5699260c369b72e5bf927181c782af3d77a679db15835dc42ead9701ebaf; independent_audit.mjs SHA-256 71d975f4aa31c50b45bf77cd6af4939dbc8fb23fe5f2947c8d41d8dba8e5e4f0. Their output, if reproduced, is still a reconstruction and is not attributed to the historical A02 invocation. Any parse/count/hash/clock-field discrepancy is STOP; no retry or substitution.
