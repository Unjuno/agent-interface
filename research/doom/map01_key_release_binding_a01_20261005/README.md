# Per-admission key-up and release binding A03

This construction-only test advances the #59 r135 measurement prerequisite: explicit per-admission identity/context and one independently joinable per-key up/release outcome. It retains two earlier failed construction attempts rather than hiding their defects.

- **H:** an auditor can bind each admitted key press to exactly one subsequent, context-matched key-up and verified-empty release, while rejecting six identity/order/completeness faults.
- **T:** one baseline plus six single-fault mutations, using a frozen Python fixture, candidate reducer and separately written independent oracle in pinned offline WSLc.
- **D:** `PASS_METHOD_SCOPED` only when baseline passes, all faults fail with the expected class, oracle agrees, and scripts compile. A01 is a runner HOLD. A02 failed the expected-reason comparison on four labels. A03 froze corrected reason labels and passed all seven cases; candidate, auditor, and compile exit codes were 0.
- **C:** synthetic IDs and event order are easier and more complete than a real asynchronous producer; aggregate empty state cannot recover a missing/misbound per-key event.
- **U:** no runtime emitters, physical input state, task effect, useful feedback, model, recovery benefit or live threat response were tested.

See `PREREGISTRATION.md`, `FREEZE.json`, `CONSTRUCTION_ATTEMPT_01.json`, `CONSTRUCTION_ATTEMPT_02.json`, `RUN_A03.json`, `candidate.py`, `audit.py`, the per-attempt outputs, `COMMANDS.txt`, `RESULT.md` and `SHA256SUMS.txt`. This does not authorize or substitute for a new live allocation. No historical result or runtime source was modified.
