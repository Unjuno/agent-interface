# State-conditioned regret for optional observation omission

- **Status:** A02 finite method result passed; the separate A01 protocol deviation remains preserved.
- **Source:** Issue [#8397](https://github.com/Unjuno/agent-interface/issues/8397).
- **Idea:** Measure the exact consequence of withholding optional observations by task state and omission duration while holding a fixed policy and mandatory safety observations constant.
- **Outcome:** A01 is `STOP_PROTOCOL_DEVIATION`. The separately frozen A02 candidate and raw-only auditor each ran once and reconstructed 8/8 finite traces. Pre-decision and post-completion omissions preserved authored effects while reducing delivered observations (3→2); omitting across a transition produced a wrong-target effect and one recovery step. Captured-but-undelivered and mandatory-safety omission cases remained distinct. This is a synthetic instrument result, not evidence for skipping live screenshots or changing runtime scheduling. Integrated unchanged through merged [PR #8531](https://github.com/Unjuno/agent-interface/pull/8531).
