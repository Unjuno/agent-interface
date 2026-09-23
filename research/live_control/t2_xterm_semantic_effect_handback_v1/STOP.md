# #1537 preformal construction stop

Task: `T2-XTERM-SEMANTIC-EFFECT-HANDBACK-20260918-005`

Disposition: `PREFORMAL_CONSTRUCTION_STOP_XTERM_INPUT_DELIVERY`

Scientific disposition: **NONE**. Formal allocations: **0**.

The planned science was a transfer of #1518 current-effect handback from a private Tk pixel transition to a task-semantic receipt produced by a raw-PTY helper running inside stock XTerm. Construction never established the required XTEST→XTerm→PTY input path, so no semantic-effect latency or handback claim is permitted.

## Excluded construction sequence

1. First attempt stopped because inherited `XAUTHORITY=/opt/xvfb/.Xauthority` did not exist. A case-local empty Xauthority was introduced; this was harness-only.
2. Subsequent attempts exposed `BadMatch(SetInputFocus)` while targeting XTerm too early/top-level.
3. A bounded repair waited for a mapped viewable XTerm child and prohibited top-level fallback. The focus exception disappeared.
4. Final construction still delivered no `x` byte to the raw-PTY helper. Positive semantic receipts were 0/4. XTerm remained alive until cleanup and exited by SIGTERM (rc15), indicating the helper stayed blocked on PTY input.

The independent #1518-style helper-level absolute-deadline control passed. Global XTEST press/release completed and terminal X key was UP 5/5. These mechanics do not substitute for task delivery.

## Final excluded construction

- rows: 5
- positive receipts: 0/4
- positive task-correct: 0/4
- candidate positive unresolved timeouts: 2/2
- late accepted receipts: 0
- possible/local post-handback physical tail: 0
- NO_EFFECT unresolved timeout: 1/1, but task-correct false because helper never received the key
- formal: 0

SHA-256:
- final construction result: `1ab639435bec032ac4e2fef7d07714866f1903bb9eb1f4e1d06d71fb7ffa8d63`
- experiment source at stop: `be8e742b50d5cc5aad2098ec902adb868cd4986433fbbdda3f2409408b8e989c`
- task helper source at stop: `2594615d971709ae9ef628a64fd3baa1c76c0a06e5bdf57e5c9926f59fd2508f`
- deadline control source at stop: `8e73ff17e2e088724cce7ed41ef3dce7dbc0408c0b237d6a4b46a61ad3182e1a`

These hashes record the construction bytes after the fact; they are **not** a claim that #1537 had reached source-frozen formal eligibility.

## Successor

A fresh successor should isolate one question only: prove that one ordinary XTEST `x` event reaches a raw-PTY helper in stock XTerm under private Xvfb, with independently verified key release and no semantic receipt machinery. Only after that input-delivery construction passes should the semantic-effect handback protocol be retried under a new task/version.
