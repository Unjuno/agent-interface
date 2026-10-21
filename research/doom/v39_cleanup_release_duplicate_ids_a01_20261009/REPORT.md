# A01 result — ambiguous duplicate cleanup event IDs

Decision: FAIL_METHOD (synthetic method-level evidence-reconstruction defect).

The seven-case candidate was invoked once against current-main commit 0455b0079ca29bcfe85153f280e592f5e96528f6 and exact cleanup source blob 50c63fa83969ed518a91e39c08d1ee52064eb636 (SHA-256 bc8d3550e6c2d057c7b615b38e424de3497418547e835490429f526853e1fe28). Raw output is preserved in RAW.json before this independent audit.

Four controls matched: matching token, legacy tokenless terminal, mismatched token, and missing terminal. Three duplicate probes failed the conservative evidence gate:
- Repeated acceptance ID with lease-A then lease-B and only a lease-B terminal yielded terminals_complete=true and releases_verified_empty=true; the first acceptance has no matching terminal.
- Repeated terminal rows with lease-B then lease-A yielded both flags true.
- Reversing those terminal rows kept terminals_complete=true but changed releases_verified_empty to false. The empty-release conclusion is row-order-dependent.

The independent raw-only auditor ran once; its input SHA-256 is bdb0f0bb9ea8b07b31b7b870d252ffc253c4ef279470efd8657dfd952c40f443. Decision FAIL_METHOD; controls_match=true; ambiguous_duplicates_rejected=false; duplicate_terminal_order_dependent=true.

H: Confirmed for these synthetic malformed histories: ID-keyed last-row-wins reconstruction can mask an unmatched acceptance and produce order-dependent empty-release evidence.
T: Exact pinned cleanup implementation executed in-memory; no runtime.
D: Candidate and auditor are frozen at the branch's initial commit; source identity and case design in PLAN.md and FREEZE.json.
C: One candidate invocation; raw committed first; one independent audit. One initial auditor-launch syntax failure did not execute audit.py; corrected launch produced the sole auditor invocation. No candidate rerun.
U: No evidence that duplicate IDs occur in production. No live/process/input/physical release, game, GUI, model, or survival conclusion. Does not satisfy #59 live-threat gate. Existing #7706 A01/A02 remain unchanged.
Next: Treat duplicate event identity as ambiguous/incomplete in the receipt reconstruction, add regression tests for all three histories, and obtain independent review. Keep live validation in the separately owned lane.
