# Issue #8654 C06 — stochastic partial-feedback enumeration

Disposition: FAIL_METHOD. Candidate and audit sources were frozen at source commit 8f13efb2597fc9c3fff0f68d73d37edbf9dcbc28.

Candidate enumerated 197376 joint action/reward histories across three regimes. Raw JSONL shards and their hash manifest were committed at 6434fcad13cdd0407c9f2218fdc2ec96896e5c23 before the independent auditor ran.

Audit summary:

null

Audit error: SyntaxError: Cannot convert 282429536481 GLOBAL_SHIFT to a BigInt     at BigInt (<anonymous>)     at eval (eval at main ([eval]:63:17), <anonymous>:66:86)     at auditC06 (eval at main ([eval]:63:17), <anonymous>:69:58)     at main ([eval]:66:17)     at [eval]:93:1     at [eval]:94:4     at runScriptInThisContext (node:internal/vm:219:10)     at node:internal/process/execution:451:12     at [eval]-wrapper:6:24     at runScriptInContext (node:internal/process/execution:449:60)

The design is exact for Bernoulli potential outcomes with four trials per context. Diagnostic action probability is 1/4 for the cue-opposed action and 3/4 for the cue-aligned action; greedy support is intentionally deficient. This is method evidence only, not evidence that exploration improves real-agent behavior or is safe in a GUI.
