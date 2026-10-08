# Issue #8577 A01 — real Tk widget transfer result

## Disposition

**PASS_METHOD_SCOPED** — the frozen checker and independent auditor completed the single planned allocation in the locally cached WSLc image. This is a bounded method-transfer result on a disposable Tk 8.6 fixture, not a product, agent, OS-input, or user study.

The candidate was invoked once and emitted 13 rows. The independent auditor was invoked once against the saved candidate JSON and emitted zero reconstruction errors. Counts: 4 PASS, 5 VIOLATION, 3 UNKNOWN, 1 NOT_APPLICABLE. All four frozen mutation controls were rejected. Raw output and audit digests are in `SHA256SUMS`; source/runtime provenance is frozen in `FREEZE.json`.

## Result by planned contrast

- The valid text setter, valid Checkbutton keyboard setter, equal-value no-op, and completed asynchronous receipt were classified PASS.
- Seeded wrong-target, ignored-input, duplicate-callback, first-write-wins, and combined wrong-target × duplicate-callback were classified VIOLATION.
- Stale epoch, pending completion at the decision boundary, and focus on a decoy were UNKNOWN (abstain).
- The non-idempotent counter command was NOT_APPLICABLE and remained uninvoked.
- For duplicate callback, both weak comparators missed the fault: the requested field ended at the expected value, and deterministic replay reproduced the same final snapshot. The event ledger independently exposed duplicate callback delivery. This supports the narrow claim that the declared law/event evidence caught these authored fixture faults where those two baselines did not.

The pre-freeze mutation regression also exposed and repaired an auditor gap: changing the decoy's widget value and replay value together had previously escaped detection. The final auditor cross-checks public projections against raw widget readback and explicitly verifies the decoy terminal value; all four mutations were rejected in normal and optimized construction suites before the freeze.

## Execution and preserved stop evidence

Source base: `0e50fc59a737f58cb72db5bac4a5d845df00badf`. Frozen source commit: `d9cf7d2f002e5bd5bc9f9f72c8b25f218bf7e4af`.

The pinned image was `ai-x20-tk-5260:20261003-a02`, image ID `sha256:217851fe68e7340cd6301e6d1a1bd79d2c7b6cb4d13eb444a06fabaf0fde3417`, with Python 3.12.14 and Tk 8.6. The standard `xvfb-run` launcher failed in preparation because `xauth` is absent; that failure was not erased. Construction suites then passed in both normal and optimized Python using Xvfb started directly on display :99. The one-shot formal candidate and auditor both exited successfully using that frozen route. Fontconfig emitted a non-fatal cache-permission warning.

Post-execution byte-integrity review found that the frozen ancillary `README.md` digest differs from the Windows worktree bytes after Git's CRLF checkout conversion. Git reports no content difference beyond line endings; all executable source, test, fixture, truth, and protocol hashes match the frozen values. The README was not executed or read by candidate/auditor. This documentation-only hash deviation is retained here rather than silently rewriting the freeze; no candidate or auditor rerun was made.

The WSLc image and private Xvfb session required no Docker Desktop or external daemon. No CPU/memory enforcement is claimed. The GUI events are synthesized at the Tk toolkit event-queue boundary and processed through default widget bindings. This is not physical keyboard/OS injection, a production GUI, a game, or an agent task.

## H / T / D / C / U conclusion

- **H:** Supported within this fixture: scoped idempotent-law checks plus event/readback reconstruction detected the authored setter faults and abstained at the declared stale, pending, and ambiguous-focus boundaries.
- **T:** One frozen 13-case allocation across Tk Entry and Checkbutton widgets, with a fresh disposable fixture per route.
- **D:** All frozen status, abstention, non-idempotence, weak-baseline-blind-spot, reconstruction, and four mutation-rejection conditions met; `PASS_METHOD_SCOPED`.
- **C:** This does not show that the checker adds value over a strong route-specific receipt checker; deterministic authored faults may be easier than real toolkit/application failures; the fixture exposes status text and raw values.
- **U:** One small Tk fixture, one Linux/WSL runtime, authored faults, and synthesized toolkit-level events. No prevalence, arbitrary GUI/lens conformance, OS input reliability, accessibility tree, task completion, safety, portability, or product-readiness inference.

No retries, source changes, or output overwrites occurred after freeze. The earlier closed #8556 result and merged PR #8558 remain unchanged; this is its distinct successor allocation for open Issue #8577.
